from django.contrib import admin
from .models import TextRecording, SentenceRecording

# Register your models here.

admin.site.register(TextRecording)
admin.site.register(SentenceRecording)