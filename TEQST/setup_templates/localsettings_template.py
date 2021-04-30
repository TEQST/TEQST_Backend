import os
from .settings import *

"""
This template embodies the standard Django settings setup.

Copy this file into the TEQST directory (next to settings.py)
and rename it to 'localsettings.py'. This file is then gitignored
and you can manage local settings in this file.

You can use the "python manage.py newsecretkey" command to generate
a new random secret key to use for the SECRET_KEY setting.
"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'YOUR_SECRET_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}