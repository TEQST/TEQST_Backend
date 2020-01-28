from django.urls import path, include
from .views import TextRecordingView, SentenceRecordingCreateView, SentenceRecordingUpdateView

urlpatterns = [
    path('textrecordings/', TextRecordingView.as_view()),
    path('sentencerecordings/', SentenceRecordingCreateView.as_view()),
    path('sentencerecordings/<int:rec>/', SentenceRecordingUpdateView.as_view())
]