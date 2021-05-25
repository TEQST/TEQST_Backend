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
    # maybe split into
    # pub/sharedfolders/<int:pk>/texts/ for the GET Method
    # pub/texts/ for the POST method
    path('pub/texts/', views.PubTextListView.as_view(), name='pub-texts'),
    # spk/sharedfolders/<int:pk>/texts/
    path('spk/sharedfolders/<int:pk>/', views.SpkTextListView.as_view(), name='sharedfolder-detail'),
    # pub/sharedfolders/<int:pk>/speakers/
    path('sharedfolders/<int:pk>/', views.PubSharedFolderSpeakerView.as_view(), name='sharedfolder-speakers'),
    #
    path('pub/sharedfolders/<int:pk>/listeners/', views.PubSharedFolderListenerView.as_view(), name='sharedfolder-listeners'),
    # pub/texts/<int:pk>/
    path('pub/texts/<int:pk>/', views.PubTextDetailedView.as_view(), name='pub-text-detail'),
    # spk/texts/<int:pk>/
    path('spk/texts/<int:pk>/', views.SpkTextDetailedView.as_view(), name='spk-text-detail'),
    # pub/sharedfolders/<int:pk>/download/
    path('download/<int:pk>/', views.SpeechDataDownloadView.as_view(), name='download'),

    path('pub/sharedfolders/<int:pk>/stats/', views.PubSharedFolderStatsView.as_view(), name='sharedfolder-stats'),

    path('pub/texts/<int:pk>/stats/', views.PubTextStatsView.as_view(), name='text-stats'),

    path('spk/publicfolders/', views.SpkPublicFoldersView.as_view(), name='public-folders'),

    path('lstn/publishers/', views.LstnPublisherListView.as_view(), name='lstn-publishers'),

    path('lstn/publishers/<int:pk>/', views.LstnPublisherDetailedView.as_view(), name='lstn-publisher-detail'),

    path('lstn/sharedfolders/<int:pk>/texts/', views.LstnTextListView.as_view(), name='lstn-sharedfolder-detail'),

    path('lstn/texts/<int:pk>/', views.LstnTextDetailedView.as_view(), name='lstn-text-detail'),

    path('lstn/sharedfolder/<int:pk>/stats/', views.LstnSharedFolderStatsView.as_view(), name='lstn-sharedfolder-stats'),

    path('lstn/texts/<int:pk>/stats/', views.LstnTextStatsView.as_view(), name='lstn-text-stats')
]