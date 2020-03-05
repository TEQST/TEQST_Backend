from django.urls import path, include
from .views import UserListView, UserDetailedView, UserRegisterView, LanguageView, GetAuthToken, LogoutView, MenuLanguageView


urlpatterns = [
    path('users/', UserListView.as_view(), name="users"),
    path('user/', UserDetailedView.as_view(), name="user"),
    path('langs/', LanguageView.as_view(), name="langs"),
    path('locale/<lang>', MenuLanguageView.as_view(), name="locale"),
    path('auth/register/', UserRegisterView.as_view(), name="register"),
    path('auth/login/', GetAuthToken.as_view(), name="login"),
    path('auth/logout/', LogoutView.as_view(), name="logout")
]