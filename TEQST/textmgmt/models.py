from django.db import models, transaction
from django.conf import settings
from django.core.files import uploadedfile, base
from django.core.files.storage import default_storage
from django.contrib import auth
from rest_framework import views
from . import utils
from usermgmt import models as user_models
from usermgmt.countries import COUNTRY_CHOICES
import os, zipfile, chardet, zlib, re
from pathlib import Path
#from google.cloud.storage import Blob


class Folder(models.Model):
    name = models.CharField(max_length=250)
    owner = models.ForeignKey(auth.get_user_model(), on_delete=models.CASCADE, related_name='folder')  
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subfolder', blank=True, null=True)

    class Meta:
        ordering = ['owner', 'name']
        constraints = [
            models.UniqueConstraint(fields=['name','parent'], name='unique_subfolder'),
            models.UniqueConstraint(fields=['name'], condition=models.Q(parent=None), name='unique_folder'),
        ]

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
        #sf_path = Path(sf.get_path())
        #logfile = uploadedfile.SimpleUploadedFile('', '')
        #default_storage.save(str(sf_path/'log.txt'), logfile)
        return sf


def stm_upload_path(instance, filename):
    sf_path = instance.get_path()
    title = re.sub(r"[\- ]", "_", instance.name)
    title = title.lower()
    return f'{sf_path}/{title}.stm'


def log_upload_path(instance, filename):
    sf_path = instance.get_path()
    return f'{sf_path}/log.txt'


class SharedFolder(Folder):
    speaker = models.ManyToManyField(auth.get_user_model(), related_name='sharedfolder', blank=True)
    listener = models.ManyToManyField(auth.get_user_model(), related_name='listenfolder', blank=True)
    public = models.BooleanField(default=False)

    stmfile = models.FileField(upload_to=stm_upload_path, blank=True)
    logfile = models.FileField(upload_to=log_upload_path, blank=True)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.stmfile.save('name', base.ContentFile(''), save=False)
            self.logfile.save('name', base.ContentFile(''), save=False)
        super().save(*args, **kwargs)
    
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
        #path = Path(self.get_path())

        # not using with here will cause the file not to close and thus not to be created
        # with default_storage.open(str(path/'download.zip'), 'wb') as file:
        #     zf = zipfile.ZipFile(file, 'w')  #, compression=zipfile.ZIP_DEFLATED, compresslevel=6)

        #     # arcname is the name/path which the file will have inside the zip file
        #     with default_storage.open(str(path/f'{self.name}.stm'), 'rb') as stm_file:
        #         zf.writestr(str(f'{self.name}.stm'), stm_file.read())  #, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        #     #stm_file.close()
        #     with default_storage.open(str(path/'log.txt'), 'rb') as log_file:
        #         zf.writestr('log.txt', log_file.read())  #, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        #     #log_file.close()
        #     zf.close()
        #     del zf

        # #for file_to_zip in (path/'AudioData').glob('*'):
        # for file_to_zip in default_storage.listdir(str(path/'AudioData'))[1]:
        #     #if file_to_zip.is_file():
        #     arcpath = f'AudioData/{file_to_zip}'
        #     arc_file_content = None
        #     with default_storage.open(str(path/'AudioData'/file_to_zip), 'rb') as arc_file:
        #         arc_file_content = arc_file.read()
            
        #     my_file = default_storage.open(str(path/'download.zip'), 'rwb')
        #     my_zf = zipfile.ZipFile(my_file, 'a')
        #     my_zf.writestr(str(arcpath), arc_file_content)  #, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        #     my_zf.close()
        #     del my_zf
        #     my_file.close()

        #with default_storage.open(str(path/'download.zip'), 'wb') as file:
        f = default_storage.open(self.get_path()+'/download.zip', 'wb')
        zf = zipfile.ZipFile(f, 'w')

        # arcname is the name/path which the file will have inside the zip file
        with self.stmfile.open('rb') as stm_file:
            zf.writestr(self.stmfile.name.replace(self.get_path()+'/', ''), stm_file.read())
        with self.logfile.open('rb') as log_file:
            zf.writestr(self.logfile.name.replace(self.get_path()+'/', ''), log_file.read())

        #for file_to_zip in (path/'AudioData').glob('*'):
        for text in self.text.all():
            for trec in text.textrecording.all():
                if trec.is_finished():
                    with trec.stmfile.open('rb') as arc_file:
                        zf.writestr(trec.stmfile.name.replace(self.get_path()+'/', ''), arc_file.read())
        zf.close()
        f.close()

        return self.get_path()+'/download.zip'

        #with default_storage.open(str(path/'download.zip'), 'wb') as ftw:
            #fsize = os.stat("/tmp/download.zip").st_size
        #    with open("/tmp/download.zip", 'rb') as tempfile:
                # for i in range((fsize // 4194304) + 1):
                #     chunk = tempfile.read(4194304)
                #     ftw.write(chunk)
                # cnt = 0
                # while True:
                #     cnt += 1
                #     chunk = tempfile.read(4194304)
                #     if chunk == '' or cnt > 2048:
                #         break
                #     ftw.write(chunk)
                #for i in range(fsize // 4194304):
                #    ftw.blob.upload_from_file(tempfile, size=4194304, content_type=ftw.mime_type, predefined_acl=ftw._storage.default_acl)
                #ftw.blob.upload_from_file(tempfile, size=(fsize % 4194304), content_type=ftw.mime_type, predefined_acl=ftw._storage.default_acl)
        #        ftw.blob.upload_from_file(tempfile, content_type=ftw.mime_type, predefined_acl=ftw._storage.default_acl)

            # with default_storage.open(str(path/'res.txt'), 'wb') as res:
            #     res.write("done with file copy")


        #return "/tmp/download.zip"

    def concat_stms(self):
        with self.stmfile.open('wb') as full:
            with open(settings.BASE_DIR/'header.stm', 'rb') as header:
                full.write(header.read())
            
            # header entries for country and accent
            # TODO maybe it's alright if we put all existing countries + accents in here?
            #       would lead to simplifications
            speakers = user_models.CustomUser.objects.filter(textrecording__text__shared_folder=self)
            countries = set([s.country for s in speakers])
            accents = set([s.accent for s in speakers])
            country_dict = dict(COUNTRY_CHOICES)
            c_header = ';; CATEGORY "3" "COUNTRY" ""\n'
            for country in countries:
                c_header += f';; LABEL "{country}" "{country_dict[country]}" ""\n'
            a_header = ';; CATEGORY "4" "ACCENT" ""\n'
            for accent in accents:
                a_header += f';; LABEL "{accent}" "{accent}" ""\n'
            full.write(bytes(c_header, encoding='utf-8'))
            full.write(bytes(a_header, encoding='utf-8'))

            for text in self.text.all():
                text.append_stms(full)
                

    def log_contains_user(self, username):
        with self.logfile.open('rb') as log:
            lines = log.readlines()
            for line in lines:
                line = line.decode('utf-8')
                if line[:8] == 'username':
                    if line[10:] == username + '\n':
                        return True
        return False


    def add_user_to_log(self, user):
        if self.log_contains_user(str(user.username)):
            return
        #logfile = default_storage.open(str(path), 'ab')
        file_content = b''
        with self.logfile.open('rb') as log:
            file_content = log.read()
        with self.logfile.open('wb') as log:
            # logfile.writelines(bytes(line + '\n', encoding='utf-8') for line in [
            #     f'username: {user.username}',
            #     f'birth_year: {user.birth_year}',
            #     f'gender: {user.gender}',
            #     f'education: {user.education}',
            #     f'accent: {user.accent}',
            #     f'country: {user.country}',
            #     '#'
            # ])
            logfile_entry = 'username: ' + str(user.username) + '\n' \
                            + 'email: ' + str(user.email) + '\n' \
                            + 'date_joined: ' + str(user.date_joined) + '\n' \
                            + 'birth_year: ' + str(user.birth_year) + '\n#\n'
            file_content += bytes(logfile_entry, encoding='utf-8')
            log.write(file_content)



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

    class Meta:
        ordering = ['shared_folder','title']
        constraints = [
            models.UniqueConstraint(fields=['title','shared_folder'], name='unique_text'),
        ]

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

    def create_sentences(self):
        with transaction.atomic():
            if not self.sentences.exists():
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

                for i in range(len(content)):
                    self.sentences.create(content=content[i], index=i + 1, word_count=content[i].strip().count(' ') + 1)

    def get_content(self):
        if not self.sentences.exists():
            self.create_sentences()
        content = []
        for sentence in self.sentences.all():
            content.append(sentence.content)
        return content
    
    def sentence_count(self):
        if not self.sentences.exists():
            self.create_sentences()
        return self.sentences.count()

    def word_count(self, sentence_limit=None):
        if not self.sentences.exists():
            self.create_sentences()
        count = 0
        if sentence_limit == None:
            for sentence in self.sentences.all():
                count += sentence.word_count
        else:
            for sentence in self.sentences.filter(index__lte=sentence_limit):
                count += sentence.word_count
        return count
    
    def append_stms(self, file):
        for trec in self.textrecording.all():
            if trec.is_finished():
                with trec.stmfile.open('rb') as part:
                    file.write(part.read())


class Sentence(models.Model):
    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='sentences', null=False, blank=False)
    content = models.TextField(null=False, blank=False)
    word_count = models.IntegerField(null=False, blank=False)
    index = models.IntegerField(null=False, blank=False)

    class Meta:
        ordering = ['text', 'index']
        constraints = [
            models.UniqueConstraint(fields=['text', 'index'], name='unique_sentence'),
        ]

    def __str__(self):
        return str(self.index) + ": " + self.content