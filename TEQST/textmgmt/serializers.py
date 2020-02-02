from rest_framework import serializers
from .models import Folder, SharedFolder, Text
from usermgmt.models import CustomUser
from usermgmt.serializers import UserBasicSerializer

################################
# important todos:
# - add folder name change functionality
################################


class FolderPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        # TODO sharedfolders should not be allowed to be parent folders for other folders
        user = self.context['request'].user
        queryset = Folder.objects.filter(owner=user, sharedfolder=None)
        return queryset


class FolderFullSerializer(serializers.ModelSerializer):
    """
    to be used by view: FolderListView
    for: Folder creation, top-level-folder list retrieval
    """
    parent = FolderPKField(allow_null=True)
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    # is_sharedfolder in the sense that there exists a Sharedfolder object 
    # with the same pk as this Folder 
    class Meta:
        model = Folder
        fields = ['id', 'name', 'owner', 'parent', 'is_sharedfolder']
        read_only_fields = ['owner', 'is_sharedfolder']
    
    def validate_name(self, value):
        if '__' in value:
            raise serializers.ValidationError('The folder name contains invalid characters \"__\"')
        return value

    def validate(self, data):
        if Folder.objects.filter(owner=self.context['request'].user, name=data['name'], parent=data['parent']).exists():
            raise serializers.ValidationError('A folder with the given name in the given place already exists')
        return super().validate(data)

class FolderBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: FolderDetailedView
    for: Folder update and nested serializers in retrieve
    """
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    # is_sharedfolder in the sense that there exists a Sharedfolder object 
    # with the same pk as this Folder
    class Meta:
        model = Folder
        fields = ['id', 'name', 'is_sharedfolder']
        read_only_fields = ['name', 'is_sharedfolder']  # remove 'name' for folder name change

class FolderDetailedSerializer(serializers.ModelSerializer):
    """
    to be used by view: FolderDetailView
    for: Folder retrieval
    """
    parent = FolderPKField(allow_null=True)
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    subfolder = FolderBasicSerializer(many = True, read_only=True)
    # is_sharedfolder in the sense that there exists a Sharedfolder object 
    # with the same pk as this Folder 
    class Meta:
        model = Folder
        fields = ['id', 'name', 'owner', 'parent', 'subfolder', 'is_sharedfolder']
        #read_only_fields = ['owner', 'subfolder', 'is_sharedfolder']
        #should not be necessary
        read_only_fields = fields


class TextBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextListView, TextDetailedView
    for: retrieving a list of texts, updating the title of a text
    """
    class Meta:
        model = Text
        # TODO adjust fields
        fields = ['id', 'title']


class SharedFolderContentSerializer(serializers.ModelSerializer):
    # TODO add read only field of path (callable)
    """
    to be used by view: SharedFolderListView
    for: SharedFolder list retrieval in speaker view
    """
    texts = TextBasicSerializer(read_only=True, many=True, source='text')
    path = serializers.CharField(read_only=True, source='get_readable_path')
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'owner', 'path', 'texts']
        read_only_fields = ['name', 'owner', 'path', 'texts']  # is path neede in read_only_fields?


class SharedFolderDetailSerializer(serializers.ModelSerializer):
    """
    to be used by view: 
    for: sharedfolder speaker retrieval and update
    """
    speaker_ids = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, allow_null=True, source='speaker', write_only=True)
    speakers = UserBasicSerializer(many=True, read_only=True, source='speaker')
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'speakers', 'speaker_ids']
        read_only_fields = ['name', 'speakers']
        write_only_fields = ['speaker_ids']
        depth = 1


class SharedFolderPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = Folder.objects.filter(owner=user, subfolder=None)
        return queryset


class TextFullSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextDetailedView, TextListView
    for: opening a text, creation of a text
    """
    content = serializers.ListField(source='get_content', child=serializers.CharField(), read_only=True)
    shared_folder = SharedFolderPKField()
    class Meta:
        model = Text
        # TODO maybe make the textfile write only
        fields = ['id', 'title', 'shared_folder', 'content', 'textfile']
        read_only_fields = ['content']
        extra_kwargs = {'textfile': {'write_only': True}}

    def validate(self, data):
        if Text.objects.filter(shared_folder=data['shared_folder'], title=data['title']).exists():
            raise serializers.ValidationError("A text with the given title in the given folder already exists")
        return super().validate(data)


class PublisherSerializer(serializers.ModelSerializer):
    """
    to be used by view: PublisherListView
    for: retrieval of list of publishers, who own sharedfolders shared with request.user
    """
    freedfolders = serializers.SerializerMethodField(read_only=True, method_name='get_freed_folders')

    class Meta:
        model = CustomUser
        # remove id for production
        fields = ['id', 'username', 'freedfolders']
        read_only_fields = ['username']
    
    def get_freed_folders(self, obj):
        pub = obj
        spk = self.context['request'].user
        info = []
        for sf in SharedFolder.objects.filter(owner=pub, speaker=spk):
            info.append({"id": sf.pk, "name": sf.name, "path": sf.get_readable_path()})
        return info



        