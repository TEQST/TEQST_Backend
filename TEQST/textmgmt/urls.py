from django.urls import path, include
from .views import FolderListView, FolderDetailedView, SharedFolderView, TextListView, TextDetailedView


urlpatterns = [
    path('folders/', FolderListView.as_view()),
    path('folders/<int:pk>/', FolderDetailedView.as_view()),
    path('sharedfolders/', SharedFolderView.as_view()),
    path('texts/', TextListView.as_view()),
    path('texts/<int:pk>/', TextDetailedView.as_view())
]