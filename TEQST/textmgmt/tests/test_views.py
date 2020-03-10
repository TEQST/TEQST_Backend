from django.test import TestCase, Client
from django.urls import reverse
from usermgmt.tests.utils import *
from django.contrib.auth.models import Group
from textmgmt.models import Folder, SharedFolder, Text


class TestFolderStructure(TestCase):
    """
    urls tested:
    /api/folders/
    /api/folders/<int:pk>/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        Group.objects.create(name='Publisher')
        setup_user(USER_DATA_CORRECT_1, make_publisher=True)
        setup_user(USER_DATA_CORRECT_2)

    def setUp(self):
        self.client = Client()
        login_data_1 = {"username": USER_DATA_CORRECT_1['username'],
                        "password": USER_DATA_CORRECT_1['password']}
        login_response_1 = self.client.post(reverse("login"), data=login_data_1)
        self.token_1 = 'Token ' + login_response_1.json()['token']
        login_data_2 = {"username": USER_DATA_CORRECT_2['username'],
                        "password": USER_DATA_CORRECT_2['password']}
        login_response_2 = self.client.post(reverse("login"), data=login_data_2)
        self.token_2 = 'Token ' + login_response_2.json()['token']
    
    def test_folders_no_auth(self):
        response = self.client.get(reverse("folders"))
        self.assertEqual(response.status_code, 401)
    
    def test_folder_detail_no_auth(self):
        pass