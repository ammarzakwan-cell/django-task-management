from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("logout/", views.logout_request, name="logout"),
    path("login/", views.login_request, name="login"),
]   