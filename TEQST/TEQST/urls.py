from django.contrib import admin
from django.urls import path, include
from rest_framework import urls

admin.site.site_header = "TEQST Administration"
admin.site.site_title = "TEQST Admin"
admin.site.index_title = "App administration"


urlpatterns = [
    path('api/', include('textmgmt.urls')),
    path('api/', include('usermgmt.urls')),
    path('api/', include('recordingmgmt.urls')),
    path('admin/', admin.site.urls)
]

