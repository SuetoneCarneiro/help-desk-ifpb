from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "entrar/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    # No Django 5, o LogoutView só aceita POST: um link (GET) não desloga ninguém.
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
]
