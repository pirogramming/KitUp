from django.urls import path
from . import api_views

app_name = "guides_api"

urlpatterns = [
    path("card/<int:card_id>/toggle/", api_views.toggle_card, name="toggle_card"),
]