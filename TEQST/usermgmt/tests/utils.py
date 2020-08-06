from django.contrib.auth.models import Group
from django.urls import reverse
from django.conf import settings
from usermgmt.models import Language, CustomUser

import shutil
import os

USER_DATA_CORRECT_1 = {"username": "harry",
                     "password": "testing321",
                     "education": "M12",
                     "gender": "M",
                     "birth_year": 1999,
                     "language_ids": ["en", "fr"],
                     "accent": "Scotish",
                     "menu_language_id": "en",
                     "country": "USA"}

USER_DATA_CORRECT_2 = {"username": "ron",
                     "password": "testing321",
                     "education": "M12",
                     "gender": "M",
                     "birth_year": 2000,
                     "language_ids": ["en", "de"],
                     "accent": "German",
                     "menu_language_id": "de",
                     "country": "USA"}

USER_DATA_CORRECT_3 = {"username": "hermione",
                     "password": "testing321",
                     "education": "6T12",
                     "gender": "F",
                     "birth_year": 1997,
                     "language_ids": ["fr"],
                     "accent": "African",
                     "menu_language_id": "en",
                     "country": "USA"}

USER_DATA_CORRECT_4 = {"username": "ginny",
                     "password": "testing321",
                     "education": "B6",
                     "gender": "F",
                     "birth_year": 1998,
                     "language_ids": ["en", "fr", "es"],
                     "accent": "British",
                     "menu_language_id": "en",
                     "country": "USA"}

USERS_DATA_CORRECT = [USER_DATA_CORRECT_1, USER_DATA_CORRECT_2, USER_DATA_CORRECT_3, USER_DATA_CORRECT_4]


def setup_user(user_data, make_publisher=False):
    user_data = user_data.copy()
    languages = user_data.pop('language_ids')
    user = CustomUser.objects.create_user(**user_data)
    user.languages.set(languages)
    user.save()
    if make_publisher:
        pub_group = Group.objects.get_or_create(name='Publisher')[0]
        user.groups.add(pub_group)

def setup_users():
    for user_data in USERS_DATA_CORRECT:
        if user_data is USER_DATA_CORRECT_1 or user_data is USER_DATA_CORRECT_3:
            setup_user(user_data, make_publisher=True)
        else:
            setup_user(user_data)

def setup_languages():
    EN = Language.objects.get(short="en")
    EN.localization_file.name = 'locale/en.po'
    EN.save()
    DE = Language.objects.create(native_name="Deutsch", english_name="German", short="de")
    DE.localization_file.name = 'locale/de.po'
    DE.save()
    Language.objects.create(native_name="Espagnol", english_name="Spanish", short="es")
    Language.objects.create(native_name="Francais", english_name="French", short="fr")
    Language.objects.create(native_name="Arabic_native", english_name="Arabic", short="ar", right_to_left=True)

def get_user(index):
    return CustomUser.objects.get(username=USERS_DATA_CORRECT[index - 1]['username'])

def get_lang(short):
    return Language.objects.get(short=short)

def create_languages_users_groups():
    setup_languages()
    Group.objects.create(name='Publisher')
    setup_users()  # 1 and 3 are publishers, 2 and 4 are not

def login_test_user(user_number, client):
    user_index = user_number - 1
    assert 0 <= user_index < len(USERS_DATA_CORRECT)
    login_data = {"username": USERS_DATA_CORRECT[user_index]['username'],
                  "password": USERS_DATA_CORRECT[user_index]['password']}
    login_response = client.post(reverse("login"), data=login_data)
    return 'Token ' + login_response.json()['token']

def delete_all_users():
    for user in USERS_DATA_CORRECT:
        path = f'{settings.MEDIA_ROOT}/{user["username"]}/'
        if (os.path.exists(path)):
            shutil.rmtree(path)