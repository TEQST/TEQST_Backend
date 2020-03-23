from django.urls import path, include
from . import views

urlpatterns = [
    # ideas for better understandable urls:
    # pub/folders/
    path('folders/', views.PubFolderListView.as_view(), name='folders'),
    # pub/folders/<int:pk>/
    path('folders/<int:pk>/', views.PubFolderDetailedView.as_view(), name='folder-detail'),
    # spk/publishers/
    path('publishers/', views.SpkPublisherListView.as_view(), name='publishers'),
    # spk/publishers/<int:pk>/
    path('publishers/<int:pk>/', views.SpkPublisherDetailedView.as_view(), name='publisher-detail'),
    # pub/texts/
    path('pub/texts/', views.PubTextListView.as_view(), name='pub-texts'),
    # spk/sharedfolders/<int:pk>/
    path('spk/sharedfolders/<int:pk>/', views.SpkTextListView.as_view(), name='sharedfolder-detail'),
    # pub/sharedfolders/<int:pk>/
    path('sharedfolders/<int:pk>/', views.PubSharedFolderSpeakerView.as_view(), name='sharedfolder-speakers'),
    # pub/texts/<int:pk>/
    path('pub/texts/<int:pk>/', views.PubTextDetailedView.as_view(), name='pub-text-detail'),
    # spk/texts/<int:pk>/
    path('spk/texts/<int:pk>/', views.SpkTextDetailedView.as_view(), name='spk-text-detail'),
    # pub/sharedfolders/<int:pk>/download/
    path('download/<int:sf>/', views.SpeechDataDownloadView.as_view(), name='download'),

    path('pub/sharedfolders/<int:pk>/stats/', views.PubSharedFolderStatsView.as_view(), name='sharedfolder-stats'),
]