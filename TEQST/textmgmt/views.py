from django.shortcuts import render
from .serializers import FolderFullSerializer, FolderBasicSerializer, SharedFolderListSerializer, SharedFolderDetailSerializer
from .serializers import TextBasicSerializer, TextFullSerializer
from .models import Folder, SharedFolder, Text
from usermgmt.permissions import IsPublisher
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, mixins, response, status
from rest_framework.exceptions import NotFound

################################
# important todos:
# - the get_queryset method from textlistview
# - test if sharedfolderbypublisherview works
# - implement view for 'api/publishers/'
################################


class FolderListView(generics.ListCreateAPIView):
    queryset = Folder.objects.all()
    serializer_class = FolderFullSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        user = self.request.user
        if 'parent' in self.request.query_params:
            if not Folder.objects.filter(pk=self.request.query_params['parent']).exists():
                raise NotFound("parent not found")
            if Folder.objects.get(pk=self.request.query_params['parent']).is_shared_folder():
                raise NotFound("parent not found")
            #if parent is a sharedfolder: error message
            return Folder.objects.filter(parent=self.request.query_params['parent'], owner=user.pk)
        return Folder.objects.filter(parent=None, owner=user.pk)
    
    def get(self, request, *args, **kwargs):
        if not self.get_queryset() and 'parent' in self.request.query_params:
            parent_folder = Folder.objects.get(pk=self.request.query_params['parent'])
            return response.Response({"parent_name" : parent_folder.name}, status=status.HTTP_204_NO_CONTENT)
        return super().get(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderDetailedView(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    """
    Update Mixin: Folder name change
    Delete Mixin: Folder deletion
    """
    queryset = Folder.objects.all()
    serializer_class = FolderBasicSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

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
    """
    use: list shared_folders shared with the current user by a specified publisher
    """
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


class SharedFolderDetailView(generics.RetrieveUpdateAPIView):
    """
    use: retrieve and update the speakers of a shared folder
    """
    queryset = SharedFolder.objects.all()
    serializer_class = SharedFolderDetailSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        user = self.request.user
        return SharedFolder.objects.filter(owner=user.pk)


class PublisherTextListView(generics.ListCreateAPIView):
    queryset = Text.objects.all()
    serializer_class = TextBasicSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        # TODO IMPORTANT: Rethink this
        user = self.request.user
        if 'sharedfolder' in self.request.query_params:
            if not SharedFolder.objects.filter(pk=self.request.query_params['sharedfolder']).exists():
                raise NotFound("Invalid Sharedfolder id.")
            if SharedFolder.objects.get(pk=self.request.query_params['sharedfolder']).owner == user:
                return Text.objects.filter(shared_folder=self.request.query_params['sharedfolder'])

        # TODO The 'sharedfolder' query param must be required.
        # better solution would maybe be bad response or error
        # return Text.objects.none()
        raise NotFound("No sharedfolder specified.")
    
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
            if not SharedFolder.objects.filter(pk=self.request.query_params['sharedfolder']).exists():
                raise NotFound("SharedFolder not found")
            if user in SharedFolder.objects.get(pk=self.request.query_params['sharedfolder']).speaker.all():
                return Text.objects.filter(shared_folder=self.request.query_params['sharedfolder'])
        
        # TODO maybe theres a better alternative 
        # return Text.objects.none()
        raise NotFound("No SharedFolder specified")


class PublisherTextDetailedView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Text.objects.all()
    serializer_class = TextFullSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        user = self.request.user
        return Text.objects.filter(shared_folder__owner=user.pk)

    def get_serializer_class(self):
        # TODO using BasicSerializer should not be necessary
        if self.request.method == 'GET':
            return TextFullSerializer
        return TextBasicSerializer


class SpeakerTextDetailedView(generics.RetrieveAPIView):
    queryset = Text.objects.all()
    serializer_class = TextFullSerializer

    def get_queryset(self):
        user = self.request.user
        return Text.objects.filter(shared_folder__sharedfolder__speaker__id=user.id)