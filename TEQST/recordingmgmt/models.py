from django.db import models
from usermgmt.models import CustomUser
from textmgmt.models import Text

class TextRecording(models.Model):
    speaker = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    # is the audiofile really needed?
    audiofile = models.FileField(null=True, blank=True)

    def active_sentence(self):
        return SenctenceRecording.objects.filter(recording=self).count()


def sentence_rec_upload_path(instance, filename):
    sf_path = instance.recording.text.shared_folder.sharedfolder.get_path()
    # it is probably better to discard the filename and create our own
    return sf_path + '/TempAudio/' + filename


class SenctenceRecording(models.Model):
    recording = models.ForeignKey(TextRecording, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    audiofile = models.FileField(upload_to=sentence_rec_upload_path)