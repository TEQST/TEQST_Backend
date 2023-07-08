from django.urls import path
from . import views

urlpatterns = [
    path('spk/textrecordings/', views.TextRecordingView.as_view(), name='textrecs'),
    path('spk/sentencerecordings/', views.SentenceRecordingCreateView.as_view(), name='sentencerecs-create'),
    path('spk/sentencerecordings/<int:rec>/', views.SentenceRecordingUpdateView.as_view(), name='sentencerecs-detail'),
    path('spk/sentencerecordings/<int:tr_id>/<int:index>/', views.SentenceRecordingRetrieveUpdateView.as_view(), name='sentencerecs-retrieveupdate')
]