from django.shortcuts import render
from .serializers import UserFullSerializer, UserBasicSerializer, LanguageSerializer, UserRegisterSerializer
from .models import CustomUser, Language
from .permissions import IsPublisher
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, mixins
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status

from django.http import HttpResponse


class UserListView(generics.ListAPIView):
    '''
    Is used to get a list of users, publishers should use this to assign speakers to their texts(sharedFolders)
    '''
    queryset = CustomUser.objects.all()
    serializer_class = UserBasicSerializer
    permission_classes = [IsAuthenticated, IsPublisher]

    def get_queryset(self):
        if 'query' in self.request.query_params:
            name_pre = self.request.query_params['query']
            return CustomUser.objects.filter(username__startswith=name_pre)
        else:
            return CustomUser.objects.all()


class UserDetailedView(generics.RetrieveUpdateDestroyAPIView):
    '''
    Is used by all users to retrieve and update their data
    '''
    serializer_class = UserFullSerializer

    def get_object(self):
        return self.request.user

class LanguageView(generics.ListAPIView):
    '''
    Is used to retrieve a list of all languages
    This view has no permission requirements because this information is relevant when registering a new user
    '''
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = []

class MenuLanguageView(generics.RetrieveAPIView):

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    
    def get_object(self):
        return self.request.user.menu_language

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        f = instance.localization_file.open("rb") 
        response = HttpResponse()
        response.write(f.read())
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment; filename="' + instance.localization_file.name + '"'
        return response

    

class UserRegisterView(generics.CreateAPIView):
    '''
    Is used to register a new user to the system
    Obviously no permission requirements
    '''
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = []


class GetAuthToken(ObtainAuthToken):
    """
    This is the view used to log in a user (get his Authentication Token)
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        response = super(GetAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        user = CustomUser.objects.get(id=token.user_id)
        user_serializer = UserFullSerializer(user, many=False)
        return Response({'token': token.key, 'user': user_serializer.data})


class LogoutView(APIView):
    '''
    Is used to log out a user (make his Authentication Token invalid)
    '''
    def post(self, request, *args, **kwargs):
        token = request.auth 
        token.delete()
        return Response('Logout successful!', status=status.HTTP_200_OK)