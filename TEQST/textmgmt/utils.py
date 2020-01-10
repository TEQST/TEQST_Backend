from django.conf import settings
import os


def folder_path(folder):
    dirs = []
    user = str(folder.owner.username)
    while folder != None:  # go through the folders
        dirs.append(str(folder.name))
        folder = folder.parent
    dirs.append(user)
    dirs.reverse()
    media_path = '/'.join(dirs)
    path = os.path.join(settings.MEDIA_ROOT, media_path)
    return path