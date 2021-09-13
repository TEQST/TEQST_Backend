from django.db import models
from django.core.files import base
from django.core.files.storage import default_storage
from django.contrib import auth
from django.conf import settings
from textmgmt import models as text_models
from . import storages
from .utils import format_timestamp
import wave, re
import librosa
import shlex
import subprocess
import os
from pathlib import Path


def get_normalized_filename(instance):
    title = re.sub(r"[\- \\\/]", "_", instance.text.title)
    title = title.lower()
    return f'{title}-usr{instance.speaker.id:04d}'


def text_rec_upload_path(instance, filename):
    sf_path = instance.text.shared_folder.get_path()
    name = get_normalized_filename(instance)
    return f'{sf_path}/AudioData/{name}.wav'


def stm_upload_path(instance, filename):
    sf_path = instance.text.shared_folder.get_path()
    name = get_normalized_filename(instance)
    return f'{sf_path}/STM/{name}.stm'


class TextRecording(models.Model):
    """
    Acts as a relation between a user and a text and saves all information that are specific to that recording. 
    """
    speaker = models.ForeignKey(auth.get_user_model(), on_delete=models.CASCADE)
    text = models.ForeignKey(text_models.Text, on_delete=models.CASCADE, related_name='textrecording')

    TTS_permission = models.BooleanField(default=True)
    SR_permission = models.BooleanField(default=True)

    # This stores the last time a sentencerecording for this textrecording was created/updated
    last_updated = models.DateTimeField(auto_now=True)
    rec_time_without_rep = models.FloatField(default=0.0)
    rec_time_with_rep = models.FloatField(default=0.0)
    
    audiofile = models.FileField(upload_to=text_rec_upload_path, blank=True)
    stmfile = models.FileField(upload_to=stm_upload_path, blank=True)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.audiofile.save('name', base.ContentFile(b''), save=False)
            self.stmfile.save('name', base.ContentFile(b''), save=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['text', 'speaker']
        constraints = [
            models.UniqueConstraint(fields=['speaker', 'text'], name='unique_trec'),
        ]

    def active_sentence(self):
        sentence_num = SentenceRecording.objects.filter(recording=self).count() + 1
        # if a speaker is finished with a text this number is one higher than the number of sentences in the text
        return sentence_num
    
    def is_finished(self):
        return self.srecs.count() >= self.text.sentence_count()
    
    def get_progress(self):
        """
        returns a tuple of (# sentences completed, # sentences in the text)
        """
        return (self.active_sentence() - 1, self.text.sentence_count())

    def create_stm(self):
        self.text.shared_folder.add_user_to_log(self.speaker)

        #create string with encoded userdata
        user_str = f'<{self.speaker.gender},{self.speaker.education},'
        if self.SR_permission:
            user_str += 'SR'
        if self.TTS_permission:
            user_str += 'TTS'
        user_str += f',{self.speaker.country},{self.speaker.accent}>'
        username = self.speaker.username
        current_timestamp = 0
        sentences = self.text.get_content()
        wav_path_rel = Path(self.audiofile.name).stem

        # accessing files from their FileFields in write mode under the use of the GoogleCloudStorage from django-storages
        # causes errors. Opening files in write mode from the storage works.
        with default_storage.open(self.stmfile.name, 'wb') as stm_file:
            with default_storage.open(self.audiofile.name, 'wb') as audio_full:
                # since the wave library internally uses python's standard open() method to open files
                # it needs to be handed an already opened file when working with Google Cloud storage
                wav_full = wave.open(audio_full, 'wb')
                for srec in self.srecs.all():
                    with srec.audiofile.open('rb') as srec_audio:
                        wav_part = wave.open(srec_audio, 'rb')

                        #On concatenating the first file: also copy all settings
                        if current_timestamp == 0:
                            wav_full.setparams(wav_part.getparams())
                        duration = wav_part.getnframes() / wav_part.getframerate()

                        stm_entry = wav_path_rel + '_' + username + '_' + format_timestamp(current_timestamp) + '_' + format_timestamp(current_timestamp + duration) + ' ' \
                        + wav_path_rel + ' ' + str(wav_part.getnchannels()) + ' ' + username + ' ' + "{0:.2f}".format(current_timestamp) + ' ' + "{0:.2f}".format(current_timestamp + duration) + ' ' \
                        + user_str + ' ' + sentences[srec.index - 1] + '\n'
                    
                        stm_file.write(bytes(stm_entry, encoding='utf-8'))

                        current_timestamp += duration

                        #copy audio
                        wav_full.writeframesraw(wav_part.readframes(wav_part.getnframes()))
                        wav_part.close()
                wav_full.close()
        
        self.text.shared_folder.concat_stms()




def sentence_rec_upload_path(instance, filename):
    """
    Delivers the location in the filesystem where the recordings should be stored.
    """
    sf_path = instance.recording.text.shared_folder.get_path()
    return f'{sf_path}/TempAudio/{instance.recording.id}_{instance.index}.opus'


class SentenceRecording(models.Model):
    """
    Acts as a 'component' of a TextRecording, that saves audio and information for each sentence in the text
    """
    class Validity(models.TextChoices):
        VALID = "VALID"
        INVALID_START = "INVALID_START"
        INVALID_END = "INVALID_END"
        INVALID_START_END = "INVALID_START_END"

    recording = models.ForeignKey(TextRecording, on_delete=models.CASCADE, related_name='srecs')
    index = models.IntegerField(default=0)
    audiofile = models.FileField(upload_to=sentence_rec_upload_path, storage=storages.BackupStorage())
    valid = models.CharField(max_length=50, choices=Validity.choices, default=Validity.VALID)
    length = models.FloatField(default=0.0)

    class Meta:
        ordering = ['recording', 'index']
        constraints = [
            models.UniqueConstraint(fields=['recording', 'index'], name='unique_srec'),
        ]

    def save(self, *args, **kwargs):
        old_length: float
        creating = True
        if not self._state.adding:
            creating = False
            old_length = self.length
        super().save(*args, **kwargs)  # need to save once to have the audiofile on disk
        self.valid, self.length = self.get_audio_info()
        super().save()

        # update recording times
        self.recording.rec_time_without_rep += self.length
        if not creating:
            self.recording.rec_time_without_rep -= old_length
        self.recording.rec_time_with_rep += self.length
        # the following line does two things:
        # 1. It saves the recording time updates
        # 2. It ensures that the last_updated field of the textrecording is updated
        #    (always happens on a call to the save method)
        self.recording.save()

        if self.recording.is_finished():
            self.recording.create_stm()
    
    def get_audio_length(self):
        audio_file = default_storage.open(self.audiofile, 'rb')
        wav = wave.open(audio_file, 'rb')
        duration = wav.getnframes() / wav.getframerate()
        wav.close()
        self.audiofile.close()
        return duration
    
    def get_audio_info(self):
        """
        returns audio info in the form of a tuple (Validity, Length).
        Validity as a value of the Validity Enum
        e.g. (self.Validity.VALID, 5.34)
        """
        # create temporary wav file
        # using ffmpeg command "ffmpeg -i input.opus -vn output.wav"
        cwd_rel, filename_opus = sentence_rec_upload_path(self, None).rsplit('/', 1)
        filename_wav = filename_opus[:-5]+'.wav'
        args = shlex.split(f'ffmpeg -i {filename_opus} -vn {filename_wav}')
        subprocess.run(args, cwd=settings.MEDIA_ROOT/cwd_rel, check=True)  # may raise an error if it didn't work

        filepath_wav = settings.MEDIA_ROOT/cwd_rel/filename_wav
        with default_storage.open(filepath_wav) as af:  # TODO open the temp file, not self.audiofile
            y, sr = librosa.load(af, sr=None)
        length = librosa.get_duration(y=y, sr=sr)
        nonMuteSections = librosa.effects.split(y, 20)
        validity: self.Validity
        info = ()
        if len(nonMuteSections) != 0:  # this test is is probably unnecessary
            start_invalid = nonMuteSections[0][0] / sr < 0.3
            end_invalid = nonMuteSections[-1][1] / sr > length - 0.2
            if start_invalid and end_invalid:
                validity = self.Validity.INVALID_START_END
            else:
                if start_invalid:
                    validity = self.Validity.INVALID_START
                elif end_invalid:
                    validity = self.Validity.INVALID_END
                else:
                    validity = self.Validity.VALID
            info = (validity, length)
        else:
            info = (self.Validity.VALID, length)  # does this make sense if len(nonMuteSection) != 0 ?

        # delete temporary file
        os.remove(filepath_wav)

        return info