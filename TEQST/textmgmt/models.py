from django.db import models
#from django.contrib.auth.models import User
from django.conf import settings
from .utils import folder_path, folder_relative_path
import os
import shutil

################################
# important todos:
# - before text ceration a sharedfolder must have been created
################################


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
        if self.is_shared_folder() and not isinstance(self, SharedFolder):
            sf = self.sharedfolder
            sf.name = self.name
            sf.save()
    
    def delete(self, *args, **kwargs):
        # TODO maybe this is desired, maybe not.
        if not isinstance(self, SharedFolder):
            shutil.rmtree(folder_path(self))
        # does not work if the folder is not there
        super().delete(*args, **kwargs)
    
    def is_shared_folder(self):
        return hasattr(self, 'sharedfolder')

    def make_shared_folder(self):
        #Check for folder having no children is required:
        # len(self.subfolder.all()) == 0
        if isinstance(self, SharedFolder):
            return self
        if self.is_shared_folder():
            return self.sharedfolder
        sf = SharedFolder(folder_ptr=self, name=self.name, owner=self.owner, parent=self.parent)
        sf.save()
        return sf


class SharedFolder(Folder):
    speaker = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='sharedfolder', blank=True)

    # __str__() is inherited

    def save(self, *args, **kwargs):
        # actual folder is created in super method
        # TODO upon creation create other necessary stuff like temp folders etc.
        super().save(*args, **kwargs)

    def get_path(self):
        # TODO implement
        return folder_relative_path(self)
    
    # maybe override delete() to not call shutil.rmtree()


def upload_path(instance, filename):
    path = instance.shared_folder.get_path() + '/' + filename
    return path


class Text(models.Model):
    title = models.CharField(max_length=30)
    # sentences_count = models.IntegerField(null=True)
    # sentences = models.TextField(null=True)
    # sentences can be replaced. A file read can easily be done from within the model
    shared_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='text')
    textfile = models.FileField(upload_to=upload_path)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # TODO a sharedfolder must have been created
        self.shared_folder = self.shared_folder.make_shared_folder()
        super().save(*args, **kwargs)
    
    def get_content(self):
        content = []
        count = -1
        self.textfile.open('r')
        for line in self.textfile:
            count += 1
            if count % 2 != 0:
                continue
            s = {}
            s['s_num'] = count // 2
            s['content'] = line
            content.append(s)
        self.textfile.close()
        return content