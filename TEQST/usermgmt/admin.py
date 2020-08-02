from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser, Language, Tag, Usage, Customization

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = ['username']
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets
    # omitting 'first_name', 'last_name', 'email'
    fieldsets[1][1]['fields'] = ('email', 'birth_year', 'education', 'gender', 'languages', 'country', 'accent')
    add_fieldsets[0][1]['fields'] = ('username', 'birth_year', 'password1', 'password2')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Language)
