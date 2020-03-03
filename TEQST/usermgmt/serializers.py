from rest_framework import serializers
from .models import CustomUser, Language

from datetime import date

class LanguageSerializer(serializers.ModelSerializer):
    '''
    Is used to serialize a language, mostly used as nested serializer and to get a list of supported languages
    '''

    class Meta():
        model = Language
        fields = ['english_name', 'native_name', 'short', 'right_to_left', 'is_menu_language']
        read_only_fields = fields


class UserFullSerializer(serializers.ModelSerializer):
    '''
    Is used to recieve and update the properties of the user currently logged in
    '''

    #'languages' uses nested objects and is used for retrieving the languages. 
    #'language_ids' is used for modifying the same attribute and works only with id's
    languages = LanguageSerializer(many = True, read_only = True)
    language_ids = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, source='languages', write_only=True)
    
    #'menu_language' and 'menu_language_id' work the same as 'languages' and 'language_ids' but with a single object
    menu_language = LanguageSerializer(read_only=True)
    menu_language_id = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), source='menu_language', write_only=True, required=False)

    #'is_publisher' calculates it's value by executing the 'is_publisher' method in the CustomUser model
    is_publisher = serializers.BooleanField(read_only=True)

    class Meta():
        model = CustomUser
        fields = ['id', 'username', 'education', 'gender', 'birth_year', 'languages', 'language_ids', 'menu_language', 'menu_language_id', 'country', 'is_publisher']
        read_only_fields = ['id', 'username', 'is_publisher']

    #checks if the given birth_year is in a certain "valid" range, is called automatically by the drf
    def validate_birth_year(self, value):
        if value < 1900 or value > date.today().year:
            raise serializers.ValidationError("Invalid birth_year.")
        return value
        

class UserBasicSerializer(serializers.ModelSerializer):
    '''
    Is used to retrieve a list of all users
    '''
    class Meta():
        model = CustomUser
        depth = 1
        fields = ['id', 'username', 'education', 'gender', 'birth_year', 'languages', 'country']
        read_only_fields = fields


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Used for user ceration. Maybe this serializer can be integrated in another serializer later on.
    Other fields should probably be added.
    """

    #'languages' uses nested objects and is used for retrieving the languages. 
    #'language_ids' is used for modifying the same attribute and works only with id's
    languages = LanguageSerializer(many = True, read_only = True)
    language_ids = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, source='languages', write_only=True)
    
    #'menu_language' and 'menu_language_id' work the same as 'languages' and 'language_ids' but with a single object
    menu_language = LanguageSerializer(read_only=True)
    menu_language_id = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), source='menu_language', write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'education', 'gender', 'birth_year', 'language_ids', 'languages', 'menu_language', 'menu_language_id', 'country']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}
    
    def create(self, validated_data):
        language_ids = validated_data.pop('languages')
        user = CustomUser.objects.create_user(**validated_data)
        user.languages.set(language_ids)
        user.save()
        return user

    #checks if the given birth_year is in a certain "valid" range, is called automatically by the drf
    def validate_birth_year(self, value):
        if value < 1900 or value > date.today().year:
            raise serializers.ValidationError("Invalid birth_year.")
        return value
