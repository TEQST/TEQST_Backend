from django.urls import path, include
from .views import FolderListView, FolderDetailedView, SharedFolderByPublisherView, SharedFolderSpeakerView, PublisherTextListView, SpeakerTextListView, TextDetailedView


urlpatterns = [
    path('folders/', FolderListView.as_view()),
    path('folders/<int:pk>/', FolderDetailedView.as_view()),
    path('sharedfolders/', SharedFolderByPublisherView.as_view()),
    path('pub/texts/', PublisherTextListView.as_view()),
    path('spk/texts/', SpeakerTextListView.as_view()),
    path('sharedfolders/<int:pk>/', SharedFolderSpeakerView.as_view()),
    path('texts/<int:pk>/', TextDetailedView.as_view())
]