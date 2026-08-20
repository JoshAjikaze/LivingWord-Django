from django.urls import path

from . import views

app_name = "social"

urlpatterns = [
    path("oauth/<str:platform>/start/", views.oauth_start, name="oauth_start"),
    path("oauth/<str:platform>/callback/", views.oauth_callback, name="oauth_callback"),
]
