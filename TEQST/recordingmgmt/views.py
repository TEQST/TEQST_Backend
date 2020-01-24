from rest_framework import generics, mixins
from django.db import models
from .serializers import TextRecordingSerializer, SenctenceRecordingSerializer
from .models import TextRecording, SenctenceRecording

from django.http import HttpResponse
import os


class TextRecordingView(generics.ListCreateAPIView):
    queryset = TextRecording.objects.all()
    serializer_class = TextRecordingSerializer

    def get_queryset(self):
        user = self.request.user
        if 'text' in self.request.query_params:
            return TextRecording.objects.filter(text=self.request.query_params['text'], speaker=user.pk)
        return TextRecording.objects.none()

class SenctenceRecordingCreateView(generics.CreateAPIView):
    queryset = SenctenceRecording.objects.all()
    serializer_class = SenctenceRecordingSerializer

class SenctenceRecordingUpdateView(generics.RetrieveUpdateAPIView):
    queryset = SenctenceRecording.objects.all()
    serializer_class = SenctenceRecordingSerializer

    def get_object(self):
        rec = self.kwargs['rec']
        if 'index' in self.request.query_params:
            return SenctenceRecording.objects.get(recording__id=rec, index=self.request.query_params['index'])
        return models.return_None()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        f = instance.audiofile.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] ='audio/wav'
        response['Content-Length'] =os.path.getsize(instance.audiofile.path)
        return response