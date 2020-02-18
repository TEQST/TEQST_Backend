from django.urls import path, include
from . import views

urlpatterns = [
    path('folders/', views.FolderListView.as_view()),
    path('folders/<int:pk>/', views.FolderDetailedView.as_view()),
    path('publishers/', views.PublisherListView.as_view()),
    path('publishers/<int:pk>/', views.PublisherDetailedView.as_view()),
    path('pub/texts/', views.PublisherTextListView.as_view()),
    path('spk/sharedfolders/<int:pk>/', views.SpeakerTextListView.as_view()),
    path('sharedfolders/<int:pk>/', views.SharedFolderDetailView.as_view()),
    path('pub/texts/<int:pk>/', views.PublisherTextDetailedView.as_view()),
    path('spk/texts/<int:pk>/', views.SpeakerTextDetailedView.as_view()),
    path('download/<int:sf>/', views.SpeechDataDownloadView.as_view())
]