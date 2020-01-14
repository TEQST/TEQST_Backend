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