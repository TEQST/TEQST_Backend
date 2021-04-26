from django import forms
from django.contrib.auth import forms as auth_forms
from . import models

class CustomUserCreationForm(auth_forms.UserCreationForm):

    class Meta(auth_forms.UserCreationForm.Meta):
        model = models.CustomUser
        fields = ("username", "birth_year", "country", "accent")

class CustomUserChangeForm(auth_forms.UserChangeForm):

    class Meta(auth_forms.UserChangeForm.Meta):
        model = models.CustomUser
        fields = '__all__'