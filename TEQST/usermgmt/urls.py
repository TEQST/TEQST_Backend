from django.urls import path, include
from .views import UserListView, UserDetailedView, UserRegisterView, LanguageView, GetAuthToken


urlpatterns = [
    path('users/', UserListView.as_view()),
    path('users/<int:pk>/', UserDetailedView.as_view()),
    path('langs/', LanguageView.as_view()),
    path('auth/register/', UserRegisterView.as_view()),
    #path('auth/login/', GetAuthToken.as_view())
]