from django.core.files import storage
import datetime
from pathlib import Path


class OverwriteStorage(storage.default_storage.__class__):
    """
    This provides a file storage policy that overwrites files in the event of equal filenames
    """

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name

class BackupStorage(storage.default_storage.__class__):
    """
    This provides a file storage policy that overwrites files in the event of equal filenames
    """

    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            path = Path(name)
            date = datetime.datetime.now()
            new_file_name_ext = f'{path.stem}__{date.strftime("%Y_%m_%d_%H_%M_%S")}{path.suffix}'
            old_file = self.open(str(path), 'rb')
            self.save(str(path.parent/'Backup'/new_file_name_ext), old_file)
            old_file.close()
            self.delete(name)
        return name