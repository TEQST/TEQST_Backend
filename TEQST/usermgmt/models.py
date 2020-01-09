from django.db import models

class Profile(models.Model):
    gender = models.CharField(max_length=20)

class Tag(models.Model):
    pass

class Language(models.Model):
    pass
