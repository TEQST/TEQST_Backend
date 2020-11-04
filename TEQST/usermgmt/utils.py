from django.conf import settings

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

ACCENT_DEFAULT = 'Not specified'

def upload_path(instance, filename):
    return Path(LOCALIZATION_FOLDER)/filename
