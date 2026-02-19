from django.urls import path
from . import views

app_name = "teams"

urlpatterns = [
    # 소속팀 여부에 따라 이동 url 상이 (team/team_apply)
    path('matching/', views.team_matching_router, name='matching_router'),

    # 팀 매칭 신청
    path("apply/", views.team_apply, name="team_apply"),  # team_apply.html
    
    # 열정 테스트 (팀플 신청 시)
    path("passion-test/", views.passion_test, name="passion_test"),  # passion_test.html
    
    # 열정 테스트 결과 제출
    path("passion-submit/", views.passion_submit, name="passion_submit"),
    
    # 팀 매칭 신청 취소
    path("cancel/", views.team_matching_cancel, name="team_matching_cancel"),
    
    # 팀 매칭 결과/대기 화면
    path("status/", views.team_status, name="team_status"),  # team.html
    
    # 이메일 알림 활성화
    path("enable-notifications/", views.enable_email_notifications, name="enable_notifications"),
]
