from django.urls import path, include
from .views import TextRecordingView, SentenceRecordingCreateView, SentenceRecordingUpdateView, SentenceRecordingRetrieveUpdateView

urlpatterns = [
    path('textrecordings/', TextRecordingView.as_view(), name='textrecs'),
    path('sentencerecordings/', SentenceRecordingCreateView.as_view(), name='sentencerecs-create'),
    path('sentencerecordings/<int:rec>/', SentenceRecordingUpdateView.as_view(), name='sentencerecs-detail'),
    path('sentencerecordings/<int:tr_id>/<int:index>', SentenceRecordingRetrieveUpdateView.as_view(), name='sentencerecs-retrieveupdate')
]