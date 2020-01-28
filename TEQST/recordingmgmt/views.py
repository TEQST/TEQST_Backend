from rest_framework import generics, mixins, status
from django.db import models
from .serializers import TextRecordingSerializer, SenctenceRecordingSerializer, SenctenceRecordingUpdateSerializer
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
    
    def perform_create(self, serializer):
        serializer.save(speaker=self.request.user)

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        if not self.get_queryset().exists():
            print('empty')
            response.status_code = status.HTTP_204_NO_CONTENT
        return response

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
    
    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return SenctenceRecordingUpdateSerializer
        return SenctenceRecordingSerializer

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        f = instance.audiofile.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] ='audio/wav'
        response['Content-Length'] =os.path.getsize(instance.audiofile.path)
        return response