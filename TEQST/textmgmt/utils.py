from django.conf import settings
import os


def folder_relative_path(folder):
    dirs = []
    user = str(folder.owner.username)
    while folder != None:  # go through the folders
        dirs.append(str(folder.get_filesystem_name()))
        folder = folder.parent
    dirs.append(user)
    dirs.reverse()
    media_path = '/'.join(dirs)
    return media_path


def folder_path(folder):
    media_path = folder_relative_path(folder)
    path = os.path.join(settings.MEDIA_ROOT, media_path)
    return path
