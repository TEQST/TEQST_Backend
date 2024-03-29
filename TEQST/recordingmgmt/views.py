from rest_framework import generics, status, exceptions, response, permissions as rf_permissions
from django import http
from django.core import exceptions as core_exceptions
from django.db.models import Q
from . import serializers, models
from textmgmt import models as text_models, permissions as text_permissions
from usermgmt import permissions

from pathlib import Path


class TextRecordingView(generics.ListCreateAPIView):
    """
    url: api/textrecordings/
    use: retrieval and creation of textrecordings for a given text and request.user
    When creating a TextRecording, the root uuid has to be sent with the request body
    """
    queryset = models.TextRecording.objects.all()
    serializer_class = serializers.TextRecordingSerializer

    def get_queryset(self):
        user = self.request.user
        if 'text' in self.request.query_params:
            try:
                if not text_models.Text.objects.filter(Q(pk=self.request.query_params['text'])).exists():
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



#This is currently used for recording updates
class SentenceRecordingUpdateView(generics.RetrieveUpdateAPIView):
    """
    url: api/sentencerecordings/:id/
    use: retrieval and update of a single recording of a sentence
    """
    queryset = models.SentenceRecording.objects.all()
    serializer_class = serializers.SentenceRecordingUpdateSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsSpeaker]
    
    def get_object(self):
        try:
            trec = models.TextRecording.objects.get(id=self.kwargs['rec'])
            self.check_object_permissions(self.request, trec)
            if not 'index' in self.request.query_params:
                raise exceptions.NotFound('No index specified')
            srec = trec.srecs.get(sentence__index=self.request.query_params['index'])
            self.check_object_permissions(self.request, srec)
            return srec
        except (core_exceptions.ObjectDoesNotExist, core_exceptions.MultipleObjectsReturned):
            raise exceptions.NotFound('Invalid recording specified')
        
    # Useful for browsable API to have a default get response
    #def get(self, request, *args, **kwargs):
    #    instance = self.get_object()
    #    return http.FileResponse(instance.audiofile.open('rb'))



#This is currently used for recording audio retrieval
class SentenceRecordingRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    url: api/sentencerecordings/<tr_id>/<index>/
    use: retrieval and update of a single recording of a sentence
    """
    queryset = models.SentenceRecording.objects.all()
    serializer_class = serializers.SentenceRecordingUpdateSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsSpeaker | permissions.IsOwner | permissions.IsListener]

    def get_object(self):
        try:
            trec = models.TextRecording.objects.get(id=self.kwargs['tr_id'])
            self.check_object_permissions(self.request, trec)
            srec = trec.srecs.get(sentence__index=self.kwargs['index'])
            self.check_object_permissions(self.request, srec)
            return srec
        except (core_exceptions.ObjectDoesNotExist, core_exceptions.MultipleObjectsReturned):
            raise exceptions.NotFound('Invalid recording specified')

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        return http.FileResponse(instance.audiofile.open('rb'))