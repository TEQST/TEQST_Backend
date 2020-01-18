from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserChangeForm
from .models import CustomUser, Language, Tag, Usage, Customization

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username']
    fieldsets = UserAdmin.fieldsets
    fieldsets[1][1]['fields'] = ('first_name', 'last_name', 'email', 'date_of_birth', 'education', 'gender', 'languages')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Language)
admin.site.register(Tag)
admin.site.register(Usage)
admin.site.register(Customization)