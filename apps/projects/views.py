from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_http_methods

from apps.projects.models import Season, Project
from apps.projects.forms import ProjectDashboardEditForm, ProjectRelatedLinksForm
from apps.projects.services import TeamMatchingService
from apps.teams.models import Team, TeamMember


@login_required
def dashboard(request):
    """
    현재 프로젝트 대시보드 진입점
    
    - 사용자가 속한 현재 진행 중인 프로젝트가 있으면 해당 프로젝트 대시보드로 리다이렉트
    - 없으면 "현재 진행중인 프로젝트가 없어요" 페이지 렌더링
    """
    
    # 사용자의 현재 진행 중인 프로젝트 찾기
    team_member = TeamMember.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('team__project').first()
    
    # 프로젝트 있으면 상세 페이지로 리다이렉트
    if team_member and team_member.team.project:
        return redirect('projects:dashboard_detail', project_id=team_member.team.project.id)
    
    # 프로젝트 없으면 "현재 진행중인 프로젝트가 없어요" 페이지 표시
    return render(request, "projects/dashboard.html", {"has_project": False})


@login_required
@require_http_methods(["GET"])
def dashboard_detail(request, project_id):
    """
    프로젝트 대시보드 조회 (읽기 전용)
    
    읽기 전용 정보:
    - 진행기간 (starts_at, ends_at)
    - 팀 정보 (team composition)
    - 진척도 (guide_stage progress)
    """
    project = get_object_or_404(Project, id=project_id)
    
    # 팀원 확인
    is_team_member = TeamMember.objects.filter(
        team__project=project,
        user=request.user,
        is_active=True
    ).exists()
    
    if not is_team_member:
        messages.error(request, "팀원만 접근할 수 있습니다.")
        return redirect("projects:dashboard")
    
    # 팀 정보
    team = project.team
    members = team.members.filter(is_active=True).select_related("user", "role")
    member_count_by_role = team.get_member_count_by_role()
    
    # 시즌 정보
    season = None
    active_season = Season.get_active_season()
    if active_season:
        if active_season.project_start <= project.created_at <= active_season.project_end:
            season = active_season
    
    # 가이드 진척도 계산
    guide_progress = None
    if project.current_stage:
        from apps.guides.models import GuideTask, GuideTaskProgress
        
        total_tasks = GuideTask.objects.filter(
            card__stage=project.current_stage
        ).count()
        
        completed_tasks = GuideTaskProgress.objects.filter(
            task__card__stage=project.current_stage,
            project=project,
            user=request.user,
            is_completed=True
        ).count()
        
        progress_percent = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
        
        guide_progress = {
            'stage': project.current_stage,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percent': progress_percent,
        }
    
    context = {
        "project": project,
        "team": team,
        "members": members,
        "member_count_by_role": member_count_by_role,
        "season": season,
        "guide_progress": guide_progress,
        "is_team_member": is_team_member,
    }
    
    return render(request, "projects/dashboard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def dashboard_update(request, project_id):
    """
    프로젝트 대시보드 수정 (팀원만)
    
    수정 가능 필드:
    - 서비스명 (title)
    - 서비스 소개 (description)
    - 프로필 사진 (project_image)
    - 팀 규칙 (team_rules)
    - 관련 링크 (related_links)
    - 즐겨찾기 (is_favorite)
    """
    project = get_object_or_404(Project, id=project_id)
    
    # 팀원 권한 확인
    is_team_member = TeamMember.objects.filter(
        team__project=project,
        user=request.user,
        is_active=True
    ).exists()
    
    if not is_team_member:
        messages.error(request, "팀원만 수정할 수 있습니다.")
        return redirect("projects:dashboard_detail", project_id=project_id)
    
    if request.method == "POST":
        form = ProjectDashboardEditForm(request.POST, request.FILES, instance=project)
        links_form = ProjectRelatedLinksForm(request.POST)
        
        if form.is_valid() and links_form.is_valid():
            project = form.save(commit=False)
            project.related_links = links_form.to_dict()
            project.save()
            
            messages.success(request, "✅ 프로젝트 정보가 수정되었습니다.")
            return redirect("projects:dashboard_detail", project_id=project_id)
        else:
            messages.error(request, "❌ 입력 오류가 있습니다. 다시 확인해주세요.")
    else:
        form = ProjectDashboardEditForm(instance=project)
        related_links = project.related_links or {}
        links_form = ProjectRelatedLinksForm(initial={
            "notion_url": related_links.get("notion"),
            "figma_url": related_links.get("figma"),
            "github_url": related_links.get("github"),
        })
    
    context = {
        "project": project,
        "form": form,
        "links_form": links_form,
    }
    
    return render(request, "projects/dashboard_update.html", context)


@login_required
@require_http_methods(["GET"])
def project_list(request):
    """과거 프로젝트 리스트 (완료된 프로젝트)"""
    # 사용자가 속했던 모든 팀의 프로젝트
    projects = Project.objects.filter(
        team__members__user=request.user,
        team__members__is_active=False  # 비활성 (완료된 팀)
    ).distinct().select_related('team').order_by('-created_at')
    
    context = {
        "projects": projects,
    }
    return render(request, "projects/project_list.html", context)


@login_required
@require_http_methods(["GET"])
def project_detail(request, project_id):
    """과거 프로젝트 상세 (조회만)"""
    project = get_object_or_404(Project, id=project_id)
    
    # 사용자가 해당 프로젝트에 속했었는지 확인
    is_member = TeamMember.objects.filter(
        team__project=project,
        user=request.user
    ).exists()
    
    if not is_member:
        messages.error(request, "접근 권한이 없습니다.")
        return redirect("projects:project_list")
    
    # 팀 정보
    team = project.team
    members = team.members.all().select_related("user", "role")
    member_count_by_role = team.get_member_count_by_role()
    
    # 시즌 정보
    season = None
    active_season = Season.get_active_season()
    if active_season:
        if active_season.project_start <= project.created_at <= active_season.project_end:
            season = active_season
    
    context = {
        "project": project,
        "team": team,
        "members": members,
        "member_count_by_role": member_count_by_role,
        "season": season,
    }
    
    return render(request, "projects/project_detail.html", context)


@login_required
def kitup_list(request):
    """모든 KITUP 프로젝트 리스트"""
    # TODO: 모든 프로젝트 리스트 로직 구현
    context = {}
    return render(request, "projects/kitup_list.html", context)


@login_required
def kitup_detail(request, project_id):
    """모든 KITUP 프로젝트 상세"""
    # TODO: 모든 프로젝트 상세 로직 구현
    # project = get_object_or_404(Project, id=project_id)
    context = {
        "project_id": project_id,
    }
    return render(request, "projects/kitup_detail.html", context)


# ================================
# 팀 매칭 관리 API
# ================================

@permission_required('projects.add_project', raise_exception=True)
@require_POST
def run_team_matching(request, season_id):
    """
    팀 매칭 알고리즘 실행 (관리자만)
    
    POST /projects/matching/{season_id}/run/
    
    Returns:
        JSON: 매칭 결과 통계
    """
    try:
        season = Season.objects.get(id=season_id)
    except Season.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'시즌 ID {season_id}를 찾을 수 없습니다.',
        }, status=404)
    
    # 팀매칭 기간 확인
    if not season.is_matching_period():
        return JsonResponse({
            'success': False,
            'error': '현재 팀매칭 기간이 아닙니다.',
        }, status=400)
    
    try:
        result = TeamMatchingService.run_matching(season_id)
        
        return JsonResponse({
            'success': True,
            'message': f'✅ 팀 매칭 완료! {result["teams_created"]}개 팀 생성',
            'data': {
                'teams_created': result['teams_created'],
                'total_users_matched': result['total_users_matched'],
                'pm_matched': result['pm_matched'],
                'fe_matched': result['fe_matched'],
                'be_matched': result['be_matched'],
                'total_unmatched': result['total_unmatched'],
                'unmatched_details': result['unmatched'],
            }
        })
    
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': f'❌ 매칭 실패: {str(e.message)}',
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'❌ 예상치 못한 오류: {str(e)}',
        }, status=500)
