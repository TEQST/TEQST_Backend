from django.urls import path, include
from .views import TextRecordingView, SenctenceRecordingCreateView, SenctenceRecordingUpdateView

urlpatterns = [
    path('textrecordings/', TextRecordingView.as_view()),
    path('senctencerecordings/', SenctenceRecordingCreateView.as_view()),
    path('senctencerecordings/<int:rec>', SenctenceRecordingUpdateView.as_view())
]