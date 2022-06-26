from rest_framework import generics, response, status, views, exceptions, decorators, permissions as rf_permissions, \
    serializers as rf_serializers
from django import http
from django.db.models import Q
from django.core.files.storage import default_storage
from . import models, serializers, permissions as text_permissions
from usermgmt import models as user_models, permissions
from pathlib import Path


@decorators.api_view(['POST'])
@decorators.permission_classes([rf_permissions.IsAuthenticated, permissions.IsPublisher])
def multi_delete_folders(request):
    result, _ = request.user.folder.filter(id__in=request.data).delete()
    if result == 0:
        raise exceptions.NotFound('No folders matched your list of ids')
    return response.Response(status=204)


@decorators.api_view(['POST'])
@decorators.permission_classes([rf_permissions.IsAuthenticated, permissions.IsPublisher])
def multi_delete_texts(request):
    result, _ = models.Text.objects.filter(shared_folder__owner=request.user, id__in=request.data).delete()
    if result == 0:
        raise exceptions.NotFound('No texts matched your list of ids')
    return response.Response(status=204)


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
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]


class PubSharedFolderSpeakerView(generics.RetrieveUpdateAPIView):
    """
    url: api/sharedfolders/:id/
    use: retrieve and update the speakers of a shared folder
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderSpeakerSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]


class PubSharedFolderListenerView(generics.RetrieveUpdateAPIView):
    """
    url: api/pub/sharedfolders/:id/listeners/
    use: retrieve and update the speakers of a shared folder
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderListenerSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]


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
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsSpeaker | text_permissions.BelowRoot | text_permissions.IsRoot]


class PubTextDetailedView(generics.RetrieveDestroyAPIView):
    """
    url: api/pub/texts/:id/
    use: in publish tab: retrieve a text, text deletion
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextFullSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]

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
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsSpeaker | text_permissions.BelowRoot]


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
        user = self.request.user
        pub_pks = user.sharedfolder.all().values_list('owner', flat=True)
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
        if user.sharedfolder.filter(owner=pub).exists():
            return pub
        raise exceptions.PermissionDenied('This publisher has not shared any folders with you as speaker.')


class SpeechDataDownloadView(generics.RetrieveAPIView):
    """
    url: api/download/:id/
    use: Download of speechdata for a given SharedFolder as zip file
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SpkSharedFolderTextSerializer #Any serializer that identifies SharedFolders would be possible here
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]

    def get(self, request, *args, **kwargs):
        """
        handles a HTTP GET request
        """
        instance = self.get_object()
        if not instance.has_any_recordings():
            raise exceptions.ParseError("Nothing to download yet.")
        zip_path = instance.create_zip_for_download()
        
        # zipfile = default_storage.open(zip_path, 'rb')
        # resp = http.HttpResponse()
        # resp.write(zipfile.read())
        # zipfile.close()
        # resp['Content-Type'] = "application/zip"
        resp = http.FileResponse(default_storage.open(zip_path, 'rb'), as_attachment=True, filename="download.zip")
        #resp = http.FileResponse(open(zip_path, 'rb'), as_attachment=True, filename="download.zip")

        # resp = http.HttpResponse(status=status.HTTP_200_OK)
        # resp.write("file created")
        return resp


class PubSharedFolderStatsView(generics.RetrieveAPIView):
    """
    url: api/pub/sharedfolders/:id/stats/
    use: get statistics on how far the speakers of a publisher's shared folder are
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]


class PubTextStatsView(generics.RetrieveAPIView):
    """
    url: api/pub/texts/:id/stats/
    use: get statistics on how far the speakers are in a given text
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]


class SpkPublicFoldersView(generics.ListAPIView):
    """
    url: api/spk/publicfolders/
    use: get a list of all public folders
    """
    queryset = models.SharedFolder.objects.filter(public=True)
    serializer_class = serializers.PublicFolderSerializer


'''
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
        user = self.request.user
        pub_pks = user.listenfolder.all().values_list('owner', flat=True)
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
        if user.listenfolder.filter(owner=pub).exists():
            return pub
        raise exceptions.PermissionDenied('This publisher has not shared any folders with you as listener.')
'''


class LstnTextListView(generics.RetrieveAPIView):
    """
    url: api/lstn/sharedfolders/:id/texts/
    use: in listen tab: retrieve a sharedfolder with the texts it contains
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.LstnSharedFolderTextSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]


class LstnTextDetailedView(generics.RetrieveAPIView):
    """
    url: api/lstn/texts/:id/
    use: in listen tab: retrieve a text
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextFullSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]


'''
class LstnSharedFolderStatsView(generics.RetrieveAPIView):
    """
    url: api/lstn/sharedfolders/:id/stats/
    use: get statistics on how far the speakers of a publisher's shared folder are
    """
    queryset = models.SharedFolder.objects.all()
    serializer_class = serializers.SharedFolderStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]


class LstnTextStatsView(generics.RetrieveAPIView):
    """
    url: api/lstn/texts/:id/stats/
    use: get statistics on how far the speakers are in a given text
    """
    queryset = models.Text.objects.all()
    serializer_class = serializers.TextStatsSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]
'''


class SpkFolderDetailView(generics.RetrieveAPIView):

    class OutputSerializer(rf_serializers.ModelSerializer):
        
        class NestedSerializer(rf_serializers.ModelSerializer):
            class Meta:
                model = models.Folder
                fields = ['id', 'name', 'is_sharedfolder']

        subfolder = NestedSerializer(many=True)
        class Meta:
            model = models.Folder
            fields = ['id', 'name', 'owner', 'parent', 'subfolder', 'is_sharedfolder']

    queryset = models.Folder.objects.all()
    serializer_class = OutputSerializer
    permission_classes = [rf_permissions.IsAuthenticated, text_permissions.IsRoot | text_permissions.BelowRoot]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if text_permissions.IsRoot().has_object_permission(request, self, instance):
            instance.parent = None
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)


#TODO untested
class PubListenerPermissionView(generics.ListCreateAPIView):

    class InputSerializer(rf_serializers.ModelSerializer):
        class Meta:
            model = models.ListenerPermission
            fields = ['folder', 'listeners', 'speakers', 'accents']

    class OutputSerializer(rf_serializers.ModelSerializer):
        class Meta:
            model = models.ListenerPermission
            fields = ['folder', 'listeners', 'speakers', 'accents']

    queryset = models.ListenerPermission.objects.all()
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]

    def get_serializer_class(self):
        #TODO extract into mixin
        if self.request.mode == 'GET':
            return self.OutputSerializer
        else:
            return self.InputSerializer