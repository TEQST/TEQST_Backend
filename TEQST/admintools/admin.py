from django.contrib import admin
from . import models

class AssignmentAdmin(admin.ModelAdmin):

    readonly_fields = ('created', 'applied', 'last_apply', )
    filter_horizontal = ('speaker', 'listener', 'folder', )

    fieldsets = (
        (None, {
            'fields': ('apply_now', 'applied', 'last_apply', 'name', 'created', ),
        }),
        ('Selected', {
            'fields': ('speaker', 'listener', 'folder', ),
            'classes': ('collapse', ),
        }),
    )

    list_display = ('name', 'created_at', 'applied', 'apply_now', 'last_applied_at')
    list_display_links = ('name', 'created_at', )
    list_editable = ('apply_now', )

    def created_at(self, obj):
        return obj.created_str

    def last_applied_at(self, obj):
        return obj.last_apply_str


admin.site.register(models.Assignment, AssignmentAdmin)