from rest_framework import serializers
from .models import Folder, SharedFolder, Text

################################
# important todos:
# - sharedfolder speaker add/rem
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
    class Meta:
        model = Folder
        fields = ['id', 'name', 'owner', 'parent', 'subfolder']
        read_only_fields = ['owner', 'subfolder']


class FolderBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: FolderDetailedView
    for: Folder update
    """
    class Meta:
        model = Folder
        fields = ['id', 'name']
        read_only_fields = ['name']  # remove 'name' for folder name change


class SharedFolderSerializer(serializers.ModelSerializer):
    # TODO add read only field of path (callable)
    """
    to be used by view: SharedFolderListView, maybe also speaker change by Pub
    for: SharedFolder list retrieval in speaker view, edit (e.g. speaker set) by publisher
    """
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'owner', 'parent', 'speaker']
        read_only_fields = ['name', 'owner', 'parent']


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


class TextBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextListView, TextDetailedView
    for: retrieving a list of texts, updating the title of a text
    """
    class Meta:
        model = Text
        # TODO adjust fields
        fields = ['id', 'title']
        