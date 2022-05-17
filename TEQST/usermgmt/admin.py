from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from . import forms, models

class CustomUserAdmin(auth_admin.UserAdmin):
    form = forms.CustomUserChangeForm
    add_form = forms.CustomUserCreationForm
    model = models.CustomUser
    list_display = ['username']
    fieldsets = auth_admin.UserAdmin.fieldsets
    add_fieldsets = auth_admin.UserAdmin.add_fieldsets
    # omitting 'first_name', 'last_name', 'email'
    fieldsets[1][1]['fields'] = ('email', 'birth_year', 'education', 'gender', 'languages', 'country', 'accent')
    add_fieldsets[0][1]['fields'] = ('username', 'password1', 'password2', 'birth_year', 'country', 'accent')

admin.site.register(models.CustomUser, CustomUserAdmin)
admin.site.register(models.Language)
admin.site.register(models.AccentSuggestion)
