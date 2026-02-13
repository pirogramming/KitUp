from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from .views import main_view
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    
    path("", main_view, name="main"),  # 메인 화면 (main.html)
    path("admin/", admin.site.urls),
    
    #   allauth (로그인/소셜로그인)
    path("accounts/", include("allauth.urls")),
    #   allauth 쪽으로 리다이렉트
    path("login/", RedirectView.as_view(url="/accounts/login/")),
    path("logout/", RedirectView.as_view(url="/accounts/logout/")),
    path("signup/", RedirectView.as_view(url="/accounts/signup/")),
    
    # template views: HTML로 보여줄 주소들
    path("accounts/", include("apps.accounts.urls")),
    path("projects/", include("apps.projects.urls")),
    path("teams/", include("apps.teams.urls")),
    path("guides/", include("apps.guides.urls")),
    path("reflections/", include("apps.reflections.urls")),

    # API views: Swagger로 테스트할 주소들
    path("api/", include("config.api_urls")),
    
    # Swagger & API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )