from rest_framework import generics, mixins, response, status, views, exceptions, permissions as rf_permissions
from django import http
from django.db.models import Q
from django.core.files.storage import default_storage
from . import models, serializers
from usermgmt import models as user_models, permissions


class PubFolderListView(generics.ListCreateAPIView):
    """
    url: api/folders/
    use: list the topmost layer of folders for a publisher, folder creation
    """
    queryset = models.Folder.objects.all()
    serializer_class = serializers.FolderFullSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_queryset(self):
        user = self.request.user
        #the use of the parent param is deprecated. you should get this info with folderDetailView
        if 'parent' in self.request.query_params:
            if not models.Folder.objects.filter(pk=self.request.query_params['parent']).exists():
                raise exceptions.NotFound("parent not found")
            if models.Folder.objects.get(pk=self.request.query_params['parent']).is_shared_folder():
                raise exceptions.NotFound("parent not found")
            #if parent is a sharedfolder: error message
            return models.Folder.objects.filter(parent=self.request.query_params['parent'], owner=user.pk)

        return models.Folder.objects.filter(parent=None, owner=user.pk)  # parent=None means the folder is in the topmost layer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PubFolderDetailedView(generics.RetrieveDestroyAPIView):
    """
    url: api/folders/:id/
    use: retrieve a Folder with its subfolders, Folder deletion
    """
    queryset = models.Folder.objects.all()
    serializer_class = serializers.FolderDetailedSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_queryset(self):
        # This could exclude Folders which are SharedFolders. This view is only used with folders that aren't shared.
        user = self.request.user
        return models.Folder.objects.filter(owner=user.pk)


class PubSharedFolderSpeakerView(generics.RetrieveUpdateAPIView):
    """
    url: api/sharedfolders/:id/
    use: retrieve and update the speakers of a shared folder
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderSpeakerSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_queryset(self):
        user = self.request.user
        return models.SharedFolder.objects.filter(owner=user.pk)


class PubSharedFolderListenerView(generics.RetrieveUpdateAPIView):
    """
    url: api/pub/sharedfolders/:id/listeners/
    use: retrieve and update the speakers of a shared folder
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderListenerSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_queryset(self):
        user = self.request.user
        return models.SharedFolder.objects.filter(owner=user.pk)


class PubTextListView(generics.ListCreateAPIView):
    """
    url: api/pub/texts/?sharedfolder=123
    use: in the publish tab: retrieve a list of texts contained in a sharedfolder, text upload
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextBasicSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_queryset(self):
        user = self.request.user
        if 'sharedfolder' in self.request.query_params:
            try:
                if not models.SharedFolder.objects.filter(pk=self.request.query_params['sharedfolder'], owner=user).exists():
                    raise exceptions.NotFound("Invalid Sharedfolder id")
                return models.Text.objects.filter(shared_folder=self.request.query_params['sharedfolder'])
            except ValueError:
                raise exceptions.NotFound("Invalid sharedfolder id")
        raise exceptions.NotFound("No sharedfolder specified")

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.TextFullSerializer
        return serializers.TextBasicSerializer


class SpkTextListView(generics.RetrieveAPIView):
    """
    url: api/spk/sharedfolders/:id/
    use: in speak tab: retrieve a sharedfolder with the texts it contains
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SpkSharedFolderTextSerializer

    def get_object(self):
        sf = super().get_object()
        user = self.request.user
        if user not in sf.speaker.all() and not sf.public:
            raise exceptions.NotFound("This sharedfolder is not shared with you as speaker.")
        return sf


class PubTextDetailedView(generics.RetrieveDestroyAPIView):
    """
    url: api/pub/texts/:id/
    use: in publish tab: retrieve a text, text deletion
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextFullSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_queryset(self):
        user = self.request.user
        return models.Text.objects.filter(shared_folder__owner=user.pk)

    # TODO maybe this method is not needed
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.TextFullSerializer
        return serializers.TextBasicSerializer


class SpkTextDetailedView(generics.RetrieveAPIView):
    """
    url: api/spk/texts/:id/
    use: in speak tab: retrieve a text
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextFullSerializer

    def get_queryset(self):
        user = self.request.user
        return models.Text.objects.filter(Q(shared_folder__speaker__id=user.id) | Q(shared_folder__public=True)).distinct()


class SpkPublisherListView(generics.ListAPIView):
    """
    url: api/publishers/
    use: get list of publishers who own sharedfolders shared with request.user
    """
    queryset = user_models.CustomUser.objects.all()
    serializer_class = serializers.SpkPublisherSerializer

    def get_queryset(self):
        # does not check for is_publisher. This is not necessary

        # possible alternative solution
        # return CustomUser.objects.filter(folder__sharedfolder__speakers=self.request.user)
        # current code
        pub_pks = []
        user = self.request.user
        for shf in user.sharedfolder.all():
            pub_pks.append(shf.owner.pk)
        return user_models.CustomUser.objects.filter(pk__in = pub_pks)


class SpkPublisherDetailedView(generics.RetrieveAPIView):
    """
    url: api/publishers/:id/
    use: in speak tab: retrieve a publisher with their folders which they shared with request.user
    """
    queryset = user_models.CustomUser.objects.all()
    serializer_class = serializers.SpkPublisherSerializer

    def get_object(self):
        pub = super().get_object()
        user = self.request.user
        for shf in user.sharedfolder.all():
            if pub == shf.owner:
                return pub
        raise exceptions.NotFound('This publisher has not shared any folders with you as speaker.')


class SpeechDataDownloadView(views.APIView):
    """
    url: api/download/:id/
    use: Download of speechdata for a given SharedFolder as zip file
    """
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_object(self):
        sf_id = self.kwargs['sf']
        if not models.SharedFolder.objects.filter(pk=sf_id, owner=self.request.user.pk).exists():
            raise exceptions.NotFound("Invalid SharedFolder id")
        return models.SharedFolder.objects.get(pk=sf_id, owner=self.request.user.pk)

    def get(self, request, *args, **kwargs):
        """
        handles a HTTP GET request
        """
        instance = self.get_object()
        if not instance.has_any_recordings():
            raise exceptions.ParseError("Nothing to download yet.")
        zip_path = instance.create_zip_for_download()
        zipfile = default_storage.open(zip_path, 'rb')
        resp = http.HttpResponse()
        resp.write(zipfile.read())
        zipfile.close()
        resp['Content-Type'] = "application/zip"
        return resp


class PubSharedFolderStatsView(generics.RetrieveAPIView):
    """
    url: api/pub/sharedfolders/:id/stats/
    use: get statistics on how far the speakers of a publisher's shared folder are
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_object(self):
        sf_id = self.kwargs['pk']
        if not models.SharedFolder.objects.filter(pk=sf_id, owner=self.request.user.pk).exists():
            raise exceptions.NotFound("Invalid SharedFolder id")
        return models.SharedFolder.objects.get(pk=sf_id, owner=self.request.user.pk)


class PubTextStatsView(generics.RetrieveAPIView):
    """
    url: api/pub/texts/:id/stats/
    use: get statistics on how far the speakers are in a given text
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]

    def get_object(self):
        text_id = self.kwargs['pk']
        if not models.Text.objects.filter(pk=text_id, shared_folder__owner=self.request.user.pk).exists():
            raise exceptions.NotFound('Invalid Text id')
        return models.Text.objects.get(pk=text_id)

class SpkPublicFoldersView(generics.ListAPIView):
    """
    url: api/spk/publicfolders/
    use: get a list of all public folders
    """
    queryset = models.SharedFolder.objects.filter(public=True)
    serializer_class = serializers.PublicFolderSerializer


class LstnPublisherListView(generics.ListAPIView):
    """
    url: api/lstn/publishers/
    use: get list of publishers who own sharedfolders shared with request.user
    """
    queryset = user_models.CustomUser.objects.all()
    serializer_class = serializers.LstnPublisherSerializer

    def get_queryset(self):
        # does not check for is_publisher. This is not necessary

        # possible alternative solution
        # return CustomUser.objects.filter(folder__sharedfolder__speakers=self.request.user)
        # current code
        pub_pks = []
        user = self.request.user
        for shf in user.listenfolder.all():
            pub_pks.append(shf.owner.pk)
        return user_models.CustomUser.objects.filter(pk__in = pub_pks)


class LstnPublisherDetailedView(generics.RetrieveAPIView):
    """
    url: api/lstn/publishers/:id/
    use: in speak tab: retrieve a publisher with their folders which they shared with request.user
    """
    queryset = user_models.CustomUser.objects.all()
    serializer_class = serializers.LstnPublisherSerializer

    def get_object(self):
        pub = super().get_object()
        user = self.request.user
        for shf in user.listenfolder.all():
            if pub == shf.owner:
                return pub
        raise exceptions.NotFound('This publisher has not shared any folders with you as listener.')


class LstnTextListView(generics.RetrieveAPIView):
    """
    url: api/lstn/sharedfolders/:id/texts/
    use: in listen tab: retrieve a sharedfolder with the texts it contains
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.LstnSharedFolderTextSerializer

    def get_object(self):
        sf = super().get_object()
        user = self.request.user
        if user not in sf.listener.all():
            raise exceptions.NotFound("This sharedfolder is not shared with you as listener.")
        return sf


class LstnTextDetailedView(generics.RetrieveAPIView):
    """
    url: api/lstn/texts/:id/
    use: in listen tab: retrieve a text
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextFullSerializer

    def get_queryset(self):
        user = self.request.user
        return models.Text.objects.filter(shared_folder__listener=user)


class LstnSharedFolderStatsView(generics.RetrieveAPIView):
    """
    url: api/lstn/sharedfolders/:id/stats/
    use: get statistics on how far the speakers of a publisher's shared folder are
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated]

    def get_object(self):
        sf_id = self.kwargs['pk']
        if not models.SharedFolder.objects.filter(pk=sf_id, listener=self.request.user).exists():
            raise exceptions.NotFound("Invalid SharedFolder id")
        return models.SharedFolder.objects.get(pk=sf_id, owner=self.request.user.pk)


class LstnTextStatsView(generics.RetrieveAPIView):
    """
    url: api/lstn/texts/:id/stats/
    use: get statistics on how far the speakers are in a given text
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated]

    def get_object(self):
        text_id = self.kwargs['pk']
        if not models.Text.objects.filter(pk=text_id, shared_folder__listener=self.request.user).exists():
            raise exceptions.NotFound('Invalid Text id')
        return models.Text.objects.get(pk=text_id)