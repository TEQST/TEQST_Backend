from django.urls import path, include
from . import views

urlpatterns = [
    path('folders/', views.FolderListView.as_view(), name='folders'),
    path('folders/<int:pk>/', views.FolderDetailedView.as_view(), name='folder-detail'),
    path('publishers/', views.PublisherListView.as_view(), name='publishers'),
    path('publishers/<int:pk>/', views.PublisherDetailedView.as_view(), name='publisher-detail'),
    path('pub/texts/', views.PublisherTextListView.as_view(), name='pub-texts'),
    path('spk/sharedfolders/<int:pk>/', views.SpeakerTextListView.as_view(), name='sharedfolder-detail'),
    path('sharedfolders/<int:pk>/', views.SharedFolderDetailView.as_view(), name='sharedfolder-speakers'),
    path('pub/texts/<int:pk>/', views.PublisherTextDetailedView.as_view(), name='pub-text-detail'),
    path('spk/texts/<int:pk>/', views.SpeakerTextDetailedView.as_view(), name='spk-text-detail'),
    path('download/<int:sf>/', views.SpeechDataDownloadView.as_view(), name='download')
]