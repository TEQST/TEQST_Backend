from rest_framework import serializers
from django.conf import settings
from . import models, utils
from usermgmt import models as user_models, serializers as user_serializers
from recordingmgmt import models as rec_models
import django.core.files.uploadedfile as uploadedfile
import random, string, chardet, io, math


class FolderPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = models.Folder.objects.filter(owner=user, sharedfolder=None)
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
        model = models.Folder
        fields = ['id', 'name', 'owner', 'parent', 'is_sharedfolder']
        read_only_fields = ['owner', 'is_sharedfolder']
    
    def validate_name(self, value):
        """
        validates the name field
        """
        if utils.NAME_ID_SPLITTER in value:
            raise serializers.ValidationError('The folder name contains invalid characters "' + utils.NAME_ID_SPLITTER + '"')
        return value

    def validate(self, data):
        """
        validation that has to do with multiple fields of the serializer
        """
        if models.Folder.objects.filter(owner=self.context['request'].user, name=data['name'], parent=data['parent']).exists():
            raise serializers.ValidationError('A folder with the given name in the given place already exists')
        return super().validate(data)

class FolderBasicSerializer(serializers.ModelSerializer):
    """
    to be used by: FolderDetailedSerializer
    """
    is_sharedfolder = serializers.BooleanField(source='is_shared_folder', read_only=True)
    # is_sharedfolder in the sense that this folder has a corresponding Sharedfolder object with the same pk as this Folder
    
    class Meta:
        model = models.Folder
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
        model = models.Folder
        fields = ['id', 'name', 'owner', 'parent', 'subfolder', 'is_sharedfolder']
        read_only_fields = fields


class SharedFolderPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = models.Folder.objects.filter(owner=user, subfolder=None)
        return queryset


class TextFullSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubTextListView, PubTextDetailedView, SpkTextDetailedView
    for: creation of a text, retrieval of a text
    """
    content = serializers.ListField(source='get_content', child=serializers.CharField(), read_only=True)
    shared_folder = SharedFolderPKField()
    # specify the maximum number of lines in a text. If a text is longer, it will be split up.
    max_lines = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = models.Text
        fields = ['id', 'title', 'language', 'is_right_to_left', 'shared_folder', 'content', 'textfile', 'max_lines']
        read_only_fields = ['is_right_to_left', 'content']
        extra_kwargs = {'textfile': {'write_only': True}}

    def validate(self, data):
        if models.Text.objects.filter(shared_folder=data['shared_folder'], title=data['title']).exists():
            raise serializers.ValidationError("A text with the given title in the given folder already exists")
        return super().validate(data)
    
    def validate_title(self, value):
        if ' ' in value:
            raise serializers.ValidationError("Text title can't contain a space character.")
        return value
    
    def check_max_lines(self, max_lines: int, text_len: int):
        """
        This is very similar to the standard validate_<field_name> methods, but is called from the split_text method.
        The reason for that is that only then is the length of the uploaded text known, which max_lines is checked against.
        """
        if max_lines < 10:
            raise serializers.ValidationError("max_lines cannot be less than 10")
        if max_lines > 300:
            raise serializers.ValidationError("max_lines cannot be greater than 300")
        if text_len / max_lines > 100:
            raise serializers.ValidationError("Splitting a file into more than 100 partfiles is not permitted. Choose max_lines accordingly.")

    
    def split_text(self, textfile: uploadedfile.InMemoryUploadedFile, max_lines):
        """
        Splits the textfile into smaller files with at most max_lines sentences. 
        A list of SimpleUploadedFile objects is returned.
        """
        filename = textfile.name
        textfiles = []
        # get encoding
        textfile.open(mode='rb')
        encoding = chardet.detect(textfile.read())['encoding']

        # put all sentences in a list
        filecontent = []  # list of all sentences in the textfile
        sentence = ''  # one sentence in the textfile that is resetted after every \n\n and added to filecontent
        # the open method simply does seek(0). This needs to be done, because the file was already opened to find the encoding
        textfile.open()
        for line in textfile:
            line = line.decode(encoding=encoding)
            # this will not work if the newline character is just '\r'
            line = line.replace('\r', '')

            if line == '\n':
                if sentence != '':
                    filecontent.append(sentence)
                    sentence = ''
            else:
                sentence += line.replace('\n', '')
        if sentence != '':
            filecontent.append(sentence)
        # end of gathering filecontent
        # validate max_lines
        self.check_max_lines(max_lines, len(filecontent))
        # create SimpleUploadedFiles with max_lines of content from the textfile
        for i in range(math.ceil(len(filecontent) / max_lines)):
            filesentences, filecontent = filecontent[:max_lines], filecontent[max_lines:]
            content = ''
            for sentence in filesentences:
                content += sentence + '\n\n'
            new_filename = f'{filename[:-4]}_{i + 1}{filename[-4:]}'
            textfiles.append(uploadedfile.SimpleUploadedFile(new_filename, content.encode('utf-8-sig')))

        return textfiles
    
    def create(self, validated_data):
        max_lines = validated_data.pop('max_lines', None)
        sf = validated_data['shared_folder']
        sf = sf.make_shared_folder()
        validated_data['shared_folder'] = sf
        if max_lines is None:
            return super().create(validated_data)
        else:  # max_lines is given
            textfile = validated_data['textfile']
            # type(textfile) is django.core.files.uploadedfile.InMemoryUploadedFile
            textfiles = self.split_text(textfile, max_lines)
            return_obj = None
            for i in range(len(textfiles)):
                data = validated_data.copy()
                data['textfile'] = textfiles[i]
                data['title'] = f'{validated_data["title"]}_{i + 1}'
                return_obj = models.Text.objects.create(**data)
            # some object has to be returned, so it has been decided that the last partfile will be returned
            return return_obj

    # if there ever comes an update method, be sure to pop 'max_lines' like it's done in the create method.


class TextBasicSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubTextListView
    for: retrieval of a list of texts contained in a sharedfolder
    """
    class Meta:
        model = models.Text
        fields = ['id', 'title']


class TextProgressSerializer(serializers.ModelSerializer):
    """
    to be used by view: SpkTextListView
    through serializer: SharedFolderTextSerializer
    for: retrieval of texts of a sharedfolder including information on progress of request.user
    """
    words_total = serializers.IntegerField(read_only=True, source='word_count')
    words_finished = serializers.SerializerMethodField()

    class Meta:
        model = models.Text
        fields = ['id', 'title', 'words_total', 'words_finished']
        read_only_fields = fields

    def get_words_finished(self, obj: models.Text):
        text = obj
        user = self.context['request'].user
        sentences_finished = 0
        if rec_models.TextRecording.objects.filter(text=text, speaker=user).exists():
            tr = rec_models.TextRecording.objects.get(text=text, speaker=user)
            sentences_finished = tr.active_sentence() - 1
        return text.word_count(sentences_finished)


class TextStatsSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubTextStatsView
    for: retrieval of stats about speakers' progress of a text
    """
    speakers = serializers.SerializerMethodField(read_only=True, method_name='get_speaker_stats')
    total = serializers.IntegerField(read_only=True, source='sentence_count')

    class Meta:
        model = models.Text
        fields = ['id', 'title', 'total', 'speakers']
        read_only_fields = fields
    
    def get_speaker_stats(self, obj):
        """
        example return (multiple speakers are of course possible):
        [
            {
                'name': 'John',
                'finished': 5,
                'textrecording_id': 32,  # this key is only there if a textrecording exists
                'rec_time_without_rep': 3.072,  # same
                'rec_time_with_rep': 4.532  # same
            },
        ]
        """
        text = obj
        stats = []
        q1 = text.shared_folder.speaker.all()
        q2 = user_models.CustomUser.objects.filter(textrecording__text=text)
        for speaker in q1.union(q2):
            spk = {'name': speaker.username, 'finished': 0}
            if rec_models.TextRecording.objects.filter(speaker=speaker, text=text).exists():
                textrecording = rec_models.TextRecording.objects.get(speaker=speaker, text=text)
                spk['textrecording_id'] = textrecording.pk
                spk['finished'] = textrecording.active_sentence() - 1
                spk['rec_time_without_rep'] = textrecording.rec_time_without_rep
                spk['rec_time_with_rep'] = textrecording.rec_time_with_rep
            stats.append(spk)
        return stats


class SharedFolderTextSerializer(serializers.ModelSerializer):
    """
    to be used by view: SpkTextListView
    for: retrieval of a sharedfolder with the texts it contains
    """
    texts = TextProgressSerializer(read_only=True, many=True, source='text')
    path = serializers.CharField(read_only=True, source='get_readable_path')
    timestats = serializers.SerializerMethodField()
    
    class Meta:
        model = models.SharedFolder
        fields = ['id', 'name', 'owner', 'path', 'timestats', 'texts']
        read_only_fields = ['name', 'owner', 'timestats']
    
    def get_timestats(self, obj):
        user = self.context['request'].user
        sharedfolder = obj
        timestats = {'rec_time_without_rep': 0, 'rec_time_with_rep': 0}
        for text in sharedfolder.text.all():
            if rec_models.TextRecording.objects.filter(text=text, speaker=user).exists():
                textrecording = rec_models.TextRecording.objects.get(text=text, speaker=user)
                timestats['rec_time_without_rep'] += textrecording.rec_time_without_rep
                timestats['rec_time_with_rep'] += textrecording.rec_time_with_rep
        return timestats


class SharedFolderSpeakerSerializer(serializers.ModelSerializer):
    """
    to be used by view: PubSharedFolderSpeakerView
    for: retrieval and update of the speakers of a shared folder
    """
    speaker_ids = serializers.PrimaryKeyRelatedField(queryset=user_models.CustomUser.objects.all(), many=True, allow_null=True, source='speaker', write_only=True)
    speakers = user_serializers.UserBasicSerializer(many=True, read_only=True, source='speaker')
    class Meta:
        model = models.SharedFolder
        fields = ['id', 'name', 'speakers', 'speaker_ids', 'public']
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
        model = models.SharedFolder
        fields = ['id', 'name', 'speakers']
        read_only_fields = fields
    
    def get_speaker_stats(self, obj):
        """
        example return (multiple speakers are of course possible):
        [
            {
                'name': 'John',
                'rec_time_without_rep': 10.452,
                'rec_time_with_rep': 12.001
                'texts':[
                    {
                        'title': 't1',
                        'finished': 5,
                        'total': 9, 
                        'rec_time_without_rep': 10.452,
                        'rec_time_with_rep': 12.001
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
        q1 = sf.speaker.all()
        q2 = user_models.CustomUser.objects.filter(textrecording__text__shared_folder=sf)
        for speaker in q1.union(q2):
            spk = {'name': speaker.username, 'rec_time_without_rep': 0, 'rec_time_with_rep': 0, 'texts': []}
            for text in models.Text.objects.filter(shared_folder=sf.folder_ptr):
                txt = {'title': text.title, 'finished': 0, 'total': text.sentence_count()}
                if rec_models.TextRecording.objects.filter(speaker=speaker, text=text).exists():
                    textrecording = rec_models.TextRecording.objects.get(speaker=speaker, text=text)
                    txt['finished'] = textrecording.active_sentence() - 1
                    txt['rec_time_without_rep'] = textrecording.rec_time_without_rep
                    txt['rec_time_with_rep'] = textrecording.rec_time_with_rep
                    spk['rec_time_without_rep'] += textrecording.rec_time_without_rep
                    spk['rec_time_with_rep'] += textrecording.rec_time_with_rep
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
        model = user_models.CustomUser
        fields = ['id', 'username', 'freedfolders']
        read_only_fields = ['username']
    
    def get_freed_folders(self, obj):
        pub = obj
        spk = self.context['request'].user
        info = []
        for sf in models.SharedFolder.objects.filter(owner=pub, speaker=spk):
            info.append({"id": sf.pk, "name": sf.name, "path": sf.get_readable_path()})
        return info

class PublicFolderSerializer(serializers.ModelSerializer):
    """
    to be used by view: SpkPublicFoldersView
    for: list of public folders
    """

    path = serializers.CharField(read_only=True, source='get_readable_path')

    class Meta:
        model = models.SharedFolder
        fields = ['id', 'name', 'path']
        read_only_fields = ['id', 'name', 'path']



        