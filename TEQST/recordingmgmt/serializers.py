from rest_framework import serializers
from django.db.models import Q
from django.utils import timezone
from rest_framework.fields import IntegerField
from . import models
from textmgmt import models as text_models, permissions as text_permissions
import wave


#TODO maybe collapse this to PrimaryKeyRelatedField(queryset=Text.objects.all())
class TextPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = text_models.Text.objects.all().distinct()
        return queryset


class TextRecordingSerializer(serializers.ModelSerializer):
    """
    to be used by view: TextRecordingView
    for: retrieval and creation of textrecordings
    """

    active_sentence = serializers.IntegerField(read_only=True)
    text = TextPKField()
    sentences_status = serializers.SerializerMethodField()

    class Meta:
        model = models.TextRecording
        fields = ['id', 'speaker', 'text', 'TTS_permission', 'SR_permission', 'active_sentence', 'sentences_status', 'rec_time_without_rep', 'rec_time_with_rep']
        read_only_fields = ['speaker', 'rec_time_without_rep', 'rec_time_with_rep']

    def validate(self, data):
        if data['TTS_permission'] is False and data['SR_permission'] is False:
            raise serializers.ValidationError("Either TTS or SR permission must be True")
        return super().validate(data)

    def validate_text(self, value):
        user = self.context['request'].user

        if value.textrecording.filter(speaker=user).exists():
            raise serializers.ValidationError("You already created a recording for this text")

        if not value.is_speaker(user):
            ser = text_permissions.RootParamSerializer(data=self.context['request'].data)
            if not ser.is_valid(raise_exception=False):
                raise serializers.ValidationError("You do not have access to the text you are trying to work on")
            if not value.is_below_root(ser.validated_data['root']):
                raise serializers.ValidationError("You do not have access to the text you are trying to work on")
                
        return value
    
    def get_sentences_status(self, obj):
        tr = obj
        status = []
        for sr in tr.srecs.all():
            status.append({"index": sr.index(), "status": sr.valid})
        return status


class RecordingPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = models.TextRecording.objects.filter(speaker__id=user.id)
        return queryset


class SentenceRecordingSerializer(serializers.ModelSerializer):
    """
    to be used by view: SentenceRecordingCreateView
    for: Sentencerecording creation
    """

    recording = RecordingPKField()

    #When serializing a model, this field accesses the SentenceRecording index method
    index = IntegerField()

    def validate(self, data):
        try:
            index = data.pop('index')
            text_recording = data['recording']
            if index > text_recording.active_sentence():
                raise serializers.ValidationError("Index too high. You need to record the sentences in order.")
            if text_recording.is_finished():
                raise serializers.ValidationError("Text already finished. You can't add more Sentencerecordings.")
            sentence = text_recording.text.sentences.get(index=index)
            if models.SentenceRecording.objects.filter(sentence=sentence, recording=text_recording).exists():
                raise serializers.ValidationError("A recording for the given senctence in the given text already exists")
        except KeyError:
            raise serializers.ValidationError("No index provided")
        # type(data['audiofile']) is InMemoryUploadedFile
        data['sentence'] = sentence
        return super().validate(data)

    def validate_index(self, value):
        if value < 1:
            raise serializers.ValidationError("Invalid index.")
        return value

    # def check_audio_duration(self, duration: float, sentence: str):
    #     if duration > len(sentence) / 2.5:
    #         raise serializers.ValidationError("Recording is too long")
    #     elif duration < len(sentence) / 40:
    #         raise serializers.ValidationError("Recording is too short")


    def create(self, validated_data):
        validated_data['legacy'] = False
        return super().create(validated_data)


    class Meta:
        model = models.SentenceRecording
        fields = ['recording', 'audiofile', 'index', 'valid']
        read_only_fields = ['valid']
        extra_kwargs = {'audiofile': {'write_only': True}}


class SentenceRecordingUpdateSerializer(serializers.ModelSerializer):
    """
    to be used by view: SentenceRecordingUpdateView
    for: SentenceRecording update
    """

    recording = RecordingPKField(read_only=True)

    #When serializing a model, this field accesses the SentenceRecording index method
    index = IntegerField(read_only=True)

    class Meta:
        model = models.SentenceRecording
        fields = ['recording', 'audiofile', 'index', 'valid']
        read_only_fields = ['recording', 'index', 'valid']
        extra_kwargs = {'audiofile': {'write_only': True}}

    def validate_audiofile(self, value):
        print(type(value))
        #TODO check for file differences, otherwise reject (repeat request, consider proper idempotency)
        return value

    # def check_audio_duration(self, duration: float, sentence: str):
    #     if duration > len(sentence) / 2.5:
    #         raise serializers.ValidationError("Recording is too long")
    #     elif duration < len(sentence) / 40:
    #         raise serializers.ValidationError("Recording is too short")

    def update(self, instance: models.SentenceRecording, validated_data):
        
        # Backup the previous recording, then update it's fields
        backup = models.SentenceRecordingBackup(
            recording = instance,
            length = instance.length,
            last_updated = instance.last_updated,
            valid = instance.valid,
        )
        backup.save()
        backup.audiofile.save('unused', instance.audiofile)

        # TODO uncomment this and get the index (XXXX) if it is clear which view is used for this
        #sentence = textrecording.text.get_content()[XXXX - 1]
        #self.check_audio_duration(duration, sentence)

        validated_data['last_updated'] = timezone.now()
        validated_data['legacy'] = False

        instance.audiofile.delete(save=False)

        obj = super().update(instance, validated_data)

        return obj
