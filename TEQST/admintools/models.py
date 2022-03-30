from django.db import models
from django.contrib import auth
from textmgmt import models as text_models
import datetime

# Create your models here.
class Assignment(models.Model):
    name = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    speaker = models.ManyToManyField(auth.get_user_model(), blank=True, related_name='speaker_assignments')
    folder = models.ManyToManyField(text_models.SharedFolder, blank=True, related_name='assignments')
    listener = models.ManyToManyField(auth.get_user_model(), blank=True, related_name='listener_assignments')
    apply_now = models.BooleanField(default=False, help_text='Apply this assignment now')
    applied = models.BooleanField(default=False, editable=False, help_text='Has this assignment previously been applied')
    last_apply = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.created_str})"
        else:
            return self.created_str

    @property
    def created_str(self):
        return self.created.strftime('%d.%m.%Y %H:%M:%S')

    @property
    def last_apply_str(self):
        if self.last_apply:
            return self.last_apply.strftime('%d.%m.%Y %H:%M:%S')
        else:
            return ''

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.apply_now:
            for folder in self.folder.all():
                folder.speaker.add(*self.speaker.all())
                folder.listener.add(*self.listener.all())
            self.applied = True
            self.apply_now = False
            self.last_apply = datetime.datetime.now()
        super().save()
