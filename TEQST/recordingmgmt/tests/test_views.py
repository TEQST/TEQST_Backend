from django.test import TestCase, Client
from django.test.client import encode_multipart
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from usermgmt.tests.utils import *
from django.contrib.auth.models import Group
from textmgmt.models import Folder, Text
from usermgmt.models import CustomUser
from recordingmgmt.models import TextRecording, SentenceRecording

import shutil
import os
from django.core.files import File
from io import BytesIO


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


class TestSentenceRecordingCreateView(TestCase):
    """
    urls tested:
    /api/sentencerecordings/
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
        self.user1 = get_user(1)
        self.user2 = get_user(2)
        self.f1 = Folder.objects.create(name='f1', owner=self.user1)
        self.t1 = Text.objects.create(title='test', shared_folder=self.f1, textfile='test_resources/testtext.txt')
        self.f1.sharedfolder.speaker.add(self.user2)
        self.tr1 = TextRecording.objects.create(speaker=self.user2, text=self.t1)
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_sentencerec_create_no_auth(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'audiofile': fp, 'index': 1})
        self.assertEqual(response.status_code, 401)

    def test_sentencerec_create_correct(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'audiofile': fp, 'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 201)
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s2.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'audiofile': fp, 'index': 2}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 201)

    def test_sentencerec_create_without_recording(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s2.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'audiofile': fp, 'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_sentencerec_create_recording_does_not_exist(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': 99, 'audiofile': fp, 'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_sentencerec_create_invalid_recording(self):
        # setup
        user4 = get_user(4)
        self.f1.sharedfolder.speaker.add(user4)
        tr2 = TextRecording.objects.create(speaker=user4, text=self.t1)
        # test
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': tr2.pk, 'audiofile': fp, 'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_sentencerec_create_without_audiofile(self):
        response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_sentencerec_create_without_index(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'audiofile': fp}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_sentencerec_create_index_too_big(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'audiofile': fp, 'index': 2}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_sentencerec_create_index_too_small(self):
        # setup
        user2 = get_user(2)
        SentenceRecording.objects.create(recording=self.tr1, index=1, audiofile='test_resources/s1.wav')
        # test
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s2.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'audiofile': fp, 'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)

    def test_sentencerec_create_index_negative(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s2.wav'), 'rb') as fp:
            response = self.client.post(reverse("sentencerecs-create"), data={'recording': self.tr1.pk, 'audiofile': fp, 'index': -1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 400)


class TestSentenceRecordingUpdateView(TestCase):
    """
    urls tested:
    /api/sentencerecordings/<trec_id>/
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
        login_data_3 = {"username": USER_DATA_CORRECT_3['username'],
                        "password": USER_DATA_CORRECT_3['password']}
        login_response_3 = self.client.post(reverse("login"), data=login_data_3)
        self.token_3 = 'Token ' + login_response_3.json()['token']
        self.user1 = get_user(1)
        self.user2 = get_user(2)
        self.f1 = Folder.objects.create(name='f1', owner=self.user1)
        self.t1 = Text.objects.create(title='test', shared_folder=self.f1, textfile='test_resources/testtext.txt')
        self.f1.sharedfolder.speaker.add(self.user2)
        self.tr1 = TextRecording.objects.create(speaker=self.user2, text=self.t1)
        self.sc1 = SentenceRecording.objects.create(recording=self.tr1, index=1, audiofile='test_resources/s1.wav')
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_sentencerec_detail_no_auth(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'index': 1})
        self.assertEqual(response.status_code, 401)
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.put(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'audiofile': fp, 'index': 1})
        self.assertEqual(response.status_code, 401)

    # GET speaker related

    def test_sentencerec_detail_GET_correct(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)

    def test_sentencerec_detail_GET_trec_does_not_exist(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[99]), data={'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_GET_invalid_trec(self):
        # setup
        user4 = get_user(4)
        self.f1.sharedfolder.speaker.add(user4)
        tr2 = TextRecording.objects.create(speaker=user4, text=self.t1)
        sr2 = SentenceRecording.objects.create(recording=tr2, index=1, audiofile='test_resources/s1.wav')
        # test
        response = self.client.get(reverse("sentencerecs-detail", args=[tr2.pk]), data={'index': 1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_GET_without_index(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_GET_index_too_big(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'index': 2}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_GET_index_negative(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'index': 0}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'index': -1}, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)
    
    # GET publisher related

    def test_sentencerec_detail_pub_GET_correct(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'index': 1}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
    
    def test_sentencerec_detail_pub_GET_invalid_trec(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[self.tr1.pk]), data={'index': 1}, HTTP_AUTHORIZATION=self.token_3)
        self.assertEqual(response.status_code, 404)
    
    def test_sentencerec_detail_pub_GET_trec_does_not_exist(self):
        response = self.client.get(reverse("sentencerecs-detail", args=[99]), data={'index': 1}, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    # PUT speaker related

    def test_sentencerec_detail_PUT_correct(self):
        pass   

    def test_sentencerec_detail_PUT_trec_does_not_exist(self):
        pass

    def test_sentencerec_detail_PUT_invalid_trec(self):
        pass

    def test_sentencerec_detail_PUT_without_index(self):
        pass

    def test_sentencerec_detail_PUT_index_too_big(self):
        pass

    def test_sentencerec_detail_PUT_index_negative(self):
        pass


class TestSentenceRecordingRetrieveUpdateView(TestCase):
    """
    urls tested:
    /api/sentencerecordings/<trec_id>/<index>/
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
        login_data_3 = {"username": USER_DATA_CORRECT_3['username'],
                        "password": USER_DATA_CORRECT_3['password']}
        login_response_3 = self.client.post(reverse("login"), data=login_data_3)
        self.token_3 = 'Token ' + login_response_3.json()['token']
        self.user1 = get_user(1)
        self.user2 = get_user(2)
        self.f1 = Folder.objects.create(name='f1', owner=self.user1)
        self.t1 = Text.objects.create(title='test', shared_folder=self.f1, textfile='test_resources/testtext.txt')
        self.f1.sharedfolder.speaker.add(self.user2)
        self.tr1 = TextRecording.objects.create(speaker=self.user2, text=self.t1)
        self.sc1 = SentenceRecording.objects.create(recording=self.tr1, index=1, audiofile='test_resources/s1.wav')
    
    def tearDown(self):
        for user in [USER_DATA_CORRECT_1, USER_DATA_CORRECT_3]:
            path = settings.MEDIA_ROOT + '/' + user['username'] + '/'
            if (os.path.exists(path)):
                shutil.rmtree(path)
    
    def test_sentencerec_detail_no_auth(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 1]))
        self.assertEqual(response.status_code, 401)
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            response = self.client.put(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 1]), data={'audiofile': fp})
        self.assertEqual(response.status_code, 401)

    # GET speaker related

    def test_sentencerec_detail_GET_correct(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)

    def test_sentencerec_detail_GET_trec_does_not_exist(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[99, 1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_GET_invalid_trec(self):
        # setup
        user4 = get_user(4)
        self.f1.sharedfolder.speaker.add(user4)
        tr2 = TextRecording.objects.create(speaker=user4, text=self.t1)
        sr2 = SentenceRecording.objects.create(recording=tr2, index=1, audiofile='test_resources/s1.wav')
        # test
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[tr2.pk, 1]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_GET_index_too_big(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 2]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_GET_index_is_zero(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 0]), HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)
    
    # GET publisher related

    def test_sentencerec_detail_pub_GET_correct(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 1]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 200)
    
    def test_sentencerec_detail_pub_GET_invalid_trec(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 1]), HTTP_AUTHORIZATION=self.token_3)
        self.assertEqual(response.status_code, 404)
    
    def test_sentencerec_detail_pub_GET_trec_does_not_exist(self):
        response = self.client.get(reverse("sentencerecs-retrieveupdate", args=[99, 1]), HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    # PUT speaker related

    def test_sentencerec_detail_PUT_correct(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            data = {'audiofile': fp}
            content = encode_multipart('mybndry', data)
            content_type = 'multipart/form-data; boundary=mybndry'
            response = self.client.put(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 1]), data=content, content_type=content_type, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 200)
    
    def test_sentencerec_detail_PUT_user_is_publisher_of_text(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            data = {'audiofile': fp}
            content = encode_multipart('mybndry', data)
            content_type = 'multipart/form-data; boundary=mybndry'
            response = self.client.put(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 1]), data=content, content_type=content_type, HTTP_AUTHORIZATION=self.token_1)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_PUT_trec_does_not_exist(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            data = {'audiofile': fp}
            content = encode_multipart('mybndry', data)
            content_type = 'multipart/form-data; boundary=mybndry'
            response = self.client.put(reverse("sentencerecs-retrieveupdate", args=[99, 1]), data=content, content_type=content_type, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_PUT_invalid_trec(self):
        # setup
        user4 = get_user(4)
        self.f1.sharedfolder.speaker.add(user4)
        tr2 = TextRecording.objects.create(speaker=user4, text=self.t1)
        sr2 = SentenceRecording.objects.create(recording=tr2, index=1, audiofile='test_resources/s1.wav')
        # test
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            data = {'audiofile': fp}
            content = encode_multipart('mybndry', data)
            content_type = 'multipart/form-data; boundary=mybndry'
            response = self.client.put(reverse("sentencerecs-retrieveupdate", args=[tr2.pk, 1]), data=content, content_type=content_type, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_PUT_index_too_big(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            data = {'audiofile': fp}
            content = encode_multipart('mybndry', data)
            content_type = 'multipart/form-data; boundary=mybndry'
            response = self.client.put(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 2]), data=content, content_type=content_type, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)

    def test_sentencerec_detail_PUT_index_is_zero(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'test_resources/s1.wav'), 'rb') as fp:
            data = {'audiofile': fp}
            content = encode_multipart('mybndry', data)
            content_type = 'multipart/form-data; boundary=mybndry'
            response = self.client.put(reverse("sentencerecs-retrieveupdate", args=[self.tr1.pk, 0]), data=content, content_type=content_type, HTTP_AUTHORIZATION=self.token_2)
        self.assertEqual(response.status_code, 404)