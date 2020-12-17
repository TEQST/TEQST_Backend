from django.db import models
from django.conf import settings
from django.core.files import uploadedfile
from django.core.files.storage import default_storage
from django.contrib import auth
from . import utils
from usermgmt import models as user_models
import os, zipfile, chardet
from pathlib import Path


class Folder(models.Model):
    name = models.CharField(max_length=250)
    owner = models.ForeignKey(auth.get_user_model(), on_delete=models.CASCADE, related_name='folder')  
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
        return utils.folder_relative_path(self)

    def make_shared_folder(self):
        if self.is_shared_folder():
            return self.sharedfolder
        if self.subfolder.all().exists():
            raise TypeError("This folder can't be a shared folder")
        # create SharedFolder instance
        sf = SharedFolder(folder_ptr=self, name=self.name, owner=self.owner, parent=self.parent)
        sf.save()
        # create actual folders and files:
        sf_path = Path(sf.get_path())
        logfile = uploadedfile.SimpleUploadedFile('', '')
        default_storage.save(str(sf_path/'log.txt'), logfile)
        return sf


class SharedFolder(Folder):
    speaker = models.ManyToManyField(auth.get_user_model(), related_name='sharedfolder', blank=True)
    public = models.BooleanField(default=False)
    
    def make_shared_folder(self):
        return self
    
    def get_path(self):
        path = super().get_path()
        return path + utils.NAME_ID_SPLITTER + str(self.id)

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
        path = Path(self.get_path())
        # not using with here will cause the file not to close and thus not to be created
        with default_storage.open(str(path/'download.zip'), 'wb') as file:
            zf = zipfile.ZipFile(file, 'w')

            # arcname is the name/path which the file will have inside the zip file
            stm_file = default_storage.open(str(path/f'{self.name}.stm'), 'rb')
            zf.writestr(str(f'{self.name}.stm'), stm_file.read())
            log_file = default_storage.open(str(path/'log.txt'), 'rb')
            zf.writestr('log.txt', log_file.read())

            #for file_to_zip in (path/'AudioData').glob('*'):
            for file_to_zip in default_storage.listdir(str(path/'AudioData'))[1]:
                #if file_to_zip.is_file():
                arcpath = f'AudioData/{file_to_zip}'
                arc_file = default_storage.open(str(path/'AudioData'/file_to_zip), 'rb')
                zf.writestr(str(arcpath), arc_file.read())
            zf.close()
        return str(path/'download.zip')



def upload_path(instance, filename):
    """
    Generates the upload path for a text
    """
    sf_path = Path(instance.shared_folder.sharedfolder.get_path())
    path = sf_path/filename
    return path


# get file encoding type
def get_encoding_type(file_path):
    with default_storage.open(file_path, 'rb') as f:
        rawdata = f.read()
    return chardet.detect(rawdata)['encoding']


class Text(models.Model):
    title = models.CharField(max_length=100)
    language = models.ForeignKey(user_models.Language, on_delete=models.SET_NULL, null=True, blank=True)
    shared_folder = models.ForeignKey(SharedFolder, on_delete=models.CASCADE, related_name='text')
    textfile = models.FileField(upload_to=upload_path)

    def __str__(self):
        return self.title
    
    def is_right_to_left(self):
        if self.language:
            return self.language.right_to_left
        return False
    
    def has_any_finished_recordings(self):
        for tr in self.textrecording.all():
            if tr.is_finished():
                return True
        return False
    
    def save(self, *args, **kwargs):
        #Now expects a proper sharedfolder instance
        #Parsing a folder to sharedfolder is done in serializer or has to be done manually when working via shell
        #self.shared_folder = self.shared_folder.make_shared_folder()
        super().save(*args, **kwargs)
        """
        # change encoding of uploaded file to utf-8
        srcfile_path_str = self.textfile.name
        srcfile = Path(srcfile_path_str)
        trgfile = Path(srcfile_path_str[:-4] + '_enc' + srcfile_path_str[-4:])
        from_codec = get_encoding_type(srcfile)

        #with default_storage.open(srcfile, 'r', encoding=from_codec) as f, default_storage.open(trgfile, 'w', encoding='utf-8') as e:
        with default_storage.open(srcfile, 'r') as f, default_storage.open(trgfile, 'w') as e:
            text = f.read()
            e.write(text)

        #trgfile.replace(srcfile) # replace old file with the newly encoded file
        # the below three lines don't work
        default_storage.delete(srcfile)
        f = default_storage.open(trgfile)
        default_storage.save(srcfile, f)
        """

    def get_content(self):
        #f = default_storage.open(self.textfile.path, 'r', encoding='utf-8-sig')
        #f = default_storage.open(self.textfile.name, 'rb')
        f = self.textfile.open('rb')
        #file_content = f.readlines()

        # it is not enough to detect the encoding from the first line
        # it hast to be the entire file content
        encoding = chardet.detect(f.read())['encoding']
        f.seek(0)
        file_content = f.readlines()

        sentence = ""
        content = []
        for line in file_content:
            #line = line.decode('utf-8')
            line = line.decode(encoding)
            #line = line.decode('unicode_escape')
            if line == "\n" or line == "" or line == "\r\n":
                if sentence != "":
                    content.append(sentence)
                    sentence = ""
            else:
                sentence += line.replace('\n', ' ').replace('\r', ' ')
        if sentence != "":
            content.append(sentence)
        f.close()
        return content
    
    def sentence_count(self):
        return len(self.get_content())


    def word_count(self, sentence_limit=None):
        """
        count words of a text up to a given sentence
        @param sentence_limit: int, specify for how many sentences (starting from the beginning)
        the words should be counted. (e.g. 2: count word of the first two sentences)
        @return: int, number of words
        """
        sentences = self.get_content()
        if sentence_limit is None or sentence_limit > len(sentences):
            sentence_limit = len(sentences)
        count = 0
        for i in range(sentence_limit):
            count += sentences[i].strip().count(' ') + 1
        return count