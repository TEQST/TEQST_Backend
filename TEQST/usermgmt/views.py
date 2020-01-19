from django.shortcuts import render
from .serializers import UserFullSerializer, UserBasicSerializer, LanguageSerializer, UserRegisterSerializer
from .models import CustomUser, Language
from rest_framework import generics, mixins
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

# Create your views here.
class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserBasicSerializer

class UserDetailedView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserFullSerializer

    def get_object(self):
        return self.request.user

class LanguageView(generics.ListAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = []


class GetAuthToken(ObtainAuthToken):
    """
    This is the view used to get the Authentication Token
    """
    permission_classes = []
    #authentication_classes = []

    def post(self, request, *args, **kwargs):
        response = super(GetAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        user = CustomUser.objects.get(id=token.user_id)
        user_serializer = UserBasicSerializer(user, many=False)
        return Response({'token': token.key, 'user': user_serializer.data})
