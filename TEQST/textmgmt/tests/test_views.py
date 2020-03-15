from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from usermgmt.tests.utils import *
from django.contrib.auth.models import Group
from textmgmt.models import Folder, SharedFolder, Text
from usermgmt.models import CustomUser

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
