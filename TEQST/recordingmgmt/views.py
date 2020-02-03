from rest_framework import generics, mixins, status
from rest_framework.exceptions import NotFound
from django.db import models
from .serializers import TextRecordingSerializer, SentenceRecordingSerializer, SentenceRecordingUpdateSerializer
from .models import TextRecording, SentenceRecording
from textmgmt.models import Text

from django.http import HttpResponse
import os


class TextRecordingView(generics.ListCreateAPIView):
    queryset = TextRecording.objects.all()
    serializer_class = TextRecordingSerializer

    def get_queryset(self):
        user = self.request.user
        if 'text' in self.request.query_params:
            try:
                if not Text.objects.filter(pk=self.request.query_params['text'], shared_folder__sharedfolder__speaker=user).exists():
                    raise NotFound("Invalid text id")
                return TextRecording.objects.filter(text=self.request.query_params['text'], speaker=user.pk)
            except ValueError:
                raise NotFound("Invalid text id")
            # if not user in Text.objects.get(pk=self.request.query_params['text']).shared_folder.sharedfolder.speaker.all():
            #     raise NotFound("Invalid text id")
            # return TextRecording.objects.filter(text=self.request.query_params['text'], speaker=user.pk)
        # return TextRecording.objects.none()
        raise NotFound("No text specified")

    
    def perform_create(self, serializer):
        serializer.save(speaker=self.request.user)

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        if not self.get_queryset().exists():
            response.status_code = status.HTTP_204_NO_CONTENT
        return response

class SentenceRecordingCreateView(generics.CreateAPIView):
    queryset = SentenceRecording.objects.all()
    serializer_class = SentenceRecordingSerializer

class SentenceRecordingUpdateView(generics.RetrieveUpdateAPIView):
    queryset = SentenceRecording.objects.all()
    serializer_class = SentenceRecordingSerializer

    def get_object(self):
        rec = self.kwargs['rec']
        if not TextRecording.objects.filter(pk=rec).exists():
            raise NotFound("Invalid Textrecording id")
        if 'index' in self.request.query_params:
            try:
                if not SentenceRecording.objects.filter(recording__id=rec, index=self.request.query_params['index']).exists():
                    raise NotFound("Invalid index")
                return SentenceRecording.objects.get(recording__id=rec, index=self.request.query_params['index'])
            except ValueError:
                raise NotFound("Invalid index")
        raise NotFound("No index specified")
    
    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return SentenceRecordingUpdateSerializer
        return SentenceRecordingSerializer

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        f = instance.audiofile.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] ='audio/wav'
        response['Content-Length'] =os.path.getsize(instance.audiofile.path)
        return response