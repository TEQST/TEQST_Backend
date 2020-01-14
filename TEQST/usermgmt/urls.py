from django.urls import path, include
from .views import UserListView, UserDetailedView

urlpatterns = [
    path('users/', UserListView.as_view()),
    path('users/<int:pk>/', UserDetailedView.as_view())
]