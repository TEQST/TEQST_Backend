from django.core.files import storage


class OverwriteStorage(storage.FileSystemStorage):
    """
    This provides a file storage policy that overwrites files in the event of equal filenames
    """

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name