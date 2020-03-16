from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from usermgmt.tests.utils import *
from django.contrib.auth.models import Group
from textmgmt.models import Folder, Text
from usermgmt.models import CustomUser
from recordingmgmt.models import TextRecording, SentenceRecording

import shutil
import os
from django.core.files import File


class TestTextRecordingView(TestCase):
    """
    urls tested:
    /api/textrecordings/
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
    
    def test_textrecordings_no_auth(self):
        response = self.client.get(reverse("textrecs"), data={'text': 1})
        self.assertEqual(response.status_code, 401)
        response = self.client.post(reverse("textrecs"), data={'text': 1})
        self.assertEqual(response.status_code, 401)
    
    def test_textrecordings_GET_correct_empty(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.get(reverse("textrecs"), data={'text': t1.pk}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 204)

    def test_textrecordings_GET_correct_with_content(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        TextRecording.objects.create(speaker=user2, text=t1)
        # test
        response = self.client.get(reverse("textrecs"), data={'text': t1.pk}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_textrecordings_GET_without_text(self):
        response = self.client.get(reverse("textrecs"), data={}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_textrecordings_GET_text_does_not_exist(self):
        response = self.client.get(reverse("textrecs"), data={'text': 99}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_textrecordings_GET_invalid_text(self):
        # setup
        user1 = get_user(1)
        user4 = get_user(4)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user4)
        # test
        response = self.client.get(reverse("textrecs"), data={'text': t1.pk}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_textrecordings_POST_correct(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.post(reverse("textrecs"), data={'text': t1.pk, 'TTS_permission': True, 'SR_permission': True}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 201)

    def test_textrecordings_POST_textrecording_already_exists(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        TextRecording.objects.create(speaker=user2, text=t1)
        # test
        response = self.client.post(reverse("textrecs"), data={'text': t1.pk, 'TTS_permission': True, 'SR_permission': True}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_textrecordings_POST_without_text(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.post(reverse("textrecs"), data={'TTS_permission': True, 'SR_permission': True}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_textrecordings_POST_text_does_not_exist(self):
        response = self.client.post(reverse("textrecs"), data={'text': 99, 'TTS_permission': True, 'SR_permission': True}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_textrecordings_POST_invalid_text(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        # test
        response = self.client.post(reverse("textrecs"), data={'text': t1.pk, 'TTS_permission': True, 'SR_permission': True}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_textrecordings_POST_without_TTS(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.post(reverse("textrecs"), data={'text': t1.pk, 'SR_permission': True}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 201)

    def test_textrecordings_POST_without_SR(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.post(reverse("textrecs"), data={'text': t1.pk, 'TTS_permission': True}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 201)

    def test_textrecordings_POST_no_TTS_no_SR(self):
        # setup
        user1 = get_user(1)
        user2 = get_user(2)
        f1 = Folder.objects.create(name='f1', owner=user1)
        t1 = Text.objects.create(title='test', shared_folder=f1, textfile='test_resources/testtext.txt')
        f1.sharedfolder.speaker.add(user2)
        # test
        response = self.client.post(reverse("textrecs"), data={'text': t1.pk, 'TTS_permission': False, 'SR_permission': False}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)