from django.urls import path, include
from .views import TextRecordingView, SenctenceRecordingCreateView, SenctenceRecordingUpdateView

urlpatterns = [
    path('textrecordings/', TextRecordingView.as_view()),
    path('sentencerecordings/', SenctenceRecordingCreateView.as_view()),
    path('sentencerecordings/<int:rec>/', SenctenceRecordingUpdateView.as_view())
]