from django.urls import path, include
from .views import FolderListView, FolderDetailedView, SharedFolderByPublisherView, SharedFolderDetailView, PublisherTextListView, SpeakerTextListView, PublisherTextDetailedView, SpeakerTextDetailedView


urlpatterns = [
    path('folders/', FolderListView.as_view()),
    path('folders/<int:pk>/', FolderDetailedView.as_view()),
    path('sharedfolders/', SharedFolderByPublisherView.as_view()),
    path('pub/texts/', PublisherTextListView.as_view()),
    path('spk/texts/', SpeakerTextListView.as_view()),
    path('sharedfolders/<int:pk>/', SharedFolderDetailView.as_view()),
    path('pub/texts/<int:pk>/', PublisherTextDetailedView.as_view()),
    path('spk/texts/<int:pk>/', SpeakerTextDetailedView.as_view())
]