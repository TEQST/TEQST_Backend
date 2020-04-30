from django.core.files.storage import FileSystemStorage
import os


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
            os.rename(dir_name + file_name, dir_name + "Backup/" + file_name)
        return name