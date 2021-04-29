from django.db import models
from django.conf import settings
from django.core.files import uploadedfile, base
from django.core.files.storage import default_storage
from django.contrib import auth
from textmgmt import models as text_models
from usermgmt import models as user_models
from usermgmt.countries import COUNTRY_CHOICES
from . import storages
import wave, io, re
import librosa
from pathlib import Path


def get_normalized_filename(instance):
    title = re.sub(r"[\- \\\/]", "_", instance.text.title)
    title = title.lower()
    return f'{title}-usr{instance.speaker.id:04d}'


#May be needed in a future version
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

    rec_time_without_rep = models.FloatField(default=0.0)
    rec_time_with_rep = models.FloatField(default=0.0)
    # is the audiofile really needed?
    audiofile = models.FileField(upload_to=text_rec_upload_path, blank=True)
    stmfile = models.FileField(upload_to=stm_upload_path, blank=True)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.audiofile.save('name', base.ContentFile(''), save=False)
            self.stmfile.save('name', base.ContentFile(''), save=False)
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

        if self.recording.is_finished():
            self.recording.create_stm()
    
    def get_audio_length(self):
        audio_file = default_storage.open(self.audiofile, 'rb')
        wav = wave.open(audio_file, 'rb')
        duration = wav.getnframes() / wav.getframerate()
        wav.close()
        self.audiofile.close()
        return duration


#deprecated
def create_textrecording_stm(trec_pk):
    """
    create stm and concatenated audio for one textrecording. These are created upon first completion of a text by a user, 
    and again recreated every time the user rerecords a sentence. The stm does not contain the stm header.
    trec_pk: string = TextRecording pk
    """
    trec = TextRecording.objects.get(pk=trec_pk)
    srecs = SentenceRecording.objects.filter(recording=trec)
    speaker = trec.speaker

    # update logfile
    logpath = Path(trec.text.shared_folder.get_path())/'log.txt'
    add_user_to_log(logpath, trec.speaker)

    #create string with encoded userdata
    user_str = f'<{speaker.gender},{speaker.education},'
    if trec.SR_permission:
        user_str += 'SR'
    if trec.TTS_permission:
        user_str += 'TTS'
    user_str += f',{speaker.country},{speaker.accent}>'
    username = speaker.username
    current_timestamp = 0
    sentences = trec.text.get_content()  

    #Store an empty file at the location of the textrecording STM and wav file, so open has a file to work with
    empty_file = uploadedfile.SimpleUploadedFile('', '')

    # create .stm file and open in write mode
    path = Path(trec.text.shared_folder.get_path())/'STM'/f'{trec.text.title}-{username}.stm'

    #stm_file = io.open(path, 'w+', encoding='utf8')
    if not default_storage.exists(str(path)):
        default_storage.save(str(path), empty_file)
    #stm_file = default_storage.open(path, 'w', encoding='utf8')
    stm_file = default_storage.open(str(path), 'wb')

    # create concatenated wav file and open in write mode (uses 'wave' library)
    wav_path_rel = f'{trec.text.title}-{username}'
    wav_path = Path(trec.text.shared_folder.get_path())/'AudioData'/f'{wav_path_rel}.wav'
    if not default_storage.exists(str(wav_path)):
        default_storage.save(str(wav_path), empty_file)
    
    #wav_file = default_storage.open(str(wav_path), 'wb')
    with default_storage.open(str(wav_path), 'wb') as wav_file:
        wav_full = wave.open(wav_file, 'wb') # wave does not yet support pathlib, therefore the string conversion

        #Create .stm entries for each sentence-recording and concatenate the recording to the 'large' file
        for srec in srecs:
            #wav_audiofile = srec.audiofile.open('rb')
            with srec.audiofile.open('rb') as wav_audiofile:
                wav = wave.open(wav_audiofile, 'rb')

                #On concatenating the first file: also copy all settings
                if current_timestamp == 0:
                    wav_full.setparams(wav.getparams())
                duration = wav.getnframes() / wav.getframerate()

                stm_entry = wav_path_rel + '_' + username + '_' + format_timestamp(current_timestamp) + '_' + format_timestamp(current_timestamp + duration) + ' ' \
                    + wav_path_rel + ' ' + str(wav.getnchannels()) + ' ' + username + ' ' + "{0:.2f}".format(current_timestamp) + ' ' + "{0:.2f}".format(current_timestamp + duration) + ' ' \
                    + user_str + ' ' + sentences[srec.index - 1] + '\n'
                stm_file.write(bytes(stm_entry, encoding='utf-8'))

                current_timestamp += duration

                #copy audio
                wav_full.writeframesraw(wav.readframes(wav.getnframes()))

                #close sentence-recording file
                wav.close()

        #close files
        wav_full.close()
    stm_file.close()
    

    #concatenate all .stm files to include the last changes
    concat_stms(trec.text.shared_folder)


#deprecated
def concat_stms(sharedfolder):
    """
    Concatenate all .stm files in the given sharedfolder to include all changes
    """

    #Build paths and open the 'large' stm in read-mode
    sf_path = sharedfolder.get_path()
    stm_path = sf_path + '/STM'
    temp_stm_names = default_storage.listdir(stm_path)[1]
    #stm_file = default_storage.open(sf_path/f'{sharedfolder.name}.stm', 'w', encoding='utf8')
    stm_file = default_storage.open(str(Path(sf_path)/f'{sharedfolder.name}.stm'), 'wb')

    #Open, concatenate and close the header file
    header_file = open(settings.BASE_DIR/'header.stm', 'rb')
    stm_file.write(header_file.read())
    header_file.close()

    # header entries for country and accent
    speakers = user_models.CustomUser.objects.filter(textrecording__text__shared_folder=sharedfolder)
    countries = set([s.country for s in speakers])
    accents = set([s.accent for s in speakers])
    country_dict = dict(COUNTRY_CHOICES)
    c_header = ';; CATEGORY "3" "COUNTRY" ""\n'
    for country in countries:
        c_header += f';; LABEL "{country}" "{country_dict[country]}" ""\n'
    a_header = ';; CATEGORY "4" "ACCENT" ""\n'
    for accent in accents:
        a_header += f';; LABEL "{accent}" "{accent}" ""\n'
    stm_file.write(bytes(c_header, encoding='utf-8'))
    stm_file.write(bytes(a_header, encoding='utf-8'))

    #concatenate all existing stm files
    for temp_stm_name in temp_stm_names:
        #temp_stm_file = default_storage.open(stm_path/temp_stm_name, 'r', encoding='utf8')
        temp_stm_file = default_storage.open(str(Path(stm_path)/temp_stm_name), 'rb')
        stm_file.write(temp_stm_file.read())
        temp_stm_file.close()
    
    stm_file.close()


def format_timestamp(t):
    return "{0:0>7}".format(int(round(t*100, 0)))


#deprecated
def log_contains_user(path, username):
    #logfile = default_storage.open(str(path), 'rb')
    with default_storage.open(str(path), 'rb') as logfile:
        lines = logfile.readlines()
        for line in lines:
            line = line.decode('utf-8')
            if line[:8] == 'username':
                if line[10:] == username + '\n':
                    return True
        logfile.close()
    return False


#deprecated
def add_user_to_log(path, user):
    if log_contains_user(path, str(user.username)):
        return
    #logfile = default_storage.open(str(path), 'ab')
    file_content = b''
    with default_storage.open(str(path), 'rb') as logfile:
        file_content = logfile.read()
    with default_storage.open(str(path), 'wb') as logfile:
        # logfile.writelines(bytes(line + '\n', encoding='utf-8') for line in [
        #     f'username: {user.username}',
        #     f'birth_year: {user.birth_year}',
        #     f'gender: {user.gender}',
        #     f'education: {user.education}',
        #     f'accent: {user.accent}',
        #     f'country: {user.country}',
        #     '#'
        # ])
        logfile_entry = 'username: ' + str(user.username) + '\n' \
                        + 'email: ' + str(user.email) + '\n' \
                        + 'date_joined: ' + str(user.date_joined) + '\n' \
                        + 'birth_year: ' + str(user.birth_year) + '\n#\n'
        file_content += bytes(logfile_entry, encoding='utf-8')
        logfile.write(file_content)
        logfile.close()
