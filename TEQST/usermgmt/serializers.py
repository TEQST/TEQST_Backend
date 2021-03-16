from rest_framework import serializers
from . import utils, models
import datetime

class LanguageSerializer(serializers.ModelSerializer):
    '''
    Is used to serialize a language, mostly used as nested serializer and to get a list of supported languages
    '''

    class Meta():
        model = models.Language
        fields = ['english_name', 'native_name', 'short', 'right_to_left', 'is_menu_language']
        read_only_fields = fields


class UserFullSerializer(serializers.ModelSerializer):
    '''
    Is used to recieve and update the properties of the user currently logged in
    '''

    #'languages' uses nested objects and is used for retrieving the languages. 
    #'language_ids' is used for modifying the same attribute and works only with abbreviations's
    languages = LanguageSerializer(many = True, read_only = True)
    language_ids = serializers.PrimaryKeyRelatedField(queryset=models.Language.objects.all(), many=True, source='languages', write_only=True)
    
    #'menu_language' and 'menu_language_id' work the same as 'languages' and 'language_ids' but with a single object
    menu_language = LanguageSerializer(read_only=True)
    menu_language_id = serializers.PrimaryKeyRelatedField(queryset=models.Language.objects.all(), source='menu_language', write_only=True, required=False)

    #'is_publisher' calculates it's value by executing the 'is_publisher' method in the CustomUser model
    is_publisher = serializers.BooleanField(read_only=True)
    #same as is_publisher
    is_listener = serializers.BooleanField(read_only=True)

    class Meta():
        model = models.CustomUser
        fields = ['id', 'username', 'email', 'education', 'gender', 'birth_year', 'languages', 'language_ids', 'menu_language', 'menu_language_id', 'accent', 'country', 'dark_mode', 'is_publisher', 'is_listener']
        read_only_fields = ['id', 'username', 'is_publisher', 'is_listener']

    #checks if the given birth_year is in a certain "valid" range, is called automatically by the drf
    def validate_birth_year(self, value):
        if value < 1900 or value > datetime.date.today().year:
            raise serializers.ValidationError("Invalid birth_year.")
        return value

    #checks if the given menu_language_id belongs to a menu language
    def validate_menu_language_id(self, value):
        if not value.is_menu_language():
            raise serializers.ValidationError("Invalid menu language.")
        return value
    
    def validate(self, data):
        # this is so that the default will be set and we dont have some users accents be '' and some users accents 'Not specified'
        if 'accent' in data.keys():
            if data['accent'] == '':
                data['accent'] = utils.ACCENT_DEFAULT
        return data
        

class UserBasicSerializer(serializers.ModelSerializer):
    '''
    Is used to retrieve a list of all users
    '''
    class Meta():
        model = models.CustomUser
        depth = 1
        fields = ['id', 'username', 'email', 'education', 'gender', 'birth_year', 'languages', 'accent', 'country']
        read_only_fields = fields


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Used for user ceration. Maybe this serializer can be integrated in another serializer later on.
    Other fields should probably be added.
    """

    #'languages' uses nested objects and is used for retrieving the languages. 
    #'language_ids' is used for modifying the same attribute and works only with id's
    languages = LanguageSerializer(many = True, read_only = True)
    language_ids = serializers.PrimaryKeyRelatedField(queryset=models.Language.objects.all(), many=True, source='languages', write_only=True)
    
    #'menu_language' and 'menu_language_id' work the same as 'languages' and 'language_ids' but with a single object
    menu_language = LanguageSerializer(read_only=True)
    menu_language_id = serializers.PrimaryKeyRelatedField(queryset=models.Language.objects.all(), source='menu_language', write_only=True, required=False)

    class Meta:
        model = models.CustomUser
        fields = ['username', 'password', 'email', 'education', 'gender', 'birth_year', 'language_ids', 'languages', 'menu_language', 'menu_language_id', 'accent', 'country']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}
    
    def create(self, validated_data):
        language_ids = validated_data.pop('languages')
        user = models.CustomUser.objects.create_user(**validated_data)
        user.languages.set(language_ids)
        user.save()
        return user

    #checks if the given birth_year is in a certain "valid" range, is called automatically by the drf
    def validate_birth_year(self, value):
        if value < 1900 or value > datetime.date.today().year:
            raise serializers.ValidationError("Invalid birth_year.")
        return value
    
    #checks if the given menu_language_id belongs to a menu language
    def validate_menu_language_id(self, value):
        if not value.is_menu_language():
            raise serializers.ValidationError("Invalid menu language.")
        return value

    def validate_username(self, value):
        if value == 'locale':
            raise serializers.ValidationError("Username not allowed.")
        return value
    
    def validate(self, data):
        # this is so that the default will be set and we dont have some users accents be '' and some users accents 'Not specified'
        if 'accent' in data.keys():
            if data['accent'] == '':
                data['accent'] = utils.ACCENT_DEFAULT
        return data