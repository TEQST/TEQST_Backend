from django.urls import path, include
from .views import TextRecordingView, SentenceRecordingCreateView, SentenceRecordingUpdateView, SentenceRecordingRetrieveUpdateView

urlpatterns = [
    # ideas for better understandable urls:
    # spk/textrecordings/
    path('textrecordings/', TextRecordingView.as_view(), name='textrecs'),
    # spk/sentencerecordings/
    path('sentencerecordings/', SentenceRecordingCreateView.as_view(), name='sentencerecs-create'),
    #
    path('sentencerecordings/<int:rec>/', SentenceRecordingUpdateView.as_view(), name='sentencerecs-detail'),
    # spk/...
    path('sentencerecordings/<int:tr_id>/<int:index>', SentenceRecordingRetrieveUpdateView.as_view(), name='sentencerecs-retrieveupdate')
]