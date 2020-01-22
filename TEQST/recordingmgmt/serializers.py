from rest_framework import serializers
from .models import TextRecording, SenctenceRecording
from textmgmt.models import Text


class TextPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = Text.objects.filter(shared_folder__sharedfolder__speaker__id=user.id)


class TextRecordingSerializer(serializers.Serializer):

    active_sentence = serializers.IntegerField(read_only=True)
    text = TextPKField()

    class Meta:
        model = TextRecording
        fields = ['id', 'speaker', 'text', 'active_sentence']
        read_only_fields = ['active_sentence']