from django.urls import path, include
from .views import UserListView, UserDetailedView, UserRegisterView, LanguageView

urlpatterns = [
    path('users/', UserListView.as_view()),
    path('users/<int:pk>/', UserDetailedView.as_view()),
    path('langs/', LanguageView.as_view()),
    path('users/register/', UserRegisterView.as_view())
]