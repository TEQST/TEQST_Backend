from django.conf import settings

NAME_ID_SPLITTER = '__'

def folder_relative_path(folder):
    dirs = []
    user = str(folder.owner.username)
    while folder != None:  # go through the folders
        dirs.append(str(folder.name))
        folder = folder.parent
    dirs.append(user)
    dirs.reverse()
    media_path = '/'.join(dirs)
    return media_path


#Deprecated, since absolute paths aren't used anymore
def folder_path(folder):
    media_path = folder_relative_path(folder)
    path = settings.MEDIA_ROOT/media_path
    return path
