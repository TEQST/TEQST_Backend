from django.contrib import admin
from . import models

class AssignmentAdmin(admin.ModelAdmin):

    readonly_fields = ('created', )
    filter_horizontal = ('speaker', 'listener', 'folder', )

    fieldsets = (
        (None, {
            'fields': ('apply', 'created', ),
        }),
        ('Selected', {
            'fields': ('speaker', 'listener', 'folder', ),
            'classes': ('collapse', ),
        }),
    )

    list_display = ('created_at', 'applied', )

    def applied(self, obj):
        return obj.apply

    def created_at(self, obj):
        return obj.__str__()

    applied.boolean = True

admin.site.register(models.Assignment, AssignmentAdmin)