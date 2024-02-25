from django.urls import path
from . import views, browse_views

urlpatterns = [
    path('pub/folders/', views.PubFolderListView.as_view(), name='folders'),
    path('pub/folders/<int:pk>/', views.PubFolderDetailedView.as_view(), name='folder-detail'),
    path('pub/folders/delete/', views.multi_delete_folders, name='folder-delete'),
    path('spk/publishers/', views.SpkPublisherListView.as_view(), name='publishers'),
    path('spk/publishers/<int:pk>/', views.SpkPublisherDetailedView.as_view(), name='publisher-detail'),
    # maybe split into
    # pub/sharedfolders/<int:pk>/texts/ for the GET Method
    # pub/texts/ for the POST method
    path('pub/texts/', views.PubTextListView.as_view(), name='pub-texts'),
    path('pub/texts/upload-text/', views.PubTextUploadView.as_view(), name='pub-upload-text'),
    path('spk/sharedfolders/<int:pk>/texts/', views.SpkTextListView.as_view(), name='sharedfolder-detail'),
    path('pub/sharedfolders/<int:pk>/speakers/', views.PubSharedFolderSpeakerView.as_view(), name='sharedfolder-speakers'),
    path('pub/sharedfolders/<int:pk>/listeners/', views.PubSharedFolderListenerView.as_view(), name='sharedfolder-listeners'),
    path('pub/texts/<int:pk>/', views.PubTextDetailedView.as_view(), name='pub-text-detail'),
    path('pub/texts/delete/', views.multi_delete_texts, name='text-delete'),
    path('spk/texts/<int:pk>/', views.SpkTextDetailedView.as_view(), name='spk-text-detail'),
    path('pub/sharedfolders/<int:pk>/download/', views.SpeechDataDownloadView.as_view(), name='download'),
    path('pub/sharedfolders/<int:pk>/stats/', views.PubSharedFolderStatsView.as_view(), name='sharedfolder-stats'),
    path('pub/texts/<int:pk>/stats/', views.PubTextStatsView.as_view(), name='text-stats'),
    path('spk/publicfolders/', views.SpkPublicFoldersView.as_view(), name='public-folders'),
    path('spk/folders/<int:pk>/', views.SpkFolderDetailView.as_view(), name='spk-folder-detail'),
    path('spk/recent-folders/', views.SpkRecentProjectView.as_view(), name='spk-recent'),
    path('pub/listeners/', views.PubListenerPermissionView.as_view(), name='pub-listeners'),
    path('pub/listeners/<int:pk>/', views.PubListenerPermissionChangeView.as_view(), name='pub-listeners-detail'),
    path('lstn/folders/', views.LstnFolderListView.as_view(), name='lstn-folder-list'),
    path('lstn/folders/<int:pk>/', views.LstnFolderDetailView.as_view(), name='list-folder-detail'),
    path('lstn/sharedfolders/<int:pk>/texts/', views.LstnTextListView.as_view(), name='lstn-sharedfolder-detail'),
    path('lstn/texts/<int:pk>/', views.LstnTextDetailedView.as_view(), name='lstn-text-detail'),
    path('lstn/sharedfolders/<int:pk>/stats/', views.LstnSharedFolderStatsView.as_view(), name='lstn-sharedfolder-stats'),
    path('lstn/texts/<int:pk>/stats/', views.LstnTextStatsView.as_view(), name='lstn-text-stats'),  

    #Paths for browsing dowload
    path('browse/<path:path>/AudioData/<str:name>.<str:ext>', browse_views.AudioFileView.as_view(), name='browse-audio'),
    path('browse/<path:path>/AudioData/', browse_views.AudioBrowseView.as_view(), name='browse-audiofolder'),
    path('browse/<path:path>/<str:name>.<str:ext>', browse_views.SharedFolderFileView.as_view(), name='browse-file'),
    path('browse/<path:path>/', browse_views.FolderBrowseView.as_view(), name='browse-folder'),

]