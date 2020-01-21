from django.shortcuts import render
from .serializers import FolderFullSerializer, FolderBasicSerializer, SharedFolderListSerializer, SharedFolderSpeakerSerializer
from .serializers import TextBasicSerializer, TextFullSerializer
from .models import Folder, SharedFolder, Text
from rest_framework import generics, mixins

################################
# important todos:
# - the get_queryset method from textlistview
# - test if sharedfolderbypublisherview works
# - implement view for 'api/publishers/'
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
    """
    Update Mixin: Folder name change
    Delete Mixin: Folder deletion
    """
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


class SharedFolderByPublisherView(generics.ListAPIView):
    queryset = SharedFolder.objects.all()
    serializer_class = SharedFolderListSerializer

    def get_queryset(self):
        # TODO test if this works
        # publisher query param should be mandatory
        user = self.request.user
        shared_folders = SharedFolder.objects.filter(speaker=user.pk)
        if 'publisher' in self.request.query_params:
            return shared_folders.filter(owner=self.request.query_params['publisher'])
        #this should never be reached
        return shared_folders


class SharedFolderSpeakerView(generics.RetrieveUpdateAPIView):
    """
    use: retrieve and update the speakers of a shared folder
    """
    queryset = SharedFolder.objects.all()
    serializer_class = SharedFolderSpeakerSerializer

    def get_queryset(self):
        user = self.request.user
        return SharedFolder.objects.filter(owner=user.pk)


class PublisherTextListView(generics.ListCreateAPIView):
    queryset = Text.objects.all()
    serializer_class = TextBasicSerializer

    def get_queryset(self):
        # TODO IMPORTANT: Rethink this
        user = self.request.user
        if 'sharedfolder' in self.request.query_params:
            if SharedFolder.objects.get(pk=self.request.query_params['sharedfolder']).owner == user:
                return Text.objects.filter(shared_folder=self.request.query_params['sharedfolder'])

        # TODO The 'sharedfolder' query param must be required.
        # better solution would maybe be bad response or error
        return Text.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TextFullSerializer
        return TextBasicSerializer


class SpeakerTextListView(generics.ListAPIView):
    queryset = Text.objects.all()
    serializer_class = TextBasicSerializer

    def get_queryset(self):
        user = self.request.user
        if 'sharedfolder' in self.request.query_params:
            if user in SharedFolder.objects.get(pk=self.request.query_params['sharedfolder']).speaker.all():
                return Text.objects.filter(shared_folder=self.request.query_params['sharedfolder'])
        
        # TODO maybe theres a better alternative 
        return Text.objects.none()


class TextDetailedView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Text.objects.all()
    serializer_class = TextFullSerializer
    # TODO make fields sharedfolder, textfile read only; add field content (callable)

    def get_serializer_class(self):
        # TODO using BasicSerializer should not be necessary
        if self.request.method == 'GET':
            return TextFullSerializer
        return TextBasicSerializer