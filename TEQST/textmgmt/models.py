from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
#import .utils


class Folder(models.Model):
    name = models.CharField(max_length=50)
    # maybe useful:
    # limit_choices_to={'groups__name': 'Publisher'}
    # TODO rethink on_delete
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='folder')  
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subfolder', blank=True, null=True)

    # this method is useful for the shell and for the admin view
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # TODO if not exists yet: create actual Folder
        if not self.pk:
            pass
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # TODO do not delete actual folder. Except maybe if it is empty.
        super().delete(*args, **kwargs)


class SharedFolder(Folder):
    speaker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sharedfolder')

    # __str__() is inherited

    def save(self, *args, **kwargs):
        # actual folder is created in super method
        # TODO create other necessary stuff like temp folders etc.
        super().save(*args, **kwargs)


def upload_path():
    # TODO implement
    pass


class Text(models.Model):
    title = models.CharField(max_length=30)
    sentences_count = models.IntegerField(null=True)
    sentences = models.TextField(null=True)
    shared_folder = models.ForeignKey(SharedFolder, on_delete=models.CASCADE, related_name='text')
    textfile = models.FileField(upload_to=upload_path)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # TODO open file, fill fields sentences, sentences_count, close file
        super().save(*args, **kwargs)