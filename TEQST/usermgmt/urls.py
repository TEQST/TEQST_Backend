from django.urls import path
from . import views


urlpatterns = [
    path('users/', views.PubUserListView.as_view(), name="users"),
    path('users/checkname/', views.check_username, name="user-check"),
    path('user/', views.UserDetailedView.as_view(), name="user"),
    path('pub/speakerstats/', views.pub_speaker_stats, name="pub-speaker-stats"),
    path('langs/', views.LanguageListView.as_view(), name="langs"),
    path('countries/', views.country_list, name="countries"),
    path('accents/', views.accent_list, name="accents"),
    path('locale/<lang>', views.MenuLanguageView.as_view(), name="locale"),
    path('auth/register/', views.UserRegisterView.as_view(), name="register"),
    path('auth/login/', views.login, name="login"),
    path('auth/logout/', views.logout, name="logout")
]