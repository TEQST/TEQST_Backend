from django.db import models
from usermgmt.models import CustomUser
from textmgmt.models import Text

class TextRecording(models.Model):
    speaker = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    audiofile = models.FileField()

class SenctenceRecording(models.Model):
    recording = models.ForeignKey(TextRecording, on_delete=models.CASCADE)
    index = models.IntegerField()