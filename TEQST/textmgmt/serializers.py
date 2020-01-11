from rest_framework import serializers
from .models import Folder, SharedFolder, Text


class FolderFullSerializer(serializers.ModelSerializer):
    """
    to be used by view: FolderListView
    for: Folder creation, subfolder list retrieval
    """
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


class SharedFolderSerializer(serializers.ModelSerializer):
    # TODO add read only field of path (callable)
    """
    to be used by view: SharedFolderListView, FolderDetailedView
    for: SharedFolder list retrieval in speaker view, edit (e.g. speaker set) by publisher
    """
    class Meta:
        model = SharedFolder
        fields = ['id', 'name', 'owner', 'parent', 'speaker']


class TextFullSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextDetailedView, TextListView
    for: opening a text, creation of a text
    """
    content = serializers.CharField(source='get_content', read_only=True)
    class Meta:
        model = Text
        # TODO maybe make the textfile write only
        fields = ['id', 'title', 'shared_folder', 'sentences_count', 'content', 'textfile']
        read_only_fields = ['sentences_count', 'sentences']


class TextBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextListView, TextDetailedView
    for: retrieving a list of texts, updating the title of a text
    """
    class Meta:
        model = Text
        # TODO adjust fields
        fields = ['id', 'title']
        