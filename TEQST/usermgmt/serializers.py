from rest_framework import serializers
from .models import CustomUser, Language

class LanguageSerializer(serializers.ModelSerializer):

    class Meta():
        model = Language
        fields = ['id', 'english_name', 'native_name', 'short']
        read_only_fields = fields

class UserFullSerializer(serializers.ModelSerializer):

    languages = LanguageSerializer(many = True, read_only = False)

    class Meta():
        model = CustomUser
        fields = ['id', 'username', 'education', 'gender', 'date_of_birth', 'languages']
        read_only_fields = ['id', 'username']

    def update(self, instance, validated_data):
        language_data = validated_data.pop('languages')
        instance = super().update(instance, validated_data)
        #instance.languages.clear()
        #for language_data_item in language_data:
        #    language = Language.objects.get(id = language_data_item['id'])
        #    instance.languages.add(language)
        return instance
        

class UserBasicSerializer(serializers.ModelSerializer):

    class Meta():
        model = CustomUser
        depth = 1
        fields = ['id', 'username', 'education', 'gender', 'date_of_birth', 'languages']
        read_only_fields = ['id', 'username', 'education', 'gender', 'date_of_birth', 'languages']


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Used for user ceration. Maybe this serializer can be integrated in another serializer later on.
    Other fields should probably be added.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        user.save()
        return user
