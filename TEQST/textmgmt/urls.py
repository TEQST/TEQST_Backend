from django.urls import path, include
from .views import FolderListView, FolderDetailedView, SharedFolderByPublisherView, PublisherDetailedView, SharedFolderDetailView, PublisherTextListView, SpeakerTextListView, PublisherTextDetailedView, SpeakerTextDetailedView, PublisherListView


urlpatterns = [
    path('folders/', FolderListView.as_view()),
    path('folders/<int:pk>/', FolderDetailedView.as_view()),

    path('publishers/', PublisherListView.as_view()),

    # path('sharedfolders/', SharedFolderByPublisherView.as_view()),  # shows the SFs owned by a publisher
    path('publishers/<int:pk>/', PublisherDetailedView.as_view()),

    path('pub/texts/', PublisherTextListView.as_view()),

    # path('spk/texts/', SpeakerTextListView.as_view()),  # shows the texts in a sharedfolder
    path('spk/sharedfolders/<int:pk>/', SpeakerTextListView.as_view()),  # this is the correct one

    path('sharedfolders/<int:pk>/', SharedFolderDetailView.as_view()),  # retrieve and update the speakers of a sf
    path('pub/texts/<int:pk>/', PublisherTextDetailedView.as_view()),
    path('spk/texts/<int:pk>/', SpeakerTextDetailedView.as_view())
]