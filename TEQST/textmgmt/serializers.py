from rest_framework import serializers
from .models import Folder, SharedFolder, Text


class FolderSerializer(serializers.ModelSerializer):
    """
    to be used by view: FolderListView
    for: Folder creation, subfolder list retrieval
    """
    class Meta:
        model = Folder
        fields = ['id', 'name', 'owner', 'parent']
        read_only_fields = ['subfolder']


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
    to be used by view: TextDetailedView
    for: opening a text, creation of a text
    """
    class Meta:
        model = Text
        # TODO adjust fields
        fields = ['id', 'title', 'shared_folder', 'textfile']
        read_only_fields = ['sentences_count', 'sentences']


class TextBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextListView
    for: retrieving a list of texts
    """
    class Meta:
        model = Text
        # TODO adjust fields
        fields = ['id', 'title']
        