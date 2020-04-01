from rest_framework import generics, mixins, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from django.db import models
from .serializers import TextRecordingSerializer, SentenceRecordingSerializer, SentenceRecordingUpdateSerializer
from .models import TextRecording, SentenceRecording
from textmgmt.models import Text

from django.http import HttpResponse
import os


class TextRecordingView(generics.ListCreateAPIView):
    """
    url: api/textrecordings/
    use: retrieval and creation of textrecordings for a given text and request.user
    """
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
        raise NotFound("No text specified")

    
    def perform_create(self, serializer):
        # specify request.user as the speaker of a textrecording upon creation
        serializer.save(speaker=self.request.user)

    def get(self, *args, **kwargs):
        """
        handles the get request
        """
        response = super().get(*args, **kwargs)
        if not self.get_queryset().exists():
            #response.status_code = status.HTTP_204_NO_CONTENT
            response = Response(status=status.HTTP_204_NO_CONTENT)
        return response

class SentenceRecordingCreateView(generics.CreateAPIView):
    """
    url: api/sentencerecordings/
    use: sentencerecodring creation
    """
    queryset = SentenceRecording.objects.all()
    serializer_class = SentenceRecordingSerializer

class SentenceRecordingUpdateView(generics.RetrieveUpdateAPIView):
    """
    url: api/sentencerecordings/:id/
    use: retrieval and update of a single recording of a sentence
    """
    queryset = SentenceRecording.objects.all()
    serializer_class = SentenceRecordingUpdateSerializer

    def get_object(self):
        # the sentencerecording is uniquely defined by a textrecording id (rec) and the index of the sentence within that textrecording (index)
        # rec is part of the core url string
        rec = self.kwargs['rec']
        if not TextRecording.objects.filter(pk=rec, speaker=self.request.user).exists():
            if self.request.method == 'GET':
                if not TextRecording.objects.filter(pk=rec, text__shared_folder__owner=self.request.user).exists():
                    raise NotFound("Invalid Textrecording id")
            else:
                raise NotFound("Invalid Textrecording id")
        # index is a query parameter
        if 'index' in self.request.query_params:
            try:
                if not SentenceRecording.objects.filter(recording__id=rec, index=self.request.query_params['index']).exists():
                    raise NotFound("Invalid index")
                return SentenceRecording.objects.get(recording__id=rec, index=self.request.query_params['index'])
            except ValueError:
                raise NotFound("Invalid index")
        raise NotFound("No index specified")

    def get(self, request, *args, **kwargs):
        """
        handles the get request
        """
        instance = self.get_object()
        f = instance.audiofile.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] = 'audio/wav'
        response['Content-Length'] = os.path.getsize(instance.audiofile.path)
        return response


class SentenceRecordingRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    url: api/sentencerecordings/<tr_id>/<index>/
    use: retrieval and update of a single recording of a sentence
    """
    queryset = SentenceRecording.objects.all()
    serializer_class = SentenceRecordingUpdateSerializer

    def get_object(self):
        # the sentencerecording is uniquely defined by a textrecording id (tr_id) and the index of the sentence within that textrecording (index)
        # tr_id is part of the core url string
        tr_id = self.kwargs['tr_id']
        if not TextRecording.objects.filter(pk=tr_id, speaker=self.request.user).exists():
            if self.request.method == 'GET':
                if not TextRecording.objects.filter(pk=tr_id, text__shared_folder__owner=self.request.user).exists():
                    raise NotFound("Invalid Textrecording id")
            else:
                raise NotFound("Invalid Textrecording id")
        # index is the other part or the url
        index = self.kwargs['index']
        if not SentenceRecording.objects.filter(recording__id=tr_id, index=index).exists():
            raise NotFound("Invalid index")
        return SentenceRecording.objects.get(recording__id=tr_id, index=index)

        

    def get(self, request, *args, **kwargs):
        """
        handles the get request
        """
        instance = self.get_object()
        f = instance.audiofile.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] = 'audio/wav'
        response['Content-Length'] = os.path.getsize(instance.audiofile.path)
        return response