from django.urls import path, include
from . import views


urlpatterns = [
    path('users/', views.PubUserListView.as_view(), name="users"),
    path('users/checkname/', views.UsernameCheckView.as_view(), name="user-check"),
    path('user/', views.UserDetailedView.as_view(), name="user"),
    path('langs/', views.LanguageListView.as_view(), name="langs"),
    path('locale/<lang>', views.MenuLanguageView.as_view(), name="locale"),
    path('auth/register/', views.UserRegisterView.as_view(), name="register"),
    path('auth/login/', views.GetAuthToken.as_view(), name="login"),
    path('auth/logout/', views.LogoutView.as_view(), name="logout")
]