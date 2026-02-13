from django.shortcuts import render
from datetime import date

from apps.accounts.models import UserRoleLevel
from apps.projects.models import Project, Season
from apps.reflections.models import Retrospective

# 메인 화면 (main.html)
def main_view(request):
    """
    메인 화면 (main.html)
    - 비로그인: request.user가 AnonymousUser이므로 템플릿에서 자동 분기
    - 로그인: 
      1. 오늘의 작업 기록 (회고)
      2. 팀 매칭 모집 (현재 시즌 프로젝트들)
      3. KITUP 프로젝트 (보관된 프로젝트들)
    """
    
    user = request.user
    season = Season.get_active_season()
    context = {
        'season': season,
        'user_obj': user,
    }
    
    # 로그인 상태만 추가 데이터 조회
    if user.is_authenticated:
        """회고 부분"""
        recent_reflections = Retrospective.objects.filter(
            user=user
        ).order_by('-created_at')[:4]
        
        context["recent_reflections"] = recent_reflections
        """팀 매칭 부분"""
        season = Season.get_active_season()
        is_matching_period = season and season.is_matching_period() if season else False
        
        # 유저의 역할별 레벨
        role_levels = (
            UserRoleLevel.objects
            .filter(user=user)
            .select_related("role")
        )
        
        role_level_map = {
            rl.role.code: rl.level
            for rl in role_levels
        }
        
        # 현재 시즌의 모집 중인 프로젝트들
        matching_projects = None
        if season and is_matching_period:
            matching_projects = Project.objects.filter(
                status__in=[Project.Status.OPEN, Project.Status.MATCHED]
            ).select_related('team').order_by('-created_at')[:6]
        
        context["is_matching_period"] = is_matching_period
        context["role_levels"] = role_level_map
        context["matching_projects"] = matching_projects
    
    """KITUP 프로젝트 부분"""
    archived_projects = Project.objects.filter(
        status=Project.Status.ARCHIVED
    ).select_related('team').order_by('-created_at')
    
    context["archived_projects"] = archived_projects
    
    return render(request, "main.html", context)
