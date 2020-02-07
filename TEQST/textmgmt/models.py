from django.db import models
from django.conf import settings
from .utils import folder_path, folder_relative_path
import os


class Folder(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='folder')  
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subfolder', blank=True, null=True)

    # this method is useful for the shell and for the admin view
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # TODO test, if this is actually not needed, then omit the save method
        # if self.is_shared_folder() and not isinstance(self, SharedFolder):
        #     sf = self.sharedfolder
        #     sf.name = self.name
        #     sf.save()

    def get_parent_name(self):
        if self.parent == None:
            return None
        return self.parent.name

    def is_shared_folder(self):
        """
        This method returns True if called on a Folder instance for which a corresponding SharedFolder instance exists.
        """
        return hasattr(self, 'sharedfolder')
    
    def get_path(self):
        return folder_relative_path(self)

    def make_shared_folder(self):
        if self.is_shared_folder():
            return self.sharedfolder
        # create SharedFolder instance
        sf = SharedFolder(folder_ptr=self, name=self.name, owner=self.owner, parent=self.parent)
        sf.save()
        # create actual folders and files:
        sf_path = settings.MEDIA_ROOT + '/' + sf.get_path()
        print("creating stuff at", sf_path)
        os.makedirs(sf_path + '/STM')
        os.mkdir(sf_path + '/AudioData')
        open(sf_path + '/log.txt', 'w').close()
        return sf


class SharedFolder(Folder):
    speaker = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='sharedfolder', blank=True)
    
    def make_shared_folder(self):
        return self
    
    def get_path(self):
        path = super().get_path()
        return path + '__' + str(self.id)

    def get_readable_path(self):
        path = super().get_path()
        return path


def upload_path(instance, filename):
    """
    Generates the upload path for a text
    """
    sf_path = instance.shared_folder.sharedfolder.get_path()
    path = sf_path + '/' + filename
    return path


class Text(models.Model):
    title = models.CharField(max_length=30)
    shared_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='text')
    textfile = models.FileField(upload_to=upload_path)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.shared_folder = self.shared_folder.make_shared_folder()
        super().save(*args, **kwargs)

    def get_content(self):
        f = self.textfile.open('r')
        sentence = ""
        content = []
        for line in f:
            if line == "\n":
                if sentence != "":
                    content.append(sentence)
                    sentence = ""
            else:
                sentence += line.strip('\n')
        if sentence != "":
            content.append(sentence)
        f.close()
        return content
    
    def sentence_count(self):
        return len(self.get_content())
