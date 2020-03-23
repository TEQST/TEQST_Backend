from rest_framework import serializers
from .models import Folder, SharedFolder, Text
from .utils import NAME_ID_SPLITTER
from usermgmt.models import CustomUser
from usermgmt.serializers import UserBasicSerializer
from recordingmgmt.models import TextRecording


class FolderPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = Folder.objects.filter(owner=user, sharedfolder=None)
        return queryset


class FolderFullSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubFolderListView
    for: Folder creation, top-level-folder list retrieval
    """
    parent = FolderPKField(allow_null=True)
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    # is_sharedfolder in the sense that this folder has a corresponding Sharedfolder object with the same pk as this Folder
 
    class Meta:
        model = Folder
        fields = ['id', 'name', 'owner', 'parent', 'is_sharedfolder']
        read_only_fields = ['owner', 'is_sharedfolder']
    
    def validate_name(self, value):
        """
        validates the name field
        """
        if NAME_ID_SPLITTER in value:
            raise serializers.ValidationError('The folder name contains invalid characters "' + NAME_ID_SPLITTER + '"')
        return value

    def validate(self, data):
        """
        validation that has to do with multiple fields of the serializer
        """
        if Folder.objects.filter(owner=self.context['request'].user, name=data['name'], parent=data['parent']).exists():
            raise serializers.ValidationError('A folder with the given name in the given place already exists')
        return super().validate(data)

class FolderBasicSerializer(serializers.ModelSerializer):
    """
    to be used by: FolderDetailedSerializer
    """
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    # is_sharedfolder in the sense that this folder has a corresponding Sharedfolder object with the same pk as this Folder
    
    class Meta:
        model = Folder
        fields = ['id', 'name', 'is_sharedfolder']
        read_only_fields = ['name', 'is_sharedfolder']

class FolderDetailedSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubFolderDetailView
    for: retrieval of a Folder with its subfolders
    """
    parent = FolderPKField(allow_null=True)
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    subfolder = FolderBasicSerializer(many=True, read_only=True)
    # is_sharedfolder in the sense that this folder has a corresponding Sharedfolder object with the same pk as this Folder
    
    class Meta:
        model = Folder
        fields = ['id', 'name', 'owner', 'parent', 'subfolder', 'is_sharedfolder']
        read_only_fields = fields


class SharedFolderPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = Folder.objects.filter(owner=user, subfolder=None)
        return queryset


class TextFullSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubTextListView, PubTextDetailedView, SpkTextDetailedView
    for: creation of a text, retrieval of a text
    """
    content = serializers.ListField(source='get_content', child=serializers.CharField(), read_only=True)
    shared_folder = SharedFolderPKField()

    class Meta:
        model = Text
        fields = ['id', 'title', 'shared_folder', 'content', 'textfile']
        read_only_fields = ['content']
        extra_kwargs = {'textfile': {'write_only': True}}

    def validate(self, data):
        if Text.objects.filter(shared_folder=data['shared_folder'], title=data['title']).exists():
            raise serializers.ValidationError("A text with the given title in the given folder already exists")
        return super().validate(data)
    
    def validate_title(self, value):
        if ' ' in value:
            raise serializers.ValidationError("Text title can't contain an underscore or a space character.")
        return value


class TextBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubTextListView
    for: retrieval of a list of texts contained in a sharedfolder
    """
    class Meta:
        model = Text
        fields = ['id', 'title']


class SharedFolderTextSerializer(serializers.ModelSerializer):
    """
    to be used by view: SpkTextListView
    for: retrieval of a sharedfolder with the texts it contains
    """
    texts = TextBasicSerializer(read_only=True, many=True, source='text')
    path = serializers.CharField(read_only=True, source='get_readable_path')
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'owner', 'path', 'texts']
        read_only_fields = ['name', 'owner']


class SharedFolderSpeakerSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubSharedFolderSpeakerView
    for: retrieval and update of the speakers of a shared folder
    """
    speaker_ids = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, allow_null=True, source='speaker', write_only=True)
    speakers = UserBasicSerializer(many=True, read_only=True, source='speaker')
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'speakers', 'speaker_ids']
        read_only_fields = ['name', 'speakers']
        write_only_fields = ['speaker_ids']
        depth = 1


class SharedFolderStatsSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubSharedFolderStatsView
    for: retrieval of stats about speakers' progress of texts in a sharedfolder
    """
    speakers = serializers.SerializerMethodField(read_only=True, method_name='get_speaker_stats')

    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'speakers']
        read_only_fields = fields
    
    def get_speaker_stats(self, obj):
        """
        example return (multiple speakers are of course possible):
        [
            {
                'name': 'John',
                'texts':[
                    {
                        'title': 't1',
                        'finished': 5,
                        'total': 9
                    },
                    {
                        'title': 't2',
                        'finished': 0,
                        'total': 4
                    }
                ]
            }
        ]
        """
        sf = obj
        stats = []
        for speaker in sf.speaker.all():
            spk = {'name': speaker.username, 'texts': []}
            for text in Text.objects.filter(shared_folder=sf.folder_ptr):
                txt = {'title': text.title, 'finished': 0, 'total': text.sentence_count()}
                if TextRecording.objects.filter(speaker=speaker, text=text).exists():
                    txt['finished'] = TextRecording.objects.get(speaker=speaker, text=text).active_sentence() - 1
                spk['texts'].append(txt)
            stats.append(spk)
        return stats


class PublisherSerializer(serializers.ModelSerializer):
    """
    to be used by view: SpkPublisherListView, SpkPublisherDetailedView
    for: retrieval of single publisher or list of publishers, who own sharedfolders (freedfolders) shared with request.user
    """
    freedfolders = serializers.SerializerMethodField(read_only=True, method_name='get_freed_folders')

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'freedfolders']
        read_only_fields = ['username']
    
    def get_freed_folders(self, obj):
        pub = obj
        spk = self.context['request'].user
        info = []
        for sf in SharedFolder.objects.filter(owner=pub, speaker=spk):
            info.append({"id": sf.pk, "name": sf.name, "path": sf.get_readable_path()})
        return info



        