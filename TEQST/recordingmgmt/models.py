from django.db import NotSupportedError, models, utils
from django.core.files import base
from django.core.files.storage import default_storage
from django.contrib import auth
from django.utils import timezone
from textmgmt import models as text_models, permissions as text_permissions
from . import storages
from .utils import format_timestamp
import wave, re
import librosa
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

    created_at = models.DateTimeField(auto_now_add=True)

    # These are deprecated and only meant to hold legacy data.
    last_updated_old = models.DateTimeField(auto_now=True)
    rec_time_without_rep_old = models.FloatField(default=0.0)
    rec_time_with_rep_old = models.FloatField(default=0.0)
    
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

    @property # Replaces model field, hence the property
    def last_updated(self):
        if self.srecs.filter(legacy=False).exists(): # If there are new timestamps, use those
            try:
                last_updated = self.srecs.aggregate(last_updated=models.Max('last_updated'))['last_updated']
                return last_updated
            except NotSupportedError: #SQLite doesn't support aggregation on datetime fields
                most_recent = self.last_updated_old
                for srec in self.srecs.filter(legacy=False):
                    if most_recent < srec.last_updated:
                        most_recent = srec.last_updated
                return most_recent
        if self.last_updated_old is None: # If legacy update times are disabled, fallback to created_at
            return self.created_at
        return self.last_updated_old # Fall back to old timestamp
        
    @property # Replaces model field, hence the property
    def rec_time_without_rep(self):
        if not self.srecs.filter(legacy=False).exists():
            return self.rec_time_without_rep_old
        return self.rec_time_without_rep_old + self.srecs.filter(legacy=False).aggregate(total_time=models.Sum('length'))['total_time']

    @property # Replaces model field, hence the property
    def rec_time_with_rep(self):
        reps = SentenceRecordingBackup.objects.filter(recording__recording=self) \
            .aggregate(total_time=models.Sum('length'))['total_time']
        # Old repetitions are not recorded, hence the recovery method
        if reps is None:
            reps = 0.0
        legacy_reps = self.rec_time_with_rep_old - self.rec_time_without_rep_old
        return self.rec_time_without_rep + reps + legacy_reps

    #Used for permission checks
    def is_owner(self, user):
        return self.text.is_owner(user)

    #Used for permission checks
    def is_speaker(self, user):
        return self.speaker == user

    #Used for permission checks
    def is_listener(self, user):
        perm_qs = text_permissions.get_listener_permissions(self.text.shared_folder, user)
        for perm in perm_qs:
            if perm.contains_speaker(self.speaker):
                return True
        return False

    def is_below_root(self, root):
        return self.text.is_below_root(root)

    def active_sentence(self):
        sentence_num = self.srecs.count() + 1
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
                        + user_str + ' ' + sentences[srec.index() - 1] + '\n'
                    
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
    return f'{sf_path}/TempAudio/{instance.recording.id}_{instance.sentence.id}.wav'


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
    sentence = models.ForeignKey(text_models.Sentence, on_delete=models.CASCADE, related_name='srecs')

    audiofile = models.FileField(upload_to=sentence_rec_upload_path)
    length = models.FloatField(default=0.0) # Useful for optimization, is set in save()

    # This is not auto_now_add, since it is meant to track the audiofile, not the model
    last_updated = models.DateTimeField(default=timezone.now) 

    # Whether or not this recording is from an older version of the software, serializers update this to False on Create/Update
    legacy = models.BooleanField(default=True) 

    valid = models.CharField(max_length=50, choices=Validity.choices, default=Validity.VALID)

    class Meta:
        ordering = ['recording', 'sentence']
        constraints = [
            models.UniqueConstraint(fields=['recording', 'sentence'], name='unique_srec'),
        ]

    def save(self, *args, **kwargs):
        #This check can't be a db constraint, since those don't support cross-table lookups.
        #Because of that, it is moved to the next closest spot.
        if self.recording.text != self.sentence.text:
            raise utils.IntegrityError('Text reference is ambiguos')

        super().save(*args, **kwargs)

        with default_storage.open(self.audiofile.name) as af:
            y, sr = librosa.load(af, sr=None)
        length = librosa.get_duration(y=y, sr=sr)
        self.length = length
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

        if self.recording.is_finished():
            self.recording.create_stm()

    #Used for permission checks
    def is_owner(self, user):
        return self.recording.is_owner(user)

    #Used for permission checks
    def is_speaker(self, user):
        return self.recording.is_speaker(user)

    #Used for permission checks
    def is_listener(self, user):
        return self.recording.is_listener(user)
    
    #TODO @property ???
    def index(self):
        return self.sentence.index

    #TODO use length field if available
    def get_audio_length(self):
        with wave.open(self.audiofile, 'rb') as wav:
            duration = wav.getnframes() / wav.getframerate()
        return duration
    



def sentence_rec_backup_upload_path(instance, filename):
    """
    Delivers the location in the filesystem where the recordings should be stored.
    """
    sf_path = instance.recording.recording.text.shared_folder.get_path()
    return f'{sf_path}/TempAudio/Backup/{instance.recording.recording.id}_{instance.recording.sentence.id}__{instance.last_updated.strftime("%Y_%m_%d_%H_%M_%S_%f")}.wav'


class SentenceRecordingBackup(models.Model):

    recording = models.ForeignKey(SentenceRecording, on_delete=models.CASCADE, related_name='backups')

    audiofile = models.FileField(upload_to=sentence_rec_backup_upload_path)
    length = models.FloatField()
    last_updated = models.DateTimeField() 

    valid = models.CharField(max_length=50, choices=SentenceRecording.Validity.choices, default=SentenceRecording.Validity.VALID)

    #TODO use length field if available
    def get_audio_length(self):
        audio_file = default_storage.open(self.audiofile, 'rb')
        wav = wave.open(audio_file, 'rb')
        duration = wav.getnframes() / wav.getframerate()
        wav.close()
        self.audiofile.close()
        return duration
