from rest_framework import generics, mixins, status, exceptions, response
from django.db.models import Q
from . import serializers, models
from textmgmt import models as text_models

from django.http import HttpResponse
from pathlib import Path


class TextRecordingView(generics.ListCreateAPIView):
    """
    url: api/textrecordings/
    use: retrieval and creation of textrecordings for a given text and request.user
    """
    queryset = models.TextRecording.objects.all()
    serializer_class = serializers.TextRecordingSerializer

    def get_queryset(self):
        user = self.request.user
        if 'text' in self.request.query_params:
            try:
                if not text_models.Text.objects.filter(Q(pk=self.request.query_params['text']), Q(shared_folder__speaker=user) | Q(shared_folder__public=True)).exists():
                    raise exceptions.NotFound("Invalid text id")
                return models.TextRecording.objects.filter(text=self.request.query_params['text'], speaker=user.pk)
            except ValueError:
                raise exceptions.NotFound("Invalid text id")
            # if not user in Text.objects.get(pk=self.request.query_params['text']).shared_folder.sharedfolder.speaker.all():
            #     raise NotFound("Invalid text id")
        raise exceptions.NotFound("No text specified")

    
    def perform_create(self, serializer):
        # specify request.user as the speaker of a textrecording upon creation
        serializer.save(speaker=self.request.user)

    def get(self, *args, **kwargs):
        """
        handles the get request
        """
        resp = super().get(*args, **kwargs)
        if not self.get_queryset().exists():
            #response.status_code = status.HTTP_204_NO_CONTENT
            resp = response.Response(status=status.HTTP_204_NO_CONTENT)
        return resp

class SentenceRecordingCreateView(generics.CreateAPIView):
    """
    url: api/sentencerecordings/
    use: sentencerecodring creation
    """
    queryset = models.SentenceRecording.objects.all()
    serializer_class = serializers.SentenceRecordingSerializer

class SentenceRecordingUpdateView(generics.RetrieveUpdateAPIView):
    """
    url: api/sentencerecordings/:id/
    use: retrieval and update of a single recording of a sentence
    """
    queryset = models.SentenceRecording.objects.all()
    serializer_class = serializers.SentenceRecordingUpdateSerializer

    def get_object(self):
        # the sentencerecording is uniquely defined by a textrecording id (rec) and the index of the sentence within that textrecording (index)
        # rec is part of the core url string
        rec = self.kwargs['rec']
        if not models.TextRecording.objects.filter(pk=rec, speaker=self.request.user).exists():
            if self.request.method == 'GET':
                if not models.TextRecording.objects.filter(pk=rec, text__shared_folder__owner=self.request.user).exists():
                    if not models.TextRecording.objects.filter(pk=rec, text__shared_folder__listener=self.request.user).exists():
                        raise exceptions.NotFound("Invalid Textrecording id")
            else:
                raise exceptions.NotFound("Invalid Textrecording id")
        # index is a query parameter
        if 'index' in self.request.query_params:
            try:
                if not models.SentenceRecording.objects.filter(recording__id=rec, sentence__index=self.request.query_params['index']).exists():
                    raise exceptions.NotFound("Invalid index")
                return models.SentenceRecording.objects.get(recording__id=rec, sentence__index=self.request.query_params['index'])
            except ValueError:
                raise exceptions.NotFound("Invalid index")
        raise exceptions.NotFound("No index specified")

    def get(self, request, *args, **kwargs):
        """
        handles the get request
        """
        instance = self.get_object()
        f = instance.audiofile.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] = 'audio/wav'
        response['Content-Length'] = instance.audiofile.size
        return response


class SentenceRecordingRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    url: api/sentencerecordings/<tr_id>/<index>/
    use: retrieval and update of a single recording of a sentence
    """
    queryset = models.SentenceRecording.objects.all()
    serializer_class = serializers.SentenceRecordingUpdateSerializer

    def get_object(self):
        # the sentencerecording is uniquely defined by a textrecording id (tr_id) and the index of the sentence within that textrecording (index)
        # tr_id is part of the core url string
        tr_id = self.kwargs['tr_id']
        if not models.TextRecording.objects.filter(pk=tr_id, speaker=self.request.user).exists():
            if self.request.method == 'GET':
                if not models.TextRecording.objects.filter(pk=tr_id, text__shared_folder__owner=self.request.user).exists():
                    if not models.TextRecording.objects.filter(pk=tr_id, text__shared_folder__listener=self.request.user).exists():
                        raise exceptions.NotFound("Invalid Textrecording id")
            else:
                raise exceptions.NotFound("Invalid Textrecording id")
        # index is the other part or the url
        index = self.kwargs['index']
        if not models.SentenceRecording.objects.filter(recording__id=tr_id, index=index).exists():
            raise exceptions.NotFound("Invalid index")
        return models.SentenceRecording.objects.get(recording__id=tr_id, index=index)

        

    def get(self, request, *args, **kwargs):
        """
        handles the get request
        """
        instance = self.get_object()
        f = instance.audiofile.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] = 'audio/wav'
        response['Content-Length'] = instance.audiofile.size
        return response