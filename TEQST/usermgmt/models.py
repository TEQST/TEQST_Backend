from django.db import models
from django.contrib.auth.models import AbstractUser

class Language(models.Model):
    native_name = models.CharField(max_length=50)
    english_name = models.CharField(max_length=50)
    short = models.CharField(max_length=5)

    def __str__(self):
        return self.english_name + ' (' + self.native_name + ')'

class Tag(models.Model):
    identifier = models.CharField(max_length=10)
    default_color = models.CharField(max_length=10)

    def __str__(self):
        return self.identifier

class CustomUser(AbstractUser):
    date_of_birth = models.DateField(blank=True, null=True)
    language = models.ManyToManyField(Language, blank=True)

