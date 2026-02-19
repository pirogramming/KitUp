from django.urls import path, include

urlpatterns = [
    path("accounts/", include("apps.accounts.api_urls")),
    path("projects/", include("apps.projects.api_urls")),
    path("teams/", include("apps.teams.api_urls")),
    path("guides/", include("apps.guides.api_urls")),
    path("reflections/", include("apps.reflections.api_urls")),
]
