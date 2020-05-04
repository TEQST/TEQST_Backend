from django.core.files.storage import FileSystemStorage
import os, datetime


class OverwriteStorage(FileSystemStorage):
    """
    This provides a file storage policy that overwrites files in the event of equal filenames
    """

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name

class BackupStorage(FileSystemStorage):
    """
    This provides a file storage policy that overwrites files in the event of equal filenames
    """

    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            dir_name, file_name = os.path.split(self.path(name))
            name, ext = os.path.splitext(file_name)
            date = datetime.datetime.now()
            new_file_name = name + "__" + date.strftime("%Y_%m_%d_%H_%M_%S") + ext
            os.renames(os.path.join(dir_name, file_name), os.path.join(dir_name, 'Backup', new_file_name))
        return name