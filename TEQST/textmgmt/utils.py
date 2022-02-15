from django.conf import settings
from usermgmt.countries import COUNTRY_CHOICES
from usermgmt.utils import GENDER_CHOICES, EDU_CHOICES

from . import models

NAME_ID_SPLITTER = '__'


def filter_texts(owner, users=[], countries=[], accents=[]):
    filter_dict = {
        'shared_folder__owner': owner,
    }
    if users:
        filter_dict['textrecording__speaker__in']=users
    if countries:
        filter_dict['textrecording__speaker__country__in']=countries
    if accents:
        filter_dict['textrecording__speaker__accent__in']=accents
    return models.Text.objects.filter(**filter_dict).distinct()


def filter_shared_folders(owner, users=[], countries=[], accents=[]):
    texts = filter_texts(owner=owner, users=users, countries=countries, accents=accents)
    return models.SharedFolder.objects.filter(text__in=texts).distinct()


def filter_folders(owner, parent=None, users=[], countries=[], accents=[]):
    results = []
    shared_folders = filter_shared_folders(owner=owner, users=users, countries=countries, accents=accents)
    folders = owner.folder.filter(sharedfolder__in=shared_folders).distinct()
    while folders.exists():
        results += folders.filter(parent=parent).values_list('pk', flat=True)
        print('DEBUG', folders)
        print('DEBUG', folders.filter(parent=parent))
        print('DEBUG', results)
        folders = owner.folder.filter(subfolder__in=folders).distinct()
    return models.Folder.objects.filter(pk__in=results).distinct()


def create_headers(speakers):
    """
    Creates all necessary stm headers for the given userlist
    """
    genders = {s.gender for s in speakers}
    gender_dict = dict(GENDER_CHOICES)
    g_header = ';; CATEGORY "0" "SEX" ""\n'
    for gender in genders:
        g_header += f';; LABEL "{gender}" "{gender_dict[gender]}" ""\n'

    edus = {s.education for s in speakers}
    edu_dict = dict(EDU_CHOICES)
    e_header = ';; CATEGORY "1" "EDUCATION" ""\n'
    for edu in edus:
        e_header += f';; LABEL "{edu}" "{edu_dict[edu]}" ""\n'

    p_header = ';; CATEGORY "2" "PERMISSION" ""\n'
    p_header += ';; LABEL "SR" "SPEECH RECOGNITION" ""\n'
    p_header += ';; LABEL "TTS" "TEXT TO SPEECH" ""\n'
    p_header += ';; LABEL "SRTTS" "BOTH" ""\n'

    countries = {s.country for s in speakers}
    country_dict = dict(COUNTRY_CHOICES)
    c_header = ';; CATEGORY "3" "COUNTRY" ""\n'
    for country in countries:
        c_header += f';; LABEL "{country}" "{country_dict[country]}" ""\n'

    accents = {s.accent for s in speakers}
    a_header = ';; CATEGORY "4" "ACCENT" ""\n'
    for accent in accents:
        a_header += f';; LABEL "{accent}" "{accent}" ""\n'

    return g_header + e_header + p_header + c_header + a_header


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
