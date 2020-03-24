from .serializers import FolderFullSerializer, SharedFolderTextSerializer, SharedFolderSpeakerSerializer, SharedFolderStatsSerializer
from .serializers import TextBasicSerializer, TextFullSerializer, TextStatsSerializer, FolderDetailedSerializer, PublisherSerializer
from .models import Folder, SharedFolder, Text
from usermgmt.permissions import IsPublisher
from usermgmt.models import CustomUser
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, mixins, response, status, views
from rest_framework.exceptions import NotFound, ParseError
from django.http import HttpResponse


class PubFolderListView(generics.ListCreateAPIView):
    """
    url: api/folders/
    use: list the topmost layer of folders for a publisher, folder creation
    """
    queryset = Folder.objects.all()
    serializer_class = FolderFullSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        user = self.request.user
        #the use of the parent param is deprecated. you should get this info with folderDetailView
        if 'parent' in self.request.query_params:
            if not Folder.objects.filter(pk=self.request.query_params['parent']).exists():
                raise NotFound("parent not found")
            if Folder.objects.get(pk=self.request.query_params['parent']).is_shared_folder():
                raise NotFound("parent not found")
            #if parent is a sharedfolder: error message
            return Folder.objects.filter(parent=self.request.query_params['parent'], owner=user.pk)

        return Folder.objects.filter(parent=None, owner=user.pk)  # parent=None means the folder is in the topmost layer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PubFolderDetailedView(generics.RetrieveDestroyAPIView):
    """
    url: api/folders/:id/
    use: retrieve a Folder with its subfolders, Folder deletion
    """
    queryset = Folder.objects.all()
    serializer_class = FolderDetailedSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        # This could exclude Folders which are SharedFolders. This view is only used with folders that aren't shared.
        user = self.request.user
        return Folder.objects.filter(owner=user.pk)


class PubSharedFolderSpeakerView(generics.RetrieveUpdateAPIView):
    """
    url: api/sharedfolders/:id/
    use: retrieve and update the speakers of a shared folder
    """
    queryset = SharedFolder.objects.all()
    serializer_class = SharedFolderSpeakerSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        user = self.request.user
        return SharedFolder.objects.filter(owner=user.pk)


class PubTextListView(generics.ListCreateAPIView):
    """
    url: api/pub/texts/?sharedfolder=123
    use: in the publish tab: retrieve a list of texts contained in a sharedfolder, text upload
    """
    queryset = Text.objects.all()
    serializer_class = TextBasicSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        user = self.request.user
        if 'sharedfolder' in self.request.query_params:
            try:
                if not SharedFolder.objects.filter(pk=self.request.query_params['sharedfolder'], owner=user).exists():
                    raise NotFound("Invalid Sharedfolder id")
                return Text.objects.filter(shared_folder=self.request.query_params['sharedfolder'])
            except ValueError:
                raise NotFound("Invalid sharedfolder id")
        raise NotFound("No sharedfolder specified")
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TextFullSerializer
        return TextBasicSerializer


class SpkTextListView(generics.RetrieveAPIView):
    """
    url: api/spk/sharedfolders/:id/
    use: in speak tab: retrieve a sharedfolder with the texts it contains
    """
    queryset = SharedFolder.objects.all()
    serializer_class = SharedFolderTextSerializer

    def get_object(self):
        sf = super().get_object()
        user = self.request.user
        if user not in sf.speaker.all():
            raise NotFound("This sharedfolder is not shared with you.")
        return sf


class PubTextDetailedView(generics.RetrieveDestroyAPIView):
    """
    url: api/pub/texts/:id/
    use: in publish tab: retrieve a text, text deletion
    """
    queryset = Text.objects.all()
    serializer_class = TextFullSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        user = self.request.user
        return Text.objects.filter(shared_folder__owner=user.pk)

    # TODO maybe this method is not needed
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TextFullSerializer
        return TextBasicSerializer


class SpkTextDetailedView(generics.RetrieveAPIView):
    """
    url: api/spk/texts/:id/
    use: in speak tab: retrieve a text
    """
    queryset = Text.objects.all()
    serializer_class = TextFullSerializer

    def get_queryset(self):
        user = self.request.user
        return Text.objects.filter(shared_folder__sharedfolder__speaker__id=user.id)


class SpkPublisherListView(generics.ListAPIView):
    """
    url: api/publishers/
    use: get list of publishers who own sharedfolders shared with request.user
    """
    queryset = CustomUser.objects.all()
    serializer_class = PublisherSerializer

    def get_queryset(self):
        # does not check for is_publisher. This is not necessary
        
        # possible alternative solution
        # return CustomUser.objects.filter(folder__sharedfolder__speakers=self.request.user)
        # current code
        pub_pks = []
        user = self.request.user
        for shf in user.sharedfolder.all():
            pub_pks.append(shf.owner.pk)
        return CustomUser.objects.filter(pk__in = pub_pks)


class SpkPublisherDetailedView(generics.RetrieveAPIView):
    """
    url: api/publishers/:id/
    use: in speak tab: retrieve a publisher with their folders which they shared with request.user
    """
    queryset = CustomUser.objects.all()
    serializer_class = PublisherSerializer

    def get_object(self):
        pub = super().get_object()
        user = self.request.user
        for shf in user.sharedfolder.all():
            if pub == shf.owner:
                return pub
        raise NotFound('This publisher has not shared any folders with you.')


class SpeechDataDownloadView(views.APIView):
    """
    url: api/download/:id/
    use: Download of speechdata for a given SharedFolder as zip file
    """
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_object(self):
        sf_id = self.kwargs['sf']
        if not SharedFolder.objects.filter(pk=sf_id, owner=self.request.user.pk).exists():
            raise NotFound("Invalid SharedFolder id")
        return SharedFolder.objects.get(pk=sf_id, owner=self.request.user.pk)

    def get(self, request, *args, **kwargs):
        """
        handles a HTTP GET request
        """
        instance = self.get_object()
        if not instance.has_any_recordings():
            raise ParseError("Nothing to download yet.")
        zip_path = instance.create_zip_for_download()
        zipfile = open(zip_path, 'rb')
        resp = HttpResponse()
        resp.write(zipfile.read())
        zipfile.close()
        resp['Content-Type'] = "application/zip"
        return resp


class PubSharedFolderStatsView(generics.RetrieveAPIView):
    """
    url: api/pub/sharedfolders/:id/stats/
    use: get statistics on how far the speakers of a publisher's shared folder are
    """
    queryset = SharedFolder.objects.all()
    serializer_class = SharedFolderStatsSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_object(self):
        sf_id = self.kwargs['pk']
        if not SharedFolder.objects.filter(pk=sf_id, owner=self.request.user.pk).exists():
            raise NotFound("Invalid SharedFolder id")
        return SharedFolder.objects.get(pk=sf_id, owner=self.request.user.pk)


class PubTextStatsView(generics.RetrieveAPIView):
    """
    url: api/pub/texts/:id/stats/
    use: get statistics on how far the speakers are in a given text
    """
    queryset = Text.objects.all()
    serializer_class = TextStatsSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_object(self):
        text_id = self.kwargs['pk']
        if not Text.objects.filter(pk=text_id, shared_folder__owner=self.request.user.pk).exists():
            raise NotFound('Invalid Text id')
        return Text.objects.get(pk=text_id)