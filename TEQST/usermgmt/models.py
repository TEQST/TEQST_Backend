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
    education = models.CharField(max_length=50, blank=True, null=True)
    language = models.ManyToManyField(Language, blank=True)

    #Below is not core funcionality
    tag_usage = models.ManyToManyField(Tag, through='Usage', related_name='Publisher', blank=True)
    tag_coloring = models.ManyToManyField(Tag, through='Customization', related_name='Einsprecher', blank=True)


class Usage(models.Model):
    #TODO maybe limit_choices_to publisher if it works properly
    publisher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    meaning = models.CharField(max_length=200)

class Customization(models.Model):
    einsprecher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    custom_color = models.CharField(max_length=10)

