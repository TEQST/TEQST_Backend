from django.shortcuts import render
from .serializers import UserFullSerializer, UserBasicSerializer
from .models import CustomUser
from rest_framework import generics, mixins

# Create your views here.
class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserBasicSerializer

class UserDetailedView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserFullSerializer