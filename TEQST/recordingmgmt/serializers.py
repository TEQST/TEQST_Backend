from django.core.files.storage import default_storage
from rest_framework import serializers
from django.db.models import Q
from . import models
from textmgmt import models as text_models
import wave


class TextPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = text_models.Text.objects.filter(Q(shared_folder__speaker__id=user.id) | Q(shared_folder__public=True)).distinct()
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
        read_only_fields = ['speaker', 'active_sentence', 'rec_time_without_rep', 'rec_time_with_rep']

    def validate(self, data):
        if models.TextRecording.objects.filter(speaker=self.context['request'].user, text=data['text']).exists():
            raise serializers.ValidationError("A recording for the given text by the given user already exists")
        if data['TTS_permission'] is False and data['SR_permission'] is False:
            raise serializers.ValidationError("Either TTS or SR permission must be True")
        return super().validate(data)
    
    def get_sentences_status(self, obj):
        tr = obj
        status = []
        for sr in tr.sentencerecording_set.all():
            status.append({"index": sr.index, "status": sr.valid})
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

    def validate(self, data):
        try:
            data['index']
        except KeyError:
            raise serializers.ValidationError("No index provided")
        if models.SentenceRecording.objects.filter(index=data['index'], recording=data['recording']).exists():
            raise serializers.ValidationError("A recording for the given senctence in the given text already exists")
        text_recording = models.TextRecording.objects.get(pk=data['recording'].pk)
        if data['index'] > text_recording.active_sentence():
            raise serializers.ValidationError("Index too high. You need to record the sentences in order.")
        if text_recording.is_finished():
            raise serializers.ValidationError("Text already finished. You can't add more Sentencerecordings.")
        # type(data['audiofile']) is InMemoryUploadedFile
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
        # type(validated_data['audiofile']) is InMemoryUploadedFile
        wav_file = validated_data['audiofile'].open('rb')
        wav = wave.open(wav_file, 'rb')
        duration = wav.getnframes() / wav.getframerate()
        wav.close()
        # print('DURATION:', duration)
        textrecording = validated_data['recording']

        # sentence = textrecording.text.get_content()[validated_data['index'] - 1]
        # self.check_audio_duration(duration, sentence)

        obj = super().create(validated_data)

        textrecording.rec_time_without_rep += duration
        textrecording.rec_time_with_rep += duration
        textrecording.save()

        return obj

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

    class Meta:
        model = models.SentenceRecording
        fields = ['recording', 'audiofile', 'index', 'valid']
        read_only_fields = ['recording', 'index', 'valid']
        extra_kwargs = {'audiofile': {'write_only': True}}

    # def check_audio_duration(self, duration: float, sentence: str):
    #     if duration > len(sentence) / 2.5:
    #         raise serializers.ValidationError("Recording is too long")
    #     elif duration < len(sentence) / 40:
    #         raise serializers.ValidationError("Recording is too short")

    def update(self, instance, validated_data):
        wav_file = validated_data['audiofile'].open('rb')
        wav = wave.open(wav_file, 'rb')
        duration = wav.getnframes() / wav.getframerate()
        wav.close()
        # print('DURATION:', duration)
        wav_file_old = instance.audiofile.open('rb')
        wav_old = wave.open(wav_file_old, 'rb')
        duration_old = wav_old.getnframes() / wav_old.getframerate()
        wav_old.close()
        instance.audiofile.close()  # refer to the wave docs: the caller must close the file, this is not done by wave.close()
        # print('DURATION OLD:', duration_old)
        textrecording = instance.recording

        # TODO uncomment this and get the index (XXXX) if it is clear which view is used for this
        #sentence = textrecording.text.get_content()[XXXX - 1]
        #self.check_audio_duration(duration, sentence)

        obj = super().update(instance, validated_data)

        textrecording.rec_time_without_rep += duration
        textrecording.rec_time_without_rep -= duration_old
        textrecording.rec_time_with_rep += duration
        textrecording.save()

        return obj
