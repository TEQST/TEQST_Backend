from django.shortcuts import render
from .serializers import FolderFullSerializer, FolderBasicSerializer, SharedFolderSerializer
from .serializers import TextBasicSerializer, TextFullSerializer
from .models import Folder, SharedFolder, Text
from rest_framework import generics, mixins

################################
# important todos:
# - the get_queryset method from textlistview
################################


class FolderListView(generics.ListCreateAPIView):
    queryset = Folder.objects.all()
    serializer_class = FolderFullSerializer

    def get_queryset(self):
        user = self.request.user
        if 'parent' in self.request.query_params:
            #if parent is a sharedfolder: error message
            return Folder.objects.filter(parent=self.request.query_params['parent'], owner=user.pk)
        return Folder.objects.filter(parent=None, owner=user.pk)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderDetailedView(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Folder.objects.all()
    serializer_class = FolderBasicSerializer

    # not sure if this is really necessary
    def get_queryset(self):
        user = self.request.user
        return Folder.objects.filter(owner=user.pk)

    # the get method and the retreivemodelmixin are only here for debug reasons
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class SharedFolderView(generics.ListAPIView):
    queryset = SharedFolder.objects.all()
    serializer_class = SharedFolderSerializer

    def get_queryset(self):
        user = self.request.user
        return SharedFolder.objects.filter(speaker=user.pk)


class TextListView(generics.ListCreateAPIView):
    queryset = Text.objects.all()
    serializer_class = TextBasicSerializer

    def get_queryset(self):
        # TODO IMPORTANT: Rethink this
        user = self.request.user
        if 'sharedfolder' in self.request.query_params:
            return Text.objects.filter(shared_folder=self.request.query_params['sharedfolder'])
        # TODO this cant be the alternative. The 'sharedfolder' query param must be required
        return Text.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TextFullSerializer
        return TextBasicSerializer


class TextDetailedView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Text.objects.all()
    serializer_class = TextFullSerializer
    # TODO make fields sharedfolder, textfile read only; add field content (callable)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TextFullSerializer
        return TextBasicSerializer