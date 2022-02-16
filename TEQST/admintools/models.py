from django.db import models
from django.contrib import auth
from textmgmt import models as text_models

# Create your models here.
class Assignment(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    speaker = models.ManyToManyField(auth.get_user_model(), blank=True, related_name='speaker_assignments')
    folder = models.ManyToManyField(text_models.SharedFolder, blank=True, related_name='assignments')
    listener = models.ManyToManyField(auth.get_user_model(), blank=True, related_name='listener_assignments')
    apply = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.created.strftime('%d.%m.%Y %H:%M:%S')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.apply:
            for folder in self.folder.all():
                folder.speaker.add(*self.speaker.all())
                folder.listener.add(*self.listener.all())
