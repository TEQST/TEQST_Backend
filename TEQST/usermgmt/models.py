from django.db import models, transaction
from django.contrib import auth
from django.contrib.auth import models as auth_models
from . import utils, storages, countries


def get_english():
    try:
        with transaction.atomic():
            if Language.objects.filter(short='en').exists():
                return Language.objects.get(short='en').short
            lang = Language(native_name='english', english_name='english', short='en')
            lang.save()
        return lang.short
    except:
        return


class Language(models.Model):
    native_name = models.CharField(max_length=50)
    english_name = models.CharField(max_length=50)
    short = models.CharField(max_length=5, unique=True, primary_key=True)
    right_to_left = models.BooleanField(default=False)
    localization_file = models.FileField(upload_to=utils.upload_path, null=True, blank=True, storage=storages.OverwriteStorage())

    def __str__(self):
        return f'{self.english_name} ({self.native_name})'

    def is_menu_language(self):
        return bool(self.localization_file)


# classes Tag, Usage and Customization can be used to implement wunschkriterium Tags in Texts
class Tag(models.Model):
    identifier = models.CharField(max_length=10)
    default_color = models.CharField(max_length=10)

    def __str__(self):
        return self.identifier


class CustomUser(auth_models.AbstractUser):
    """
    Custom User Model which represents a TEQST user
    """
    gender = models.CharField(max_length=20, choices=utils.GENDER_CHOICES, default='N')
    birth_year = models.IntegerField()
    education = models.CharField(max_length=50, choices=utils.EDU_CHOICES, default='N')
    languages = models.ManyToManyField(Language, blank=True, related_name='speakers')
    # the accent field is for now just a charfield.
    accent = models.CharField(max_length=50)
    menu_language = models.ForeignKey(Language, on_delete=models.SET_DEFAULT, default=get_english, blank=True)
    country = models.CharField(max_length=10, choices=countries.COUNTRY_CHOICES)
    dark_mode = models.BooleanField(default=False, blank=True)

    def is_publisher(self):
        p = auth_models.Group.objects.get(name='Publisher')
        return p in self.groups.all()

    def is_listener(self):
        return self.listenfolder.exists()

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
    publisher = models.ForeignKey(auth.get_user_model(), on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    meaning = models.CharField(max_length=200)

    def __str__(self):
        return f'by {self.publisher.__str__()} for {self.tag.__str__()} in {self.language.__str__()}'


class Customization(models.Model):
    speaker = models.ForeignKey(auth.get_user_model(), on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    custom_color = models.CharField(max_length=10)

