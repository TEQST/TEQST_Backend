from django.test import TestCase, Client
from django.urls import reverse
from usermgmt.tests.utils import *
from django.contrib.auth.models import Group
from textmgmt.models import Folder, SharedFolder, Text
from usermgmt.models import CustomUser


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
        setup_users()  # 1 and 3 are publishers, 2 and 4 are not

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
        owner = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username']).pk
        response = self.client.post(reverse("folders"), data={'name': 'f1', 'owner': owner})
        self.assertEqual(response.status_code, 401)
    
    def test_folder_detail_no_auth(self):
        # setup
        Folder.objects.create(name='f1', owner=CustomUser.objects.get(username=USER_DATA_CORRECT_1['username']))
        # test
        response = self.client.get(reverse("folder-detail", args=[1]))
        self.assertEqual(response.status_code, 401)
        response = self.client.put(reverse("folder-detail", args=[1]))
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(reverse("folder-detail", args=[1]))
        self.assertEqual(response.status_code, 401)
    
    def test_folders_user_is_not_a_publisher(self):
        response = self.client.get(reverse("folders"), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        owner = CustomUser.objects.get(username=USER_DATA_CORRECT_2['username']).pk
        response = self.client.post(reverse("folders"), data={'name': 'f1', 'owner': owner}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
    
    def test_folder_detail_user_is_not_a_publisher(self):
        # setup
        Folder.objects.create(name='f1', owner=CustomUser.objects.get(username=USER_DATA_CORRECT_1['username']))
        # test
        response = self.client.get(reverse("folder-detail", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        response = self.client.put(reverse("folder-detail", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        response = self.client.delete(reverse("folder-detail", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
    
    def test_folders_empty(self):
        response = self.client.get(reverse("folders"), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

class TestTextUpload(TestCase):
    """
    urls tested:
    /api/texts/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        Group.objects.create(name='Publisher')
        setup_users()  # 1 and 3 are publishers, 2 and 4 are not
        owner = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        Folder.objects.create(name="Sharedfolder", owner=owner)

    def setUp(self):
        self.client = Client()
        login_data_1 = {"username": USER_DATA_CORRECT_1['username'],
                        "password": USER_DATA_CORRECT_1['password']}
        login_response_1 = self.client.post(reverse("login"), data=login_data_1)
        self.token_1 = 'Token ' + login_response_1.json()['token']
    
    def test_correct_upload(self):
        sf = Folder.objects.get(name="Sharedfolder")
        with open('testtext.txt') as fp:
            self.client.post(reverse("pub-texts"), data={'title': "testtext", 'shared_folder': sf.pk, 'textfile': fp}, HTTP_AUTHORIZATION=self.token_1)
        sf = Folder.objects.get(name="Sharedfolder")
        self.assertTrue(sf.is_shared_folder())