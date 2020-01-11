from django.db import models
#from django.contrib.auth.models import User
from django.conf import settings
from .utils import folder_path, folder_relative_path
import os
import shutil


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
        path = folder_path(self)
        if not self.pk:  # if folder is newly created
            os.makedirs(path)  # maybe mkdir works as well
            # maybe catch exceptions
        else:  # object already exists
            f_old = Folder.objects.get(id=self.id)
            path_f_old = folder_path(f_old)
            if not os.path.exists(path_f_old):  # if object exists, but not actual folder
                os.makedirs(path_f_old)
            if f_old.name != self.name:  # if name changed
                os.rename(path_f_old, path)
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # TODO maybe this is desired, maybe not.
        shutil.rmtree(folder_path(self))
        # does not work if the folder is not there
        super().delete(*args, **kwargs)
    
    def is_shared_folder(self):
        return hasattr(self, 'sharedfolder')

    def make_shared_folder(self):
        #Check for folder having no children is required:
        # len(self.subfolder.all()) == 0
        if self.is_shared_folder():
            return self
        sf = SharedFolder(folder_ptr=self, name=self.name, owner=self.owner, parent=self.parent)
        sf.save()
        return sf


class SharedFolder(Folder):
    speaker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sharedfolder', null=True, blank=True)

    # __str__() is inherited

    def save(self, *args, **kwargs):
        # actual folder is created in super method
        # TODO create other necessary stuff like temp folders etc.
        super().save(*args, **kwargs)

    def get_path(self):
        # TODO implement
        return folder_relative_path(self)


def upload_path(instance, filename):
    path = instance.shared_folder.get_path() + '/' + filename
    return path


class Text(models.Model):
    title = models.CharField(max_length=30)
    sentences_count = models.IntegerField(null=True)
    # sentences = models.TextField(null=True)
    # sentences can be replaced. A file read can easily be done from within the model
    shared_folder = models.ForeignKey(SharedFolder, on_delete=models.CASCADE, related_name='text')
    textfile = models.FileField(upload_to=upload_path)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # TODO open file, fill fields sentences, sentences_count, close file
        if not self.pk:
            count = 1
            self.textfile.open('r')
            for line in self.textfile:
                count += 1
            self.sentences_count = int(count / 2)
        super().save(*args, **kwargs)
    
    def get_content(self):
        self.textfile.open('r')
        return self.textfile.read()