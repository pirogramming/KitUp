from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    # 프로젝트 대시보드 (현재 프로젝트)
    path("dashboard/", views.dashboard, name="dashboard"),  # dashboard.html
    path("dashboard/<int:project_id>/", views.dashboard_detail, name="dashboard_detail"),  # 대시보드 조회
    path("dashboard/<int:project_id>/edit/", views.dashboard_edit, name="dashboard_edit"),  # 대시보드 수정
    
    # 지난 프로젝트
    path("", views.project_list, name="project_list"),  # project_list.html
    path("<int:project_id>/", views.project_detail, name="project_detail"),  # project_detail.html
    
    # KITUP 프로젝트 (모든 프로젝트)
    path("all/", views.kitup_list, name="kitup_list"),  # kitup_list.html
    path("all/<int:project_id>/", views.kitup_detail, name="kitup_detail"),  # kitup_detail.html
    
    # 팀 매칭 관리
    path("matching/<int:season_id>/run/", views.run_team_matching, name="run_team_matching"),  # API
]
