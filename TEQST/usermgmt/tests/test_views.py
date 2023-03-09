from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from usermgmt.models import Language, CustomUser
from usermgmt.tests.utils import *
from rest_framework.authtoken.models import Token

from datetime import date


class TestRegistration(TestCase):
    """
    urls tested:
    /api/auth/register/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()

    def setUp(self):
        self.client = Client()

    def test_user_registration_all_correct(self):
        response = self.client.post(reverse("register"), data=USER_DATA_CORRECT_1)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        self.assertEqual(user.username, USER_DATA_CORRECT_1['username'])
        self.assertEqual(user.education, USER_DATA_CORRECT_1['education'])
        self.assertEqual(user.gender, USER_DATA_CORRECT_1['gender'])
        self.assertEqual(user.birth_year, USER_DATA_CORRECT_1['birth_year'])
        self.assertTrue(Language.objects.get(short='en') in user.languages.all())
        self.assertTrue(Language.objects.get(short='fr') in user.languages.all())
        self.assertEqual(user.languages.count(), 2)
        self.assertEqual(user.country, USER_DATA_CORRECT_1['country'])


    def test_user_registration_username_exists(self):
        # setup
        self.client.post(reverse("register"), data=USER_DATA_CORRECT_1)
        # test
        response = self.client.post(reverse("register"), data=USER_DATA_CORRECT_1)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_username(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data.pop('username')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_invalid_username(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data['username'] = 'har ry'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_username_not_allowed(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data['username'] = 'locale'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_password(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data.pop('password')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)

    def test_user_registration_without_education(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data.pop('education')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.education, 'N')
    
    def test_user_registration_invalid_education(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data['education'] = 'ABC'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_gender(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data.pop('gender')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.gender, 'N')
    
    def test_user_registration_invalid_gender(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data['gender'] = 'A'
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_without_birth_year(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data.pop('birth_year')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_invalid_birth_year_small(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data['birth_year'] = 1899
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_user_registration_invalid_birth_year_big(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data['birth_year'] = date.today().year + 1
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 400)
    
    # TODO rethink the whole language thing

    def test_user_registration_without_language_ids(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data.pop('language_ids')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.languages.count(), 0)
    
    def test_user_registration_without_country(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data.pop('country')
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.country, None)
    
    def test_user_registration_accent_is_empty_string(self):
        # setup
        user_data = USER_DATA_CORRECT_1.copy()
        user_data['accent'] = ''
        # test
        response = self.client.post(reverse("register"), data=user_data)
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username=user_data['username'])
        self.assertEqual(user.accent, 'Not specified')


class TestAuthentication(TestCase):
    """
    urls tested:
    /api/auth/login/
    /api/auth/logout/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        Group.objects.create(name='Publisher')
        setup_user(USER_DATA_CORRECT_1)
        
    def setUp(self):
        self.client = Client()
    
    def test_setupclass_works(self):
        user = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(user.username, USER_DATA_CORRECT_1['username'])

    def test_login_all_correct(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username'],
                      "password": USER_DATA_CORRECT_1['password']}
        # test
        response = self.client.post(reverse("login"), data=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('token' in response.json().keys())
        self.assertTrue('user' in response.json().keys())
    
    def test_login_no_username(self):
        # setup
        login_data = {"password": USER_DATA_CORRECT_1['password']}
        # test
        response = self.client.post(reverse("login"), data=login_data)
        self.assertEqual(response.status_code, 400)
    
    def test_login_username_does_not_exist(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username'] + 'f',
                      "password": USER_DATA_CORRECT_1['password']}
        # test
        response = self.client.post(reverse("login"), data=login_data)
        self.assertEqual(response.status_code, 400)
    
    def test_login_no_password(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username']}
        # test
        response = self.client.post(reverse("login"), data=login_data)
        self.assertEqual(response.status_code, 400)
    
    def test_login_wrong_password(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username'],
                      "password": USER_DATA_CORRECT_1['password'] + 'f'}
        # test
        response = self.client.post(reverse("login"), data=login_data)
        self.assertEqual(response.status_code, 400)
    
    def test_logout_correct(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username'],
                      "password": USER_DATA_CORRECT_1['password']}
        login_response = self.client.post(reverse("login"), data=login_data)
        token = login_response.json()['token']
        # test
        self.assertTrue(Token.objects.get(key=token))
        # any header needs a prefix of 'HTTP_'
        response = self.client.post(reverse("logout"), HTTP_AUTHORIZATION='Token ' + token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Token.objects.filter(key=token).exists())
    
    def test_logout_no_auth(self):
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 401)
    
    def test_logout_wrong_token(self):
        response = self.client.post(reverse("logout"), HTTP_AUTHORIZATION='Token abcdefgh12345678')
        self.assertEqual(response.status_code, 401)
    
    def test_login_logout_login(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username'],
                      "password": USER_DATA_CORRECT_1['password']}
        login_response = self.client.post(reverse("login"), data=login_data)
        token = login_response.json()['token']
        self.client.post(reverse("logout"), HTTP_AUTHORIZATION='Token ' + token)
        # test
        new_login_response = self.client.post(reverse("login"), data=login_data)
        new_token = new_login_response.json()['token']
        self.assertNotEqual(token, new_token)

    def test_login_login(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username'],
                      "password": USER_DATA_CORRECT_1['password']}
        login_response = self.client.post(reverse("login"), data=login_data)
        token = login_response.json()['token']
        # test
        new_login_response = self.client.post(reverse("login"), data=login_data)
        new_token = new_login_response.json()['token']
        self.assertEqual(token, new_token)


class TestLanguageViews(TestCase):
    """
    urls tested:
    /api/langs/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        
    def setUp(self):
        self.client = Client()
    
    def test_langs(self):
        response = self.client.get(reverse("langs")).json()
        self.assertEqual(len(response), 5)


class TestUserList(TestCase):
    """
    urls tested:
    /api/users/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_languages_users_groups()
        
    def setUp(self):
        self.client = Client()
    
    def test_setupclass_works(self):
        self.assertEqual(CustomUser.objects.count(), 4)
        self.assertEqual(Group.objects.get(name='Publisher').user_set.count(), 2)
    
    def test_users_all_correct(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_1['username'],
                      "password": USER_DATA_CORRECT_1['password']}
        login_response = self.client.post(reverse("login"), data=login_data)
        token = login_response.json()['token']
        # test
        response = self.client.get(reverse("users"), HTTP_AUTHORIZATION='Token ' + token)
        self.assertEqual(response.status_code, 200)
    
    def test_users_user_is_not_a_publisher(self):
        # setup
        login_data = {"username": USER_DATA_CORRECT_2['username'],
                      "password": USER_DATA_CORRECT_2['password']}
        login_response = self.client.post(reverse("login"), data=login_data)
        token = login_response.json()['token']
        # test
        response = self.client.get(reverse("users"), HTTP_AUTHORIZATION='Token ' + token)
        self.assertEqual(response.status_code, 403)
    
    def test_uses_no_auth(self):
        response = self.client.get(reverse("users"))
        self.assertEqual(response.status_code, 401)
    
    def test_users_wrong_token(self):
        response = self.client.post(reverse("users"), HTTP_AUTHORIZATION='Token abcdefgh12345678')
        self.assertEqual(response.status_code, 401)


class TestUser(TestCase):
    """
    urls tested:
    /api/user/
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_languages()
        Group.objects.create(name='Publisher')
        setup_user(USER_DATA_CORRECT_1)
        
    def setUp(self):
        self.client = Client()
        login_data = {"username": USER_DATA_CORRECT_1['username'],
                      "password": USER_DATA_CORRECT_1['password']}
        login_response = self.client.post(reverse("login"), data=login_data)
        self.token = 'Token ' + login_response.json()['token']
    
    def test_setupclass_works(self):
        self.assertEqual(CustomUser.objects.count(), 1)
    
    def test_user_no_auth(self):
        response = self.client.get(reverse("user"))
        self.assertEqual(response.status_code, 401)
        response = self.client.put(reverse("user"))
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(reverse("user"))
        self.assertEqual(response.status_code, 401)

    def test_user_GET(self):
        response = self.client.get(reverse("user"), HTTP_AUTHORIZATION=self.token)
        user = response.json()
        self.assertEqual(user['username'], USER_DATA_CORRECT_1['username'])
        self.assertEqual(user['education'], USER_DATA_CORRECT_1['education'])
        self.assertEqual(user['gender'], USER_DATA_CORRECT_1['gender'])
        self.assertEqual(user['birth_year'], USER_DATA_CORRECT_1['birth_year'])
        self.assertEqual(len(user['languages']), 2)
        self.assertEqual(user['country'], USER_DATA_CORRECT_1['country'])
    
    def test_user_DELETE(self):
        response = self.client.delete(reverse("user"), HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 204)
    
    def test_user_PUT_all_correct(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data['birth_year'] = 1970
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['birth_year'], 1970)

    def test_user_PUT_without_education(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data.pop('education')
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        self.assertEqual(user.education, USER_DATA_CORRECT_1['education'])
    
    def test_user_PUT_invalid_education(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data['education'] = 'ABC'
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 400)
    
    def test_user_PUT_without_gender(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data.pop('gender')
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        self.assertEqual(user.gender, USER_DATA_CORRECT_1['gender'])
    
    def test_user_PUT_invalid_gender(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data['gender'] = 'A'
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 400)
    
    def test_user_PUT_without_birth_year(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data.pop('birth_year')
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 400)
    
    def test_user_PUT_invalid_birth_year_small(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data['birth_year'] = 1899
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 400)
    
    def test_user_PUT_invalid_birth_year_big(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data['birth_year'] = date.today().year + 1
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 400)
    
    # TODO rethink the whole language thing

    def test_user_PUT_without_language_ids(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data.pop('language_ids')
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 400)
        #user = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        #self.assertEqual(user.languages.count(), 0)
    
    def test_user_PUT_without_country(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data.pop('country')
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        self.assertEqual(user.country, USER_DATA_CORRECT_1['country'])
    
    def test_user_PUT_accent_is_empty_string(self):
        # setup
        put_data = USER_DATA_CORRECT_1.copy()
        put_data.pop('username')
        put_data['accent'] = ''
        # test
        response = self.client.put(reverse("user"), data=put_data, content_type='application/json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        self.assertEqual(user.accent, 'Not specified')
