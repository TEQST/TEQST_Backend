from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from usermgmt.tests.utils import *
from django.contrib.auth.models import Group
from textmgmt.models import Folder, SharedFolder, Text
from usermgmt.models import CustomUser
from recordingmgmt.models import TextRecording, SentenceRecording

import shutil
import os
from django.core.files import File


class TestFolderListView(TestCase):
    """
    urls tested:
    /api/folders/
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
        response = self.client.post(reverse("folders"), data={'name': 'f1'})
        self.assertEqual(response.status_code, 401)
    
    def test_folders_user_is_not_a_publisher(self):
        response = self.client.get(reverse("folders"), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        owner = CustomUser.objects.get(username=USER_DATA_CORRECT_2['username']).pk
        response = self.client.post(reverse("folders"), data={'name': 'f1'}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
    
    def test_folders_GET_empty(self):
        response = self.client.get(reverse("folders"), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
    
    def test_folders_GET_with_content(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        user3 = CustomUser.objects.get(username=USER_DATA_CORRECT_3['username'])
        Folder.objects.create(name='3f1', owner=user3)
        f1 = Folder.objects.create(name='1f1', owner=user1)
        Folder.objects.create(name='1f2', owner=user1)
        Folder.objects.create(name='1f1_1', parent=f1, owner=user1)
        # test
        response = self.client.get(reverse("folders"), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        names = [response.json()[0]['name'], response.json()[1]['name']]
        self.assertTrue('1f1' in names)
        self.assertTrue('1f2' in names)
    
    def test_folders_POST_correct_without_parent(self):
        response = self.client.post(reverse("folders"), data={'name': 'f1', 'parent': ''}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Folder.objects.all()), 1)
        self.assertTrue(Folder.objects.filter(name='f1').exists())
    
    def test_folders_POST_correct_with_parent(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.post(reverse("folders"), data={'name': 'f1_1', 'parent': str(f1.pk)}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Folder.objects.all()), 2)
        self.assertTrue(Folder.objects.filter(name='f1_1').exists())
    
    def test_folders_POST_without_name(self):
        response = self.client.post(reverse("folders"), data={'parent': ''}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_folders_POST_empty_name(self):
        response = self.client.post(reverse("folders"), data={'name': '', 'parent': ''}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_folders_POST_name_exists(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.post(reverse("folders"), data={'name': 'f1', 'parent': ''}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_folders_POST_name_exists_with_parent(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Folder.objects.create(name='f1_1', parent=f1, owner=user1)
        # test
        response = self.client.post(reverse("folders"), data={'name': 'f1_1', 'parent': str(f1.pk)}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_folders_POST_invalid_name(self):
        # the "__" (double underscore) is invalid
        response = self.client.post(reverse("folders"), data={'name': 'f1__1', 'parent': ''}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_folders_POST_without_parent(self):
        response = self.client.post(reverse("folders"), data={'name': 'f1'}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_folders_POST_invalid_parent(self):
        # setup
        user3 = CustomUser.objects.get(username=USER_DATA_CORRECT_3['username'])
        f3_1 = Folder.objects.create(name='f3_1', owner=user3)
        # test
        response = self.client.post(reverse("folders"), data={'name': 'f1', 'parent': str(f3_1.pk)}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_folders_POST_parent_does_not_exist(self):
        response = self.client.post(reverse("folders"), data={'name': 'f1', 'parent': '99'}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)


class TestFolderDetailedView(TestCase):
    """
    urls tested:
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_folder_detail_no_auth(self):
        # setup
        Folder.objects.create(name='f1', owner=CustomUser.objects.get(username=USER_DATA_CORRECT_1['username']))
        # test
        response = self.client.get(reverse("folder-detail", args=[1]))
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(reverse("folder-detail", args=[1]))
        self.assertEqual(response.status_code, 401)
    
    def test_folder_detail_user_is_not_a_publisher(self):
        # setup
        Folder.objects.create(name='f1', owner=CustomUser.objects.get(username=USER_DATA_CORRECT_1['username']))
        # test
        response = self.client.get(reverse("folder-detail", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        response = self.client.delete(reverse("folder-detail", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
    
    def test_folder_detail_DELETE_correct_normal_folder(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Folder.objects.create(name='f1_1', parent=f1, owner=user1)
        # test
        response = self.client.delete(reverse("folder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Folder.objects.count(), 0)

    def test_folder_detail_DELETE_correct_shared_folder(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.delete(reverse("folder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Folder.objects.count(), 0)
        self.assertEqual(SharedFolder.objects.count(), 0)
        self.assertEqual(Text.objects.count(), 0)

    def test_folder_detail_DELETE_folder_does_not_exist(self):
        response = self.client.delete(reverse("folder-detail", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_folder_detail_DELETE_invalid_folder(self):
        # setup
        user3 = CustomUser.objects.get(username=USER_DATA_CORRECT_3['username'])
        f1 = Folder.objects.create(name='f1', owner=user3)
        # test
        response = self.client.delete(reverse("folder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Folder.objects.count(), 1)

    def test_folder_detail_GET_correct_normal_folder(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Folder.objects.create(name='f1_1', parent=f1, owner=user1)
        Folder.objects.create(name='f1_2', parent=f1, owner=user1)
        Folder.objects.create(name='f1_3', parent=f1, owner=user1)
        # test
        response = self.client.get(reverse("folder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['subfolder']), 3)

    # this request is never used with a sharedfolder. However it does not hurt to leave it possible.
    def test_folder_detail_GET_correct_shared_folder(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("folder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['subfolder']), 0)

    def test_folder_detail_GET_folder_does_not_exist(self):
        response = self.client.get(reverse("folder-detail", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_folder_detail_GET_invalid_folder(self):
        # setup
        user3 = CustomUser.objects.get(username=USER_DATA_CORRECT_3['username'])
        f1 = Folder.objects.create(name='f1', owner=user3)
        # test
        response = self.client.get(reverse("folder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)


'''
class TestTextUpload(TestCase):
    """
    urls tested:
    /api/pub/texts/ POST
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

    @classmethod
    def tearDownClass(cls):
        Folder.objects.filter(name="sharedfolder").delete()
        super().tearDownClass()

    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
        sf = Folder.objects.get(name="Sharedfolder")
        Text.objects.filter(shared_folder=sf).delete()
    
    def test_correct_upload(self):
        sf = Folder.objects.get(name="Sharedfolder")
        with open('testtext.txt') as fp:
            self.client.post(reverse("pub-texts"), data={'title': "testtext", 'shared_folder': sf.pk, 'textfile': fp}, HTTP_AUTHORIZATION=self.token_1)
        sf = Folder.objects.get(name="Sharedfolder")
        self.assertTrue(sf.is_shared_folder())

    def test_no_text(self):
        sf = Folder.objects.get(name="Sharedfolder")
        response = self.client.post(reverse("pub-texts"), data={'title': "testtext", 'shared_folder': sf.pk}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)

    def test_no_shared_folder(self):
        sf = Folder.objects.get(name="Sharedfolder")
        with open('testtext.txt') as fp:
            response = self.client.post(reverse("pub-texts"), data={'title': "testtext", 'textfile': fp}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)

    def test_correct_upload(self):
        sf = Folder.objects.get(name="Sharedfolder")
        with open('testtext.txt') as fp:
            response = self.client.post(reverse("pub-texts"), data={'shared_folder': sf.pk, 'textfile': fp}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)

    def test_double_upload(self):
        sf = Folder.objects.get(name="Sharedfolder")
        with open('testtext.txt') as fp:
            self.client.post(reverse("pub-texts"), data={'title': "testtext", 'shared_folder': sf.pk, 'textfile': fp}, HTTP_AUTHORIZATION=self.token_1)
        sf = Folder.objects.get(name="Sharedfolder")
        self.assertTrue(sf.is_shared_folder())
        with open('testtext.txt') as fp:
            response = self.client.post(reverse("pub-texts"), data={'title': "testtext", 'shared_folder': sf.pk, 'textfile': fp}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
        
    def test_no_auth(self):
        sf = Folder.objects.get(name="Sharedfolder")
        with open('testtext.txt') as fp:
            response = self.client.post(reverse("pub-texts"), data={'title': "testtext", 'shared_folder': sf.pk, 'textfile': fp})
        self.assertEqual(response.status_code, 401)
'''


class TestTextCreation(TestCase):
    """
    urls tested:
    /api/pub/texts/ POST
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
        self.user1 = get_user(1)
        self.f1 = Folder.objects.create(name='f1', owner=self.user1)
        self.textpath = os.path.join(settings.MEDIA_ROOT, 'test_resources/testtext.txt')
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_upload_no_auth(self):
        with open(self.textpath) as fp:
            data = {'title': 'text1', 'shared_folder': self.f1.pk, 'language': 'en', 'textfile': fp}
            response = self.client.post(reverse("pub-texts"), data=data)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.f1.is_shared_folder())
    
    def test_upload_user_is_not_a_publisher(self):
        with open(self.textpath) as fp:
            data = {'title': 'text1', 'shared_folder': self.f1.pk, 'language': 'en', 'textfile': fp}
            response = self.client.post(reverse("pub-texts"), data=data, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.f1.is_shared_folder())

    def test_upload_correct(self):
        with open(self.textpath) as fp:
            data = {'title': 'text1', 'shared_folder': self.f1.pk, 'language': 'en', 'textfile': fp}
            response = self.client.post(reverse("pub-texts"), data=data, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.f1.is_shared_folder())
    
    def test_upload_twice_same_title(self):
        with open(self.textpath) as fp:
            data = {'title': 'text1', 'shared_folder': self.f1.pk, 'language': 'en', 'textfile': fp}
            response = self.client.post(reverse("pub-texts"), data=data, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.f1.is_shared_folder())
        with open(self.textpath) as fp:
            data = {'title': 'text1', 'shared_folder': self.f1.pk, 'language': 'en', 'textfile': fp}
            response = self.client.post(reverse("pub-texts"), data=data, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
    
    def test_upload_without_language(self):
        with open(self.textpath) as fp:
            data = {'title': 'text1', 'shared_folder': self.f1.pk, 'textfile': fp}
            response = self.client.post(reverse("pub-texts"), data=data, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.f1.is_shared_folder())
    
    def test_upload_language_does_not_exist(self):
        with open(self.textpath) as fp:
            data = {'title': 'text1', 'shared_folder': self.f1.pk, 'language': 'aa', 'textfile': fp}
            response = self.client.post(reverse("pub-texts"), data=data, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.f1.is_shared_folder())


class TestPublisherTextList(TestCase):
    """
    urls tested:
    /api/pub/texts/?sharedfolder=123 GET
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_pub_text_list_no_auth(self):
        response = self.client.get(reverse("pub-texts"), data={'sharedfolder': 1})
        self.assertEqual(response.status_code, 401)

    def test_pub_text_list_user_is_not_a_publisher(self):
        response = self.client.get(reverse("pub-texts"), data={'sharedfolder': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)

    def test_pub_text_list_correct_empty(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        t1.delete()
        self.assertEqual(len(Text.objects.all()), 0)
        # test
        response = self.client.get(reverse("pub-texts"), data={'sharedfolder': f1.pk}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_pub_text_list_correct_with_content(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        Text.objects.create(title='test2', shared_folder=f1, textfile='test_resources/testtext2.txt')
        # test
        response = self.client.get(reverse("pub-texts"), data={'sharedfolder': f1.pk}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_pub_text_list_without_sharedfolder(self):
        response = self.client.get(reverse("pub-texts"), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_pub_text_list_folder_does_not_exist(self):
        response = self.client.get(reverse("pub-texts"), data={'sharedfolder': 99}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_pub_text_list_invalid_folder(self):
        # setup
        user3 = CustomUser.objects.get(username=USER_DATA_CORRECT_3['username'])
        f1 = Folder.objects.create(name='f1', owner=user3)
        Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("pub-texts"), data={'sharedfolder': f1.pk}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_pub_text_list_folder_is_not_shared(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.get(reverse("pub-texts"), data={'sharedfolder': f1.pk}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)


class TestPublisherListView(TestCase):
    """
    urls tested:
    /api/publishers/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        Group.objects.create(name='Publisher')
        setup_users()  # 1 and 3 are publishers, 2 and 4 are not
    
    def setUp(self):
        self.client = Client()
        login_data_2 = {"username": USER_DATA_CORRECT_2['username'],
                        "password": USER_DATA_CORRECT_2['password']}
        login_response_2 = self.client.post(reverse("login"), data=login_data_2)
        self.token_2 = 'Token ' + login_response_2.json()['token']
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_pub_list_no_auth(self):
        response = self.client.get(reverse("publishers"))
        self.assertEqual(response.status_code, 401)
    
    def test_pub_list_empty(self):
        response = self.client.get(reverse("publishers"), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
    
    def test_pub_list_with_content(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        user3 = CustomUser.objects.get(username=USER_DATA_CORRECT_3['username'])
        user2 = CustomUser.objects.get(username=USER_DATA_CORRECT_2['username'])
        for user in [user1, user3]:
            f1 = Folder.objects.create(name='f1', owner=user)
            Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
            f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("publishers"), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)


class TestPublisherDetailedView(TestCase):
    """
    urls tested:
    /api/publishers/<id>/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        Group.objects.create(name='Publisher')
        setup_users()  # 1 and 3 are publishers, 2 and 4 are not
    
    def setUp(self):
        self.client = Client()
        login_data_2 = {"username": USER_DATA_CORRECT_2['username'],
                        "password": USER_DATA_CORRECT_2['password']}
        login_response_2 = self.client.post(reverse("login"), data=login_data_2)
        self.token_2 = 'Token ' + login_response_2.json()['token']
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_pub_detail_no_auth(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        # test
        response = self.client.get(reverse("publisher-detail", args=[user1.pk]))
        self.assertEqual(response.status_code, 401)

    def test_pub_detail_correct(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        user2 = CustomUser.objects.get(username=USER_DATA_CORRECT_2['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        f2 = Folder.objects.create(name='f2', owner=user1)
        Text.objects.create(title='test2', shared_folder=f2, textfile='test_resources/testtext2.txt')
        f2.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("publisher-detail", args=[user1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['freedfolders']), 2)

    def test_pub_detail_pub_does_not_exist(self):
        response = self.client.get(reverse("publisher-detail", args=[99]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_pub_detail_invalid_publisher(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        # test
        response = self.client.get(reverse("publisher-detail", args=[user1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)


class TestSpeakerTextListView(TestCase):
    """
    urls tested:
    /api/spk/sharedfolders/<id>/
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_spk_text_list_no_auth(self):
        response = self.client.get(reverse("sharedfolder-detail", args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_spk_text_list_correct(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        user2 = CustomUser.objects.get(username=USER_DATA_CORRECT_2['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        Text.objects.create(title='test2', shared_folder=f1, textfile='test_resources/testtext2.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("sharedfolder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['texts']), 2)
    
    def test_spk_text_list_correct_empty(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        user2 = CustomUser.objects.get(username=USER_DATA_CORRECT_2['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        t1.delete()
        self.assertEqual(len(Text.objects.all()), 0)
        # test
        response = self.client.get(reverse("sharedfolder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['texts']), 0)

    def test_spk_text_list_folder_does_not_exist(self):
        response = self.client.get(reverse("sharedfolder-detail", args=[99]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_spk_text_list_invalid_folder(self):
        # setup
        user3 = CustomUser.objects.get(username=USER_DATA_CORRECT_3['username'])
        f1 = Folder.objects.create(name='f1', owner=user3)
        Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("sharedfolder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_spk_text_list_folder_is_not_shared(self):
        # setup
        user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.get(reverse("sharedfolder-detail", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)


class TestSharedFolderDetailView(TestCase):
    """
    urls tested:
    /api/sharedfolders/<id>/
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_sf_speakers_no_auth(self):
        response = self.client.get(reverse("sharedfolder-speakers", args=[1]))
        self.assertEqual(response.status_code, 401)
        response = self.client.put(reverse("sharedfolder-speakers", args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_sf_speakers_user_is_not_a_publisher(self):
        response = self.client.get(reverse("sharedfolder-speakers", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        response = self.client.put(reverse("sharedfolder-speakers", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)

    def test_sf_speakers_GET_correct_empty(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("sharedfolder-speakers", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['speakers']), 0)

    def test_sf_speakers_GET_correct_with_content(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        user4 = get_user(4)
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        f1.sharedfolder.speaker.add(user4)
        # test
        response = self.client.get(reverse("sharedfolder-speakers", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['speakers']), 2)

    def test_sf_speakers_GET_invalid_sf(self):
        # setup
        user3 = get_user(3)
        f1 = Folder.objects.create(name='f1', owner=user3)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("sharedfolder-speakers", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sf_speakers_GET_sf_does_not_exist(self):
        response = self.client.get(reverse("sharedfolder-speakers", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sf_speakers_GET_folder_is_not_shared(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.get(reverse("sharedfolder-speakers", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sf_speakers_PUT_invalid_sf(self):
        # setup
        user3 = get_user(3)
        f1 = Folder.objects.create(name='f1', owner=user3)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.put(reverse("sharedfolder-speakers", args=[f1.pk]), data={'speaker_ids': [1]}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sf_speakers_PUT_sf_does_not_exist(self):
        response = self.client.put(reverse("sharedfolder-speakers", args=[99]), data={'speaker_ids': [1]}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sf_speakers_PUT_folder_is_not_shared(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.put(reverse("sharedfolder-speakers", args=[f1.pk]), data={'speaker_ids': [1]}, content_type='application/json', HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sf_speakers_PUT_with_speaker_ids_empty(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.put(reverse("sharedfolder-speakers", args=[f1.pk]), data={'speaker_ids': []}, content_type='application/json', HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['speakers']), 0)

    def test_sf_speakers_PUT_with_speaker_ids(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        user4 = get_user(4)
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.put(reverse("sharedfolder-speakers", args=[f1.pk]), data={'speaker_ids': [user2.pk, user4.pk]}, content_type='application/json', HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['speakers']), 2)

    def test_sf_speakers_PUT_without_speaker_ids(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.put(reverse("sharedfolder-speakers", args=[f1.pk]), data={}, content_type='application/json', HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sf_speakers_PUT_speaker_ids_user_does_not_exist(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.put(reverse("sharedfolder-speakers", args=[f1.pk]), data={'speaker_ids': [99]}, content_type='application/json', HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)

    def test_sf_speakers_PUT_speaker_ids_same_user_twice(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.put(reverse("sharedfolder-speakers", args=[f1.pk]), data={'speaker_ids': [user2.pk, user2.pk]}, content_type='application/json', HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['speakers']), 1)


class TestPublisherTextDetailedView(TestCase):
    """
    urls tested:
    /api/pub/texts/<id>/
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_pub_text_no_auth(self):
        response = self.client.get(reverse("pub-text-detail", args=[1]))
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(reverse("pub-text-detail", args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_pub_text_user_is_not_a_publisher(self):
        response = self.client.get(reverse("pub-text-detail", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
        response = self.client.delete(reverse("pub-text-detail", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)

    def test_pub_text_GET_correct(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("pub-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['content'], [])

    def test_pub_text_GET_text_does_not_exist(self):
        response = self.client.get(reverse("pub-text-detail", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_pub_text_GET_invalid_text(self):
        # setup
        user3 = get_user(3)
        f1 = Folder.objects.create(name='f1', owner=user3)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("pub-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_pub_text_DEL_correct(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.delete(reverse("pub-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 204)

    def test_pub_text_DEL_text_does_not_exist(self):
        response = self.client.delete(reverse("pub-text-detail", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_pub_text_DEL_invalid_text(self):
        # setup
        user3 = get_user(3)
        f1 = Folder.objects.create(name='f1', owner=user3)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.delete(reverse("pub-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)


class TestSpeakerTextDetailedView(TestCase):
    """
    urls tested:
    /api/spk/texts/<id>/
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        Group.objects.create(name='Publisher')
        setup_users()  # 1 and 3 are publishers, 2 and 4 are not
    
    def setUp(self):
        self.client = Client()
        login_data_2 = {"username": USER_DATA_CORRECT_2['username'],
                        "password": USER_DATA_CORRECT_2['password']}
        login_response_2 = self.client.post(reverse("login"), data=login_data_2)
        self.token_2 = 'Token ' + login_response_2.json()['token']
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_spk_text_no_auth(self):
        response = self.client.get(reverse("spk-text-detail", args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_spk_text_GET_correct(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        engl = get_lang('en')
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', language=engl, shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("spk-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['content'], [])
        self.assertEqual(response.json()['language'], 'en')
        self.assertEqual(response.json()['is_right_to_left'], False)
    
    def test_spk_text_GET_correct_rtl(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        arab = get_lang('ar')
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', language=arab, shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("spk-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['content'], [])
        self.assertEqual(response.json()['language'], 'ar')
        self.assertEqual(response.json()['is_right_to_left'], True)
    
    def test_spk_text_GET_correct_without_language(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("spk-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['content'], [])
        self.assertEqual(response.json()['language'], None)
        self.assertEqual(response.json()['is_right_to_left'], False)

    def test_spk_text_GET_text_does_not_exist(self):
        response = self.client.get(reverse("spk-text-detail", args=[99]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_spk_text_GET_invalid_text(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.get(reverse("spk-text-detail", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)


class TestSpeechDataDownloadView(TestCase):
    """
    urls tested:
    api/download/<sf_id>/
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_download_no_auth(self):
        response = self.client.get(reverse("download", args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_download_user_is_not_a_publisher(self):
        response = self.client.get(reverse("download", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)

    def test_download_correct(self):
        # !!! This test relies on the fact that test_resources/testtext.txt has exactly 3 sentences !!!
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        tr1 = TextRecording.objects.create(speaker=user2, text=t1)
        SentenceRecording.objects.create(recording=tr1, index=1, audiofile='test_resources/s1.wav')
        SentenceRecording.objects.create(recording=tr1, index=2, audiofile='test_resources/s2.wav')
        SentenceRecording.objects.create(recording=tr1, index=3, audiofile='test_resources/s3.wav')
        # test
        response = self.client.get(reverse("download", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)

    def test_download_folder_does_not_exist(self):
        response = self.client.get(reverse("download", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_download_invalid_sharedfolder(self):
        # !!! This test relies on the fact that test_resources/testtext.txt has exactly 3 sentences !!!
        # setup
        user3 = get_user(3)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user3)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        tr1 = TextRecording.objects.create(speaker=user2, text=t1)
        SentenceRecording.objects.create(recording=tr1, index=1, audiofile='test_resources/s1.wav')
        SentenceRecording.objects.create(recording=tr1, index=2, audiofile='test_resources/s2.wav')
        SentenceRecording.objects.create(recording=tr1, index=3, audiofile='test_resources/s3.wav')
        # test
        response = self.client.get(reverse("download", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_download_folder_is_not_shared(self):
        # setup
        user1 = get_user(1)
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.get(reverse("download", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    # TODO should this not better be a 404 Error?
    def test_download_sharedfolder_has_no_recordings_yet(self):
        # !!! This test relies on the fact that test_resources/testtext.txt has 3 or more sentences !!!
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        tr1 = TextRecording.objects.create(speaker=user2, text=t1)
        SentenceRecording.objects.create(recording=tr1, index=1, audiofile='test_resources/s1.wav')
        SentenceRecording.objects.create(recording=tr1, index=2, audiofile='test_resources/s2.wav')
        # test
        response = self.client.get(reverse("download", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 400)


class TestSharedFolderStatsView(TestCase):
    """
    urls tested:
    /api/pub/sharedfolders/<int:pk>/stats/
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_sharedfolder_stats_no_auth(self):
        response = self.client.get(reverse("sharedfolder-stats", args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_sharedfolder_stats_user_is_not_a_publisher(self):
        response = self.client.get(reverse("sharedfolder-stats", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)

    def test_sharedfolder_stats_correct(self):
        # !!! This test relies on the fact that test_resources/testtext.txt has exactly 3 sentences !!!
        # !!! This test relies on the fact that test_resources/testtext2.txt has exactly 4 sentences !!!
        # !!! This test relies on the fact that test_resources/testtext3.txt has exactly 5 sentences !!!
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        user4 = get_user(4)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text1', shared_folder=f1, textfile='test_resources/testtext.txt')
        t2 = Text.objects.create(title='text2', shared_folder=f1, textfile='test_resources/testtext2.txt')
        t3 = Text.objects.create(title='text3', shared_folder=f1, textfile='test_resources/testtext3.txt')
        f1.sharedfolder.speaker.add(user2)
        f1.sharedfolder.speaker.add(user4)
        tr2_1 = TextRecording.objects.create(speaker=user2, text=t1)
        SentenceRecording.objects.create(recording=tr2_1, index=1, audiofile='test_resources/s1.wav')
        SentenceRecording.objects.create(recording=tr2_1, index=2, audiofile='test_resources/s2.wav')
        tr4_1 = TextRecording.objects.create(speaker=user4, text=t1)
        SentenceRecording.objects.create(recording=tr4_1, index=1, audiofile='test_resources/s1.wav')
        SentenceRecording.objects.create(recording=tr4_1, index=2, audiofile='test_resources/s2.wav')
        SentenceRecording.objects.create(recording=tr4_1, index=3, audiofile='test_resources/s3.wav')
        tr4_3 = TextRecording.objects.create(speaker=user4, text=t3)
        SentenceRecording.objects.create(recording=tr4_3, index=1, audiofile='test_resources/s1.wav')
        # test
        response = self.client.get(reverse("sharedfolder-stats", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(len(response['speakers']), 2)
        for speaker in response['speakers']:
            if speaker['name'] == user2.username:
                for text in speaker['texts']:
                    if text['title'] == 'text1':
                        self.assertEqual(text['finished'], 2)
                        self.assertEqual(text['total'], 3)
                    elif text['title'] == 'text2':
                        self.assertEqual(text['finished'], 0)
                        self.assertEqual(text['total'], 4)
                    elif text['title'] == 'text3':
                        self.assertEqual(text['finished'], 0)
                        self.assertEqual(text['total'], 5)
            elif speaker['name'] == user4.username:
                for text in speaker['texts']:
                    if text['title'] == 'text1':
                        self.assertEqual(text['finished'], 3)
                        self.assertEqual(text['total'], 3)
                    elif text['title'] == 'text2':
                        self.assertEqual(text['finished'], 0)
                        self.assertEqual(text['total'], 4)
                    elif text['title'] == 'text3':
                        self.assertEqual(text['finished'], 1)
                        self.assertEqual(text['total'], 5)

    def test_sharedfolder_stats_shared_folder_does_not_exist(self):
        response = self.client.get(reverse("sharedfolder-stats", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sharedfolder_stats_invalid_shared_folder(self):
        # setup
        user3 = get_user(3)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user3)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("sharedfolder-stats", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sharedfolder_stats_folder_is_not_shared(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        # test
        response = self.client.get(reverse("sharedfolder-stats", args=[f1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)


class TestTextStatsView(TestCase):
    """
    urls tested:
    /api/pub/texts/<int:pk>/stats/
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
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_text_stats_no_auth(self):
        response = self.client.get(reverse("text-stats", args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_text_stats_user_is_not_a_publisher(self):
        response = self.client.get(reverse("text-stats", args=[1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 403)
    
    def test_text_stats_correct(self):
        # !!! This test relies on the fact that test_resources/testtext.txt has exactly 3 sentences !!!
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        user4 = get_user(4)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='text1', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        f1.sharedfolder.speaker.add(user4)
        tr2_1 = TextRecording.objects.create(speaker=user2, text=t1)
        SentenceRecording.objects.create(recording=tr2_1, index=1, audiofile='test_resources/s1.wav')
        SentenceRecording.objects.create(recording=tr2_1, index=2, audiofile='test_resources/s2.wav')
        tr4_1 = TextRecording.objects.create(speaker=user4, text=t1)
        SentenceRecording.objects.create(recording=tr4_1, index=1, audiofile='test_resources/s1.wav')
        SentenceRecording.objects.create(recording=tr4_1, index=2, audiofile='test_resources/s2.wav')
        SentenceRecording.objects.create(recording=tr4_1, index=3, audiofile='test_resources/s3.wav')
        # test
        response = self.client.get(reverse("text-stats", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response['title'], t1.title)
        self.assertEqual(response['total'], t1.sentence_count())
        self.assertEqual(len(response['speakers']), 2)
        for speaker in response['speakers']:
            if speaker['name'] == user2.username:
                self.assertEqual(speaker['finished'], 2)
            if speaker['name'] == user4.username:
                self.assertEqual(speaker['finished'], 3)

    def test_text_stats_shared_folder_does_not_exist(self):
        response = self.client.get(reverse("text-stats", args=[99]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)
    
    def test_text_stats_invalid_shared_folder(self):
        # setup
        user3 = get_user(3)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user3)
        t1 = Text.objects.create(title='text', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("text-stats", args=[t1.pk]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)