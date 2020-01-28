from rest_framework import serializers
from .models import Folder, SharedFolder, Text
from usermgmt.models import CustomUser

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
    for: Folder creation, subfolder list retrieval
    """
    parent = FolderPKField(allow_null=True)
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    # is_sharedfolder in the sense that there exists a Sharedfolder object 
    # with the same pk as this Folder 
    class Meta:
        model = Folder
        fields = ['id', 'name', 'owner', 'parent', 'subfolder', 'is_sharedfolder']
        read_only_fields = ['owner', 'subfolder', 'is_sharedfolder']
    
    def validate(self, data):
        if Folder.objects.filter(owner=self.context['request'].user, name=data['name'], parent=data['parent']).exists():
            raise serializers.ValidationError('A folder with the given name in the given place already exists')
        return super().validate(data)



class FolderBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: FolderDetailedView
    for: Folder update
    """
    class Meta:
        model = Folder
        fields = ['id', 'name']
        read_only_fields = ['name']  # remove 'name' for folder name change


class SharedFolderListSerializer(serializers.ModelSerializer):
    # TODO add read only field of path (callable)
    """
    to be used by view: SharedFolderListView
    for: SharedFolder list retrieval in speaker view
    """
    path = serializers.CharField(read_only=True, source='get_readable_path')
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'owner', 'path']
        read_only_fields = ['name', 'owner', 'path']  # is path neede in read_only_fields?


class SharedFolderDetailSerializer(serializers.ModelSerializer):
    """
    to be used by view: 
    for: sharedfolder speaker retrieval and update
    """
    speaker = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, allow_null=True)
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'speaker']
        read_only_fields = ['name']
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

    def validate(self, data):
        if Text.objects.filter(shared_folder=data['shared_folder'], title=data['title']).exists():
            raise serializers.ValidationError("A text with the given title in the given folder already exists")
        return super().validate(data)


class TextBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextListView, TextDetailedView
    for: retrieving a list of texts, updating the title of a text
    """
    class Meta:
        model = Text
        # TODO adjust fields
        fields = ['id', 'title']
        