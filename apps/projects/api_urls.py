from django.urls import path
from . import views

urlpatterns = [
    # 프로젝트 좋아요 토글
    path("<int:project_id>/like/", views.toggle_project_like, name="api_toggle_project_like"),
]
