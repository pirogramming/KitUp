from django.urls import path
from . import api_views

app_name = "guides_api"

urlpatterns = [
    # 태스크 완료/미완료 처리
    path(
        "projects/<int:project_id>/tasks/<int:task_id>/toggle/",
        api_views.toggle_task_completion,
        name="toggle_task",
    ),
    # 프로젝트 역할별 진척도 조회
    path(
        "projects/<int:project_id>/progress/",
        api_views.get_project_progress,
        name="project_progress",
    ),
]
