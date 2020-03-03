from django.conf import settings
import os

LOCALIZATION_FOLDER = 'locale'

EDU_CHOICES = (
    ('B6', 'Less than 6 years of school'),
    ('6T12', 'Between 6 and 12 years of school'),
    ('M12', 'More than 12 years of school'),
    ('N', 'Prefer not to say')
)

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('N', 'Prefer not to say')
)

def upload_path(instance, filename):
    return os.path.join(settings.MEDIA_ROOT, LOCALIZATION_FOLDER, filename)
