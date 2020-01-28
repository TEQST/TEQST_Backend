from django.db import models
from usermgmt.models import CustomUser
from textmgmt.models import Text
from .storages import OverwriteStorage

#May be needed in a future version
def text_rec_upload_path(instance, filename):
    sf_path = instance.recording.text.shared_folder.sharedfolder.get_path()
    return sf_path + '/AudioData/' + instance.text.id + '_' + instance.speaker.id + '.wav'


class TextRecording(models.Model):
    speaker = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)

    TTS_permission = models.BooleanField(default=True)
    SR_permission = models.BooleanField(default=True)
    # is the audiofile really needed?
    audiofile = models.FileField(upload_to=text_rec_upload_path, null=True, blank=True)

    def active_sentence(self):
        sentence_num = SentenceRecording.objects.filter(recording=self).count() + 1
        # if a speaker is finished with a text this number is one higher than the number of sentences in the text
        return sentence_num


def sentence_rec_upload_path(instance, filename):
    sf_path = instance.recording.text.shared_folder.sharedfolder.get_path()
    return sf_path + '/TempAudio/' + str(instance.recording.id) + '_' + str(instance.index) + '.wav'


class SentenceRecording(models.Model):
    recording = models.ForeignKey(TextRecording, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    audiofile = models.FileField(upload_to=sentence_rec_upload_path, storage=OverwriteStorage())

    def save(self, *args, **kwargs):
        # This should work, but I'm not 100% sure. 
        # Alternative: self.recording.active_sentence() == self.recording.text.sentence_count()
        # is_update = self.pk
        super().save(*args, **kwargs)
        # check is this is the last sentence recording in a text or if this sentence recording is being updated
        # if self.index == self.recording.text.sentence_count() or is_update:
        #     # trigger stm creation
        #     create_textrecording_stm(self.recording.pk)

        #shouldn't this work fine in all cases
        if self.recording.active_sentence() > self.recording.text.sentence_count():
            #print('create stm')
            create_textrecording_stm(self.recording.id)


def create_textrecording_stm(trec_pk):
    """
    create stm and concatenated audio for one recording. These are created upon first completion of a text by a user, 
    and again recreated every time the user rerecords a sentence. The stm does not contain the stm header.
    trec_pk: string = TextRecording pk
    """
    trec = TextRecording.objects.get(pk=trec_pk)
    srecs = SentenceRecording.objects.filter(recording=trec)

    print("#####################\nCreating STM\n#####################")

    #create string with encoded userdata
    user_str = '<' + trec.speaker.gender + ',' + trec.speaker.education + '>'
    username = trec.speaker.username
    current_timestamp = 0

    # create .stm file and open in write mode
    path = 'media/' + trec.text.shared_folder.sharedfolder.get_path() + '/STM/' + trec.text.title + '.stm'
    file = open(path, 'w+')
    #adds some dummy content
    file.write(str(current_timestamp) + ' ' + user_str + ' ' + username)
    file.close()

    # create .wav file for concatenated recordings and open in write mode; set metadata

    # declare and set audioduration variable

    # for every sentencerecording:

        # open sentencerecording file

        # get: filename, mono/stereo info, speaker username, calculate beginning and end of recording (audioduration += end),
        # gather user info to go inside < > (country, edu, gender), utterance
        # userful methods on the text Model would be get_num_of_sentences() and get_sentence_content(index)

        # Question: where do we put the TTS and SR permissions???

        # append gathered info to .stm file

        # append sentencerecording audio data to concatenated file

        # close sentencerecording file

    # close .stm file

    # close concatenated .wav file

    # call the concat_stms()


def concat_stms():
    # this needs some argument. maybe the sharedfolder id or the recording id from which it can get the sharedfolder id
    pass

