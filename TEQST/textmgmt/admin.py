from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from admintools.models import Assignment
from . import models
import functools

def update_assignment(modeladmin, request, queryset, assignment):
        assignment.folder.add(*queryset)
        modeladmin.message_user(request, f"{queryset.count()} folders were added to the assignment {assignment}")

class SharedFolderAdmin(admin.ModelAdmin):

    model = models.SharedFolder
    fields = ('owner', 'name', 'path', 'speaker', 'listener', )
    readonly_fields = ('owner', 'path', )
    filter_horizontal = ('speaker', 'listener', )
    list_filter = ('assignments', )
    actions = ('create_assignment', )

    def path(self, obj: models.SharedFolder):
        return obj.get_readable_path()

    def has_add_permission(self, request):
        return False

    def create_assignment(self, request, queryset):
        assignment = Assignment.objects.create()
        assignment.folder.add(*queryset)
        self.message_user(request, f"{queryset.count()} folders were added to the newly created assignment {assignment}")

    def get_actions(self, request):
        actions =  super().get_actions(request)
        for assignment in Assignment.objects.all():
            actions[f"Add to assignment {assignment}"] = (
                functools.partial(update_assignment, assignment=assignment),
                f"Add to assignment {assignment}",
                f"Add to assignment {assignment}",
            )
        return actions

class TextAdmin(admin.ModelAdmin):

    model = models.Text
    fields = ('title', 'shared_folder', 'path', )
    readonly_fields = ('shared_folder', 'path', )
    list_display = ('title', 'path', )

    def folder(self, obj: models.Text):
        return mark_safe(f'<a href="{reverse("admin:shared_folder_change")}">{str(obj.shared_folder)}</a>')

    def path(self, obj: models.Text):
        return obj.shared_folder.get_readable_path()

    def has_add_permission(self, request):
        return False


admin.site.register(models.Text, TextAdmin)
admin.site.register(models.SharedFolder, SharedFolderAdmin)
