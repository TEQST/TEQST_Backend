from django.db import models
from django.conf import settings
from django.core.files import uploadedfile, base
from django.core.files.storage import default_storage
from django.contrib import auth
from textmgmt import models as text_models
from usermgmt import models as user_models
from usermgmt.countries import COUNTRY_CHOICES
from . import storages
from .utils import format_timestamp
import wave, io, re
import librosa
from pathlib import Path
from datetime import date


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

        with self.stmfile.open('wb') as stm_file:
            with wave.open(self.audiofile.open('wb'), 'wb') as wav_full:
                for srec in self.srecs.all():
                    with wave.open(srec.audiofile.open('rb'), 'rb') as wav_part:

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
        
        self.text.shared_folder.concat_stms()




def sentence_rec_upload_path(instance, filename):
    """
    Delivers the location in the filesystem where the recordings should be stored.
    """
    sf_path = instance.recording.text.shared_folder.get_path()
    return f'{sf_path}/TempAudio/{instance.recording.id}_{instance.index}.wav'


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

    class Meta:
        ordering = ['recording', 'index']
        constraints = [
            models.UniqueConstraint(fields=['recording', 'index'], name='unique_srec'),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        with default_storage.open(self.audiofile.name) as af:
            y, sr = librosa.load(af, sr=None)
        length = librosa.get_duration(y=y, sr=sr)
        nonMuteSections = librosa.effects.split(y, 20)
        if len(nonMuteSections) != 0:  # this test is is probably unnecessary
            start_invalid = nonMuteSections[0][0] / sr < 0.3
            end_invalid = nonMuteSections[-1][1] / sr > length - 0.2
            if start_invalid and end_invalid:
                self.valid = self.Validity.INVALID_START_END
            else:
                if start_invalid:
                    self.valid = self.Validity.INVALID_START
                elif end_invalid:
                    self.valid = self.Validity.INVALID_END
                else:
                    self.valid = self.Validity.VALID
            super().save()
        # the followiing line ensures that the last_updated field of the textrecording is updated
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

