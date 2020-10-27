from django.test import TestCase
from django.conf import settings
from textmgmt.models import Text, Folder
from usermgmt.models import CustomUser
from usermgmt.tests.utils import *
import shutil

class TestText(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_languages_users_groups()

    def setUp(self):
        self.user1 = CustomUser.objects.get(username=USER_DATA_CORRECT_1['username'])
        self.folder = Folder.objects.create(name='f1', owner=self.user1)
        self.folder = self.folder.make_shared_folder()
    
    def tearDown(self):
        delete_all_users()
    
    def test_get_content_only_single_lines_one_newline(self):
        # setup
        filepath = 'test_resources/all_single_lines_1_newline.txt'
        text = Text.objects.create(title='t1', shared_folder=self.folder, textfile=filepath)
        # test
        self.assertEqual(text.sentence_count(), 4)
    
    def test_get_content_only_single_lines_five_newlines(self):
        # setup
        filepath = 'test_resources/all_single_lines_5_newlines.txt'
        text = Text.objects.create(title='t1', shared_folder=self.folder, textfile=filepath)
        # test
        self.assertEqual(text.sentence_count(), 4)

    def test_get_content_only_single_lines_no_newlines(self):
        # setup
        filepath = 'test_resources/all_single_lines_no_newlines.txt'
        text = Text.objects.create(title='t1', shared_folder=self.folder, textfile=filepath)
        # test
        self.assertEqual(text.sentence_count(), 4)
    
    def test_get_content_5_nls_only_single_lines_1_nl(self):
        # setup
        filepath = 'test_resources/5_nls_all_single_lines_1_nl.txt'
        text = Text.objects.create(title='t1', shared_folder=self.folder, textfile=filepath)
        # test
        self.assertEqual(text.sentence_count(), 4)
    
    def test_get_content_only_single_lines_various_nls(self):
        # setup
        filepath = 'test_resources/all_single_lines_various_nls.txt'
        text = Text.objects.create(title='t1', shared_folder=self.folder, textfile=filepath)
        # test
        self.assertEqual(text.sentence_count(), 4)
    
    def test_get_content_various_lines_various_nls(self):
        # setup
        filepath = 'test_resources/various_lines_various_nls.txt'
        text = Text.objects.create(title='t1', shared_folder=self.folder, textfile=filepath)
        # test
        self.assertEqual(text.sentence_count(), 5)