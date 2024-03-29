from rest_framework import generics, response, status, views, exceptions, decorators, permissions as rf_permissions, \
    serializers as rf_serializers
from django import http
from django.core.files import base as base_files, uploadedfile
from django.db.models import Q
from django.core.files.storage import default_storage
from . import models, folderstats, serializers, stats, utils, permissions as text_permissions
from usermgmt import models as user_models, permissions, serializers as user_serializers
import calendar, datetime, codecs, pathlib


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
    Creating texts through this view is deprecated
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


class SpkFolderDetailView(generics.RetrieveAPIView):
    """
    url: api/spk/folders/:id/
    use: retrieve a folder with its subfolders as a speaker
    """

    class OutputSerializer(rf_serializers.ModelSerializer):
        
        class NestedSerializer(rf_serializers.ModelSerializer):
            class Meta:
                model = models.Folder
                fields = ['id', 'name', 'is_sharedfolder']

        subfolder = NestedSerializer(many=True)
        path = rf_serializers.CharField(read_only=True, source='get_readable_path')
        class Meta:
            model = models.Folder
            fields = ['id', 'name', 'owner', 'path', 'parent', 'subfolder', 'is_sharedfolder']

    queryset = models.Folder.objects.all()
    serializer_class = OutputSerializer
    permission_classes = [rf_permissions.IsAuthenticated, text_permissions.IsRoot | text_permissions.BelowRoot]

    def get_object(self):
        obj = super().get_object()

        # Don't show parent of root folder; Update recent projects entry
        if text_permissions.IsRoot().has_object_permission(self.request, self, obj):
            obj.parent = None
            models.RecentProject.update_folder_for_speaker(self.request.user, obj)
        
        return obj



class SpkRecentProjectView(generics.ListAPIView):

    class OutputSerializer(rf_serializers.ModelSerializer):

        class NestedSerializer(rf_serializers.ModelSerializer):
            path = rf_serializers.CharField(read_only=True, source='get_readable_path')
            class Meta:
                model = models.Folder
                fields = ['id', 'name', 'owner', 'path', 'parent', 'is_sharedfolder', 'root']

        folder = NestedSerializer()

        class Meta:
            model = models.RecentProject
            fields = ['folder', 'last_access']
        

    queryset = models.RecentProject.objects.none()
    serializer_class = OutputSerializer

    def get_queryset(self):
        models.RecentProject.add_default_folders_for_speaker(self.request.user)
        return self.request.user.recentproject_set.all().order_by('-last_access')
        

class PubListenerPermissionView(generics.ListCreateAPIView):
    """
    url: api/pub/listeners/?folder=:id
    use: as publisher share a folder+speakers to one or many listeners or view all permissions for a folder
    """

    class FilterSerializer(rf_serializers.Serializer):
        folder = rf_serializers.PrimaryKeyRelatedField(queryset=models.Folder.objects.all())

    class InputSerializer(rf_serializers.ModelSerializer):
        accents = rf_serializers.ListField(child=rf_serializers.CharField())

        class Meta:
            model = models.ListenerPermission
            fields = ['folder', 'listeners', 'speakers', 'accents', 'all_speakers']

        def validate_folder(self, value):
            if self.context['request'].user != value.owner:
                raise exceptions.PermissionDenied("You do not own this folder")
            return value

    class OutputSerializer(rf_serializers.ModelSerializer):
        accents = rf_serializers.ListField(child=rf_serializers.CharField())
        listeners = user_serializers.UserBasicSerializer(many=True, read_only=True)
        speakers = user_serializers.UserBasicSerializer(many=True, read_only=True)

        class Meta:
            model = models.ListenerPermission
            fields = ['id', 'listeners', 'speakers', 'accents', 'all_speakers']


    queryset = models.ListenerPermission.objects.all()
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]

    def get_queryset(self):
        qs = super().get_queryset()
        filter_ser = self.FilterSerializer(data=self.request.query_params)
        filter_ser.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, filter_ser.validated_data['folder'])
        return qs.filter(folder=filter_ser.validated_data['folder'])

    def get_serializer_class(self):
        #TODO extract into mixin
        if self.request.method == 'GET':
            return self.OutputSerializer
        else:
            return self.InputSerializer


class PubListenerPermissionChangeView(generics.RetrieveUpdateDestroyAPIView):
    """
    url: api/pub/listeners/:id/
    use: as a publisher, change the listeners+speakers for a given permission view
    """

    class InputSerializer(rf_serializers.ModelSerializer):
        accents = rf_serializers.ListField(child=rf_serializers.CharField())

        class Meta:
            model = models.ListenerPermission
            fields = ['listeners', 'speakers', 'accents']

        def validate_folder(self, value):
            if self.context['request'].user != value.owner:
                raise exceptions.PermissionDenied("You do not own this folder")
            return value

    class OutputSerializer(rf_serializers.ModelSerializer):
        accents = rf_serializers.ListField(child=rf_serializers.CharField())
        listeners = user_serializers.UserBasicSerializer(many=True, read_only=True)
        speakers = user_serializers.UserBasicSerializer(many=True, read_only=True)

        class Meta:
            model = models.ListenerPermission
            fields = ['id', 'listeners', 'speakers', 'accents']


    queryset = models.ListenerPermission.objects.all()
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]

    def get_serializer_class(self):
        #TODO extract into mixin
        if self.request.method == 'GET':
            return self.OutputSerializer
        else:
            return self.InputSerializer


class LstnFolderListView(generics.ListAPIView):
    """
    url:
    use: as listener, retrieve a list of folders to which you have access
    """

    class OutputSerializer(rf_serializers.ModelSerializer):
        is_sharedfolder = rf_serializers.BooleanField(source='is_shared_folder')
        # is_sharedfolder in the sense that this folder has a corresponding Sharedfolder object with the same pk as this Folder
        
        class Meta:
            model = models.Folder
            #TODO include root?
            fields = ['id', 'name', 'is_sharedfolder']

    queryset = models.Folder.objects.all()
    serializer_class = OutputSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(lstn_permissions__listeners=self.request.user)
        

class LstnFolderDetailView(generics.RetrieveAPIView):
    """
    url: 
    use: as listener, retrieve a folder to which you have access, including its subfolders
    """

    class OutputSerializer(rf_serializers.ModelSerializer):

        class NestedSerializer(rf_serializers.ModelSerializer):
            is_sharedfolder = rf_serializers.BooleanField(source='is_shared_folder', read_only=True)
            # is_sharedfolder in the sense that this folder has a corresponding Sharedfolder object with the same pk as this Folder
            
            class Meta:
                model = models.Folder
                #TODO include root?
                fields = ['id', 'name', 'is_sharedfolder']
                read_only_fields = ['name']

        parent = rf_serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True)
        is_sharedfolder = rf_serializers.BooleanField(source='is_shared_folder')
        subfolder = NestedSerializer(many=True)
        # is_sharedfolder in the sense that this folder has a corresponding Sharedfolder object with the same pk as this Folder
        
        class Meta:
            model = models.Folder
            fields = ['id', 'name', 'owner', 'parent', 'subfolder', 'is_sharedfolder']

    queryset = models.Folder.objects.all()
    serializer_class = OutputSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]

    def get_object(self):
        instance = super().get_object()
        if not instance.parent is None:
            if not instance.parent.is_listener(self.request.user):
                instance.parent = None
        return instance


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


class LstnSharedFolderStatsView(generics.RetrieveAPIView):
    """
    url: api/lstn/sharedfolders/:id/stats/
    use: get statistics on how far the speakers of a publisher's shared folder are
    """

    class OutputSerializer(rf_serializers.ModelSerializer):
        speakers = rf_serializers.SerializerMethodField(read_only=True, method_name='get_speaker_stats')

        class Meta:
            model = models.SharedFolder
            fields = ['id', 'name', 'speakers']
            read_only_fields = fields
        
        def get_speaker_stats(self, obj):
            user = self.context['request'].user
            perm_qs = text_permissions.get_listener_permissions(obj, user)
            user_list = text_permissions.get_combined_speakers(perm_qs)
            return stats.sharedfolder_stats(obj, user_filter=user_list)

    queryset = models.SharedFolder.objects.all()
    serializer_class = OutputSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]


class LstnTextStatsView(generics.RetrieveAPIView):
    """
    url: api/lstn/texts/:id/stats/
    use: get statistics on how far the speakers are in a given text
    """

    class OutputSerializer(rf_serializers.ModelSerializer):
        speakers = rf_serializers.SerializerMethodField(read_only=True, method_name='get_speaker_stats')
        total = rf_serializers.IntegerField(read_only=True, source='sentence_count')

        class Meta:
            model = models.Text
            fields = ['id', 'title', 'total', 'speakers']
            read_only_fields = fields
        
        def get_speaker_stats(self, obj):
            user = self.context['request'].user
            perm_qs = text_permissions.get_listener_permissions(obj.shared_folder, user)
            user_list = text_permissions.get_combined_speakers(perm_qs)
            return stats.text_stats(obj, user_filter=user_list)

    queryset = models.Text.objects.all()
    serializer_class = OutputSerializer
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsListener]



class PubFolderStatsView(generics.RetrieveAPIView):
    """
    url: /api/pub/:id/stats/
    params: ?month=<iso-8601> or ?start=<iso-8601>&end=<iso-8601>
    use: get stats for folder as excel-sheet,
        `month` only considers year and month
        `start` & `end` consider year, month and day
    """

    class FilterSerializerBasic(rf_serializers.Serializer):
        month = rf_serializers.IntegerField(min_value=1, max_value=12)
        year = rf_serializers.IntegerField()

    class FilterSerializerDetailed(rf_serializers.Serializer):
        start = rf_serializers.DateField()
        end = rf_serializers.DateField()

    queryset = models.Folder.objects.all()
    serializer_class = None
    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher, permissions.IsOwner]

    def parse_basic(self, request):
        filter_ser = self.FilterSerializerBasic(data=request.query_params)
        filter_ser.is_valid(raise_exception=True)
        month = filter_ser.validated_data['month']
        year = filter_ser.validated_data['year']
        last_day = calendar.monthrange(year, month)[1]
        start = datetime.date(year, month, 1)
        end = datetime.date(year, month, last_day)
        return start, end

    def parse_detailed(self, request):
        filter_ser = self.FilterSerializerDetailed(data=request.query_params)
        filter_ser.is_valid(raise_exception=True)
        start = filter_ser.validated_data['start']
        end = filter_ser.validated_data['end']
        return start, end

    def get(self, request, *args, **kwargs):
        instance: models.Folder = self.get_object()
        
        if 'month' in request.query_params.keys() and \
            'year' in request.query_params.keys():
            start, end = self.parse_basic(request)
        elif 'end' in request.query_params.keys() and \
            'start' in request.query_params.keys():
            start, end = self.parse_detailed(request)
        else:
            raise rf_serializers.ValidationError(
                "Query params have to either specify 'month&year' or 'start&end'"
            )

        fsc_class = folderstats.FolderStatMultiCollector
        if not instance.subfolder.exists():
            fsc_class = folderstats.FolderStatSingleCollector
        fsc = fsc_class(root=instance, start=start, end=end)
        filename = f"{fsc.root.name}_{fsc.start.strftime('%d-%m-%Y')}_{fsc.end.strftime('%d-%m-%Y')}"
        resp = http.HttpResponse(headers={
            "Content-Type": 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            "Content-Disposition": f'attachment; filename={filename}.xlsx'
        })
        fsc.agg_data.to_excel(resp, index=True)
        return resp


FILENAMES = 'filenames'
CONCAT = 'concat'
NUMBERING = 'numbering'
class PubTextUploadView(generics.CreateAPIView):

    class InputSerializer(rf_serializers.Serializer):
        parent = serializers.SharedFolderPKField()
        textfile = rf_serializers.ListField(child=rf_serializers.FileField(), write_only=True)
        title = rf_serializers.CharField()
        language = rf_serializers.PrimaryKeyRelatedField(
            queryset=user_models.Language.objects.all())
        
        max_chars = rf_serializers.IntegerField(required=False)
        max_lines = rf_serializers.IntegerField(required=False)
        separator = rf_serializers.CharField(required=False, trim_whitespace=False)
        tokenize = rf_serializers.BooleanField(default=False)

        naming = rf_serializers.ChoiceField(
            choices=[FILENAMES, CONCAT, NUMBERING],
            default=CONCAT,
        )

        def validate(self, data: dict):
            if data.get('tokenize', False) and data.get('separator', None) is not None:
                raise rf_serializers.ValidationError(
                    "Cannot specify both 'tokenize' and 'separator'")
            return data

    permission_classes = [rf_permissions.IsAuthenticated, permissions.IsPublisher]
    serializer_class = InputSerializer

    def perform_create(self, serializer: InputSerializer):

        parent: models.Folder = serializer.validated_data['parent']
        textfile = serializer.validated_data['textfile']
        title: str = serializer.validated_data['title']
        language: user_models.Language = serializer.validated_data['language']

        max_chars: int = serializer.validated_data.get('max_chars', None)
        max_lines: int = serializer.validated_data.get('max_lines', None)
        separator: str = serializer.validated_data.get('separator', None)
        tokenize: bool = serializer.validated_data.get('tokenize', False)

        naming: str = serializer.validated_data['naming']

        if separator is None:
            separator = '\n\n'
        else:
            # Unescape (experimental decode feature)
            sep_bytes: bytes = codecs.escape_decode(separator)[0]
            separator = sep_bytes.decode()

        content: 'list[tuple[str, str]]'
        content = []        

        if naming == CONCAT:
            pre_split = []
            for file in textfile:
                pre_split += utils.parse_file(file, separator, tokenize, language.english_name)
            loc_content = utils.split_lines(pre_split, max_lines, max_chars)
            for i, text in enumerate(loc_content):
                name = title
                if len(loc_content) > 1:
                    name = f'{name}_{i+1:03d}'
                content.append( (name, text) )
        else:
            for fc, file in enumerate(textfile):
                pre_split = utils.parse_file(file, separator, tokenize, language.english_name)
                loc_content = utils.split_lines(pre_split, max_lines, max_chars)
                for i, text in enumerate(loc_content):
                    if naming == FILENAMES:
                        name = pathlib.PurePath(file.name).stem.replace('__', '_')
                    if naming == NUMBERING:
                        name = f'{title}_{fc+1:02d}'
                    if len(loc_content) > 1:
                        name = f'{name}_{i+1:03d}'
                    content.append( (name, text) )
        
        sf: models.SharedFolder = parent.make_shared_folder()
        # Create multiple texts if necessary
        for name, section in content:
            new_name = name
            count = 2
            while models.Text.objects.filter(shared_folder=sf, title=new_name).exists():
                new_name = f'{name}_{count:02d}'
                count += 1
            models.Text.objects.create(
                shared_folder = sf,
                #textfile = base_files.ContentFile('\n\n'.join(section)),
                textfile = utils.make_file(section, name),
                title = new_name,
                language = language,
            )
