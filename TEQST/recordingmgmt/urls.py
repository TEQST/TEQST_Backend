from django.urls import path
from . import views

urlpatterns = [
    # ideas for better understandable urls:
    # spk/textrecordings/
    path('textrecordings/', views.TextRecordingView.as_view(), name='textrecs'),
    # spk/sentencerecordings/
    path('sentencerecordings/', views.SentenceRecordingCreateView.as_view(), name='sentencerecs-create'),
    #
    path('sentencerecordings/<int:rec>/', views.SentenceRecordingUpdateView.as_view(), name='sentencerecs-detail'),
    # spk/...
    path('sentencerecordings/<int:tr_id>/<int:index>/', views.SentenceRecordingRetrieveUpdateView.as_view(), name='sentencerecs-retrieveupdate')
]