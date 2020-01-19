from django.urls import path, include
from .views import FolderListView, FolderDetailedView, SharedFolderByPublisherView, SharedFolderSpeakerView, TextListView, TextDetailedView


urlpatterns = [
    path('folders/', FolderListView.as_view()),
    path('folders/<int:pk>/', FolderDetailedView.as_view()),
    #path('publishers/', )
    path('publishers/<int:pub_pk>/sharedfolders/', SharedFolderByPublisherView.as_view()),
    path('texts/', TextListView.as_view()),  # maybe path('sharedfolders/:id/texts/')
    path('sharedfolders/<int:pk>/speakers/', SharedFolderSpeakerView.as_view()),
    path('texts/<int:pk>/', TextDetailedView.as_view())
]