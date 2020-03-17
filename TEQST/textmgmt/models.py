from django.db import models
from django.conf import settings
from .utils import folder_path, folder_relative_path, NAME_ID_SPLITTER
import os
from zipfile import ZipFile
from chardet import detect


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
        return path + NAME_ID_SPLITTER + str(self.id)

    def get_readable_path(self):
        path = super().get_path()
        return path
    
    def has_any_recordings(self):
        for text in self.text.all():
            if text.has_any_finished_recordings():
                return True
        return False
    
    def create_zip_for_download(self) -> str:
        """
        create zip file and return the path to the download.zip file
        """
        path = settings.MEDIA_ROOT + '/' + self.get_path()
        zf = ZipFile(path + "/download.zip", 'w')
        # arcname is the name/path which the file will have inside the zip file
        zf.write(path + '/' + self.name + ".stm", arcname=self.name + ".stm")
        zf.write(path + "/log.txt", arcname="log.txt")
        # os.listdir also lists folders, but there should not be any folders in /AudioData
        for file_to_zip in os.listdir(path + "/AudioData"):
            arcpath = "AudioData/" + file_to_zip
            zf.write(path + "/AudioData/" + file_to_zip, arcname=arcpath)
        zf.close()
        return path + "/download.zip"



def upload_path(instance, filename):
    """
    Generates the upload path for a text
    """
    sf_path = instance.shared_folder.sharedfolder.get_path()
    path = sf_path + '/' + filename
    return path


# get file encoding type
def get_encoding_type(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']


class Text(models.Model):
    title = models.CharField(max_length=30)
    shared_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='text')
    textfile = models.FileField(upload_to=upload_path)

    def __str__(self):
        return self.title
    
    def has_any_finished_recordings(self):
        for tr in self.textrecording.all():
            if tr.is_finished():
                return True
        return False
    
    def save(self, *args, **kwargs):
        self.shared_folder = self.shared_folder.make_shared_folder()
        super().save(*args, **kwargs)
        
        # change encoding of uploaded file to utf-8
        srcfile = self.textfile.path
        trgfile = srcfile[:-4] + '_enc' + srcfile[-4:]
        from_codec = get_encoding_type(srcfile)

        with open(srcfile, 'r', encoding=from_codec) as f, open(trgfile, 'w', encoding='utf-8') as e:
            text = f.read()
            e.write(text)

        os.remove(srcfile) # remove old encoding file
        os.rename(trgfile, srcfile) # rename new encoding

    def get_content(self):
        f = open(self.textfile.path, 'r', encoding='utf-8-sig')
        sentence = ""
        content = []
        for line in f:
            if line == "\n":
                if sentence != "":
                    content.append(sentence)
                    sentence = ""
            else:
                sentence += line.replace('\n', ' ')
        if sentence != "":
            content.append(sentence)
        f.close()
        return content
    
    def sentence_count(self):
        return len(self.get_content())
