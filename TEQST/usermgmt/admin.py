from django.contrib import admin
from django.contrib.auth import admin as auth_admin, forms as auth_forms
import more_admin_filters
from . import forms, models
from admintools.models import Assignment
from admintools import filters
import functools

def filter_rename(filter_class, title):
    class Wrapper(filter_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title = title
    return Wrapper


def update_assignment_speaker(modeladmin, request, queryset, assignment):
    assignment.speaker.add(*queryset)
    modeladmin.message_user(request, f"{queryset.count()} users were added to the assignment {assignment} as speaker")

def update_assignment_listener(modeladmin, request, queryset, assignment):
    assignment.listener.add(*queryset)
    modeladmin.message_user(request, f"{queryset.count()} users were added to the assignment {assignment} as listener")

class CustomUserAdmin(auth_admin.UserAdmin):
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password', ),
        }),
        ('Personal info', {
            'fields': ('email', 'gender', 'education', 'birth_year', 'country', 'accent', 'languages', ),
            'classes': ('collapse', ),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', ),
            'classes': ('collapse', ),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', ),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'gender', 'education', 'birth_year', 'country', 'accent', ),
        }),
    )
    form = auth_forms.UserChangeForm
    add_form = auth_forms.UserCreationForm
    change_password_form = auth_forms.AdminPasswordChangeForm
    list_display = ('username', 'country', 'accent', )
    list_filter = (
        ('speaker_assignments', filter_rename(filters.FixedMultiSelectRelatedFilter, 'speaker assignment'), ), 
        ('listener_assignments', filter_rename(filters.FixedMultiSelectRelatedFilter, 'listener assignment'), ),
        ('country', more_admin_filters.MultiSelectFilter, ),
        ('accent', more_admin_filters.MultiSelectFilter, ),
        'is_staff', 'is_superuser', 'is_active', 'groups', )
    search_fields = ('username', 'country', 'accent', )
    ordering = ('username', )
    filter_horizontal = ('groups', 'user_permissions', )
    actions = ('create_assignment_for_speakers', 'create_assignment_for_listeners', )

    def create_assignment_for_speakers(self, request, queryset):
        assignment = Assignment.objects.create()
        assignment.speaker.add(*queryset)
        self.message_user(request, f"{queryset.count()} users were added as speakers to the newly created assignment {assignment}")

    def create_assignment_for_listeners(self, request, queryset):
        assignment = Assignment.objects.create()
        assignment.listener.add(*queryset)
        self.message_user(request, f"{queryset.count()} users were added as listeners to the newly created assignment {assignment}")


    def get_actions(self, request):
        actions =  super().get_actions(request)
        for assignment in Assignment.objects.all():
            actions[f"Add to assignment {assignment} as speakers"] = (
                functools.partial(update_assignment_speaker, assignment=assignment),
                f"Add to assignment {assignment} as speakers",
                f"Add to assignment {assignment} as speakers",
            )
        for assignment in Assignment.objects.all():
            actions[f"Add to assignment {assignment} as listeners"] = (
                functools.partial(update_assignment_listener, assignment=assignment),
                f"Add to assignment {assignment} as listeners",
                f"Add to assignment {assignment} as listeners",
            )
        return actions



admin.site.register(models.CustomUser, CustomUserAdmin)
admin.site.register(models.Language)
