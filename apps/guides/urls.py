from django.urls import path
from . import views

app_name = "guides"

urlpatterns = [
    path("mission/", views.mission, name="mission"),
]