from django.contrib import admin
from .models import Folder, SharedFolder, Text

# Register your models here.
admin.site.register(Folder)
admin.site.register(SharedFolder)
admin.site.register(Text)