from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    date_of_birth = models.DateField(null=True)

class Tag(models.Model):
    pass

class Language(models.Model):
    pass
