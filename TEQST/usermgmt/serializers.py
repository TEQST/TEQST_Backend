from rest_framework import serializers
from .models import CustomUser

class UserFullSerializer(serializers.ModelSerializer):

    class Meta():
        model = CustomUser
        fields = ['id', 'username', 'education', 'gender', 'date_of_birth', 'language']
        read_only_fields = ['id', 'username']

class UserBasicSerializer(serializers.ModelSerializer):

    class Meta():
        model = CustomUser
        fields = ['username', 'education', 'gender', 'date_of_birth', 'language']
        read_only_fields = ['username', 'education', 'gender', 'date_of_birth', 'language']


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Used for user ceration. Maybe this serializer can be integrated in another serializer later on.
    Other fields should probably be added.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}