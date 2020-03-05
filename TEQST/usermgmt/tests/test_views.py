from django.test import TestCase, Client
from django.conf import settings
from django.core.files import File
from django.urls import reverse
from usermgmt.models import Language

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
        loc_en = File(open(settings.MEDIA_ROOT + '/locale/en.po', 'rb'))
        EN = Language.objects.get(short="en")
        EN.localization_file = loc_en
        EN.save()
        loc_de = File(open(settings.MEDIA_ROOT + '/locale/de.po', 'rb'))
        Language.objects.create(native_name="Deutsch", english_name="German", short="de", localization_file=loc_de)
        Language.objects.create(native_name="Espagnol", english_name="Spanish", short="es")
        Language.objects.create(native_name="Francais", english_name="French", short="fr")

    def setUp(self):
        self.client = Client()

    def test_user_registration_all_correct(self):
        response = self.client.post(reverse("register"), data=USER_DATA_CORRECT)
        self.assertEqual(response.status_code, 201)

    def test_user_registration_all_correct_name_exists(self):
        # setup
        self.client.post(reverse("register"), data=USER_DATA_CORRECT)
        # test
        response = self.client.post(reverse("register"), data=USER_DATA_CORRECT)
        self.assertEqual(response.status_code, 400)
    