from django.db import models
from django.contrib.auth.models import AbstractUser
from .utils import EDU_CHOICES

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
    gender = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    education = models.CharField(max_length=50, blank=True, null=True, choices=EDU_CHOICES)
    languages = models.ManyToManyField(Language, blank=True)

    #Below is not core funcionality
    #TODO maybe move tag_usage to Tag class to allow limit_choices_to publisher
    tag_usage = models.ManyToManyField(Tag, through='Usage', related_name='publisher', blank=True)
    tag_coloring = models.ManyToManyField(Tag, through='Customization', related_name='speaker', blank=True)

    def get_meaning(self, tag, language):
        usage = Usage.objects.get(publisher=self, tag=tag, language=language)
        return usage.meaning

    def get_color(self, tag):
        customization_set = Customization.objects.filter(speaker=self, tag=tag)
        if len(customization_set) == 0:
            return tag.default_color
        return customization_set[0].custom_color

class Usage(models.Model):
    #TODO maybe limit_choices_to publisher if it works properly
    publisher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    meaning = models.CharField(max_length=200)

    def __str__(self):
        return "by " + self.publisher.__str__() + " for " + self.tag.__str__() + " in " + self.language.__str__()

class Customization(models.Model):
    speaker = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    custom_color = models.CharField(max_length=10)

