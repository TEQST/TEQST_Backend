from django.urls import path, include
from . import views

urlpatterns = [
    path('folders/', views.PubFolderListView.as_view(), name='folders'),
    path('folders/<int:pk>/', views.PubFolderDetailedView.as_view(), name='folder-detail'),
    path('publishers/', views.SpkPublisherListView.as_view(), name='publishers'),
    path('publishers/<int:pk>/', views.SpkPublisherDetailedView.as_view(), name='publisher-detail'),
    path('pub/texts/', views.PubTextListView.as_view(), name='pub-texts'),
    path('spk/sharedfolders/<int:pk>/', views.SpkTextListView.as_view(), name='sharedfolder-detail'),
    path('sharedfolders/<int:pk>/', views.PubSharedFolderSpeakerView.as_view(), name='sharedfolder-speakers'),
    path('pub/texts/<int:pk>/', views.PubTextDetailedView.as_view(), name='pub-text-detail'),
    path('spk/texts/<int:pk>/', views.SpkTextDetailedView.as_view(), name='spk-text-detail'),
    path('download/<int:sf>/', views.SpeechDataDownloadView.as_view(), name='download')
]