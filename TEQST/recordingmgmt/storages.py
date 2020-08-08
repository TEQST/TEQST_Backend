from django.core.files.storage import FileSystemStorage
import os, datetime
from pathlib import Path


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
            path = Path(self.path(name))
            date = datetime.datetime.now()
            new_file_name_ext = f'{path.stem}__{date.strftime("%Y_%m_%d_%H_%M_%S")}{path.suffix}'
            os.renames(path, path.parent/'Backup'/new_file_name_ext)
        return name