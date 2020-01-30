from rest_framework import serializers
from .models import CustomUser, Language

from datetime import date

class LanguageSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only = False)

    class Meta():
        model = Language
        fields = ['id', 'english_name', 'native_name', 'short']
        read_only_fields = ['english_name', 'native_name', 'short']

class UserFullSerializer(serializers.ModelSerializer):

#    def __init__(self, *args, **kwargs):
#        super().__init__(*args, **kwargs)
#        try:
#            if self.context['request'].method in ['PUT']:
#                self.fields['languages'] = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True)
#            else:
#                self.fields['languages'] = LanguageSerializer(many = True, read_only = False)
#        except KeyError:
#            self.fields['languages'] = LanguageSerializer(many = True, read_only = False)
#        
    #languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True)
    languages = LanguageSerializer(many = True, read_only = True)
    language_ids = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, source='languages', write_only=True)
    
    menu_language = LanguageSerializer(read_only=True)
    menu_language_id = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), source='menu_language', write_only=True)

    is_publisher = serializers.BooleanField(read_only=True)  # source kwarg not needed, because name is same

    class Meta():
        model = CustomUser
        fields = ['id', 'username', 'education', 'gender', 'birth_year', 'languages', 'language_ids', 'menu_language', 'menu_language_id', 'country', 'is_publisher']
        read_only_fields = ['id', 'username', 'is_publisher']

    # def update(self, instance, validated_data):
    #     languages_data = validated_data.pop('languages')
    #     instance = super().update(instance, validated_data)
    #     instance.languages.clear()
    #     for language_data in languages_data:
    #         language = Language.objects.get(**language_data)
    #         instance.languages.add(language)
    #     return instance

    def validate_birth_year(self, value):
        if value < 1900 or value > date.today().year:
            raise serializers.ValidationError("Invalid birth_year.")
        return value
        

class UserBasicSerializer(serializers.ModelSerializer):

    class Meta():
        model = CustomUser
        depth = 1
        fields = ['id', 'username', 'education', 'gender', 'birth_year', 'languages', 'country']
        read_only_fields = fields


class PublisherSerializer(serializers.ModelSerializer):
    """
    to be used by view: PublisherListView
    for: retrieval of list of publishers, who own sharedfolders shared with request.user
    """
    class Meta:
        model = CustomUser
        # remove id for production
        fields = ['id', 'username']


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Used for user ceration. Maybe this serializer can be integrated in another serializer later on.
    Other fields should probably be added.
    """

    languages = LanguageSerializer(many = True, read_only = True)
    language_ids = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, source='languages', write_only=True)

    class Meta:
        model = CustomUser
        # languages still need to be added
        fields = ['username', 'password', 'education', 'gender', 'birth_year', 'language_ids', 'languages', 'menu_language', 'country']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}
    
    def create(self, validated_data):
        language_ids = validated_data.pop('languages')
        user = CustomUser.objects.create_user(**validated_data)
        user.languages.set(language_ids)
        user.save()
        return user
    
    def validate_birth_year(self, value):
        if value < 1900 or value > date.today().year:
            raise serializers.ValidationError("Invalid birth_year.")
        return value
