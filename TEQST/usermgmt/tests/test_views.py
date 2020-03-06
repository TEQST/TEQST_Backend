from django.test import TestCase, Client
from django.conf import settings
from django.core.files import File
from django.urls import reverse
from usermgmt.models import Language, CustomUser

from datetime import date

USER_DATA_CORRECT = {"username": "harry",
                     "password": "testing321",
                     "education": "M12",
                     "gender": "M",
                     "birth_year": 1999,
                     "language_ids": ["en", "fr"],
                     "menu_language_id": "en",
                     "country": "USA"}


class TestRegistration(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        EN = Language.objects.get(short="en")
        EN.localization_file.name = 'locale/en.po'
        EN.save()
        DE = Language.objects.create(native_name="Deutsch", english_name="German", short="de")
        DE.localization_file.name = 'locale/de.po'
        DE.save()
        Language.objects.create(native_name="Espagnol", english_name="Spanish", short="es")
        Language.objects.create(native_name="Francais", english_name="French", short="fr")

    def setUp(self):
        self.client = Client()

    def test_user_registration_all_correct(self):
        response = self.client.post(reverse("register"), data=USER_DATA_CORRECT)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=USER_DATA_CORRECT['username'])
        self.assertEqual(user.username, USER_DATA_CORRECT['username'])
        self.assertEqual(user.education, USER_DATA_CORRECT['education'])
        self.assertEqual(user.gender, USER_DATA_CORRECT['gender'])
        self.assertEqual(user.birth_year, USER_DATA_CORRECT['birth_year'])
        self.assertTrue(Language.objects.get(short='en') in user.languages.all())
        self.assertTrue(Language.objects.get(short='fr') in user.languages.all())
        self.assertEqual(user.languages.count(), 2)
        self.assertEqual(user.menu_language, Language.objects.get(short='en'))
        self.assertEqual(user.country, USER_DATA_CORRECT['country'])


    def test_user_registration_all_correct_name_exists(self):
        # setup
        self.client.post(reverse("register"), data=USER_DATA_CORRECT)
        # test
        response = self.client.post(reverse("register"), data=USER_DATA_CORRECT)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_username(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('username')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_invalid_username(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data['username'] = 'har ry'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_password(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('password')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)

    def test_user_registration_without_education(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('education')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.education, 'N')
    
    def test_user_registration_invalid_education(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data['education'] = 'ABC'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_gender(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('gender')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.gender, 'N')
    
    def test_user_registration_invalid_gender(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data['gender'] = 'A'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_birth_year(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('birth_year')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_invalid_birth_year_small(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data['birth_year'] = 1899
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_invalid_birth_year_big(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data['birth_year'] = date.today().year + 1
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    # TODO rethink the whole language thing

    def test_user_registration_without_language_ids(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('language_ids')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.languages.count(), 0)
    
    def test_user_registration_without_menu_language_id(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('menu_language_id')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        engl = Language.objects.get(short='en')
        self.assertEqual(user.menu_language, engl)
    
    def test_user_registration_invalid_menu_language_no_locfile(self):
        """
        registration should fail if given menu language is a language, but not a menu language (i.e. has no .po file)
        """
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data['menu_language_id'] = 'fr'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_invalid_menu_language_no_language(self):
        """
        registration should fail if given menu language is not a language
        """
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data['menu_language_id'] = 'ru'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_country(self):
        # setup
        user_data = USER_DATA_CORRECT.copy()
        user_data.pop('country')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.country, None)