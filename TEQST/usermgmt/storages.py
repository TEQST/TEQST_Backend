from django.core.files import storage


class OverwriteStorage(storage.default_storage.__class__):
    """
    This provides a file storage policy that overwrites files in the event of equal filenames
    """

    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            self.delete(name)
        return name