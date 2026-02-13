from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_http_methods

from apps.projects.models import Season, Project
from apps.projects.forms import ProjectDashboardEditForm
from apps.projects.services import TeamMatchingService
from apps.teams.models import Team, TeamMember


# ================================
# Helper 함수
# ================================

def _get_project_context(project, user):
    """
    프로젝트 상세 정보 context 생성 (dashboard_detail, project_detail에서 공유)
    N+1 쿼리 최적화: prefetch_related 및 캐싱 활용
    """
    team = project.team
    # N+1 쿼리 최적화: user__role_levels를 미리 로드
    members = team.members.filter(is_active=True).select_related(
        "user", 
        "role"
    ).prefetch_related("user__role_levels")
    member_count_by_role = team.get_member_count_by_role()
    
    # 각 멤버에 레벨 정보 추가 (캐시된 role_levels 사용)
    members_with_level = []
    for member in members:
        # prefetch_related된 role_levels에서 직접 조회 (DB 쿼리 없음)
        role_level = None
        for rl in member.user.role_levels.all():
            if rl.role.code == member.role.code:
                role_level = rl.level
                break
        
        member_data = {
            'member': member,
            'level': role_level or 0
        }
        members_with_level.append(member_data)
    

    # 시즌 정보
    season = None
    active_season = Season.get_active_season()
    if active_season:
        if active_season.project_start <= project.created_at <= active_season.project_end:
            season = active_season
    
    # 가이드 진척도 계산 (전체 미션 합산)
    guide_progress = None
    try:
        from apps.guides.models import GuideCard, GuideTaskProgress
        from apps.accounts.models import Role
        
        # 프로젝트의 모든 팀원 역할 가져오기
        # N+1 쿼리 최적화: values_list + in 사용하여 role ID만 먼저 추출
        team_role_ids = team.members.filter(is_active=True).values_list(
            'role_id', flat=True
        ).distinct()
        
        # 한 번에 모든 카드와 태스크 로드
        cards_with_tasks = GuideCard.objects.filter(
            role_id__in=team_role_ids,
            is_active=True
        ).prefetch_related('tasks')  # 카드와 태스크를 한 번에 로드
        
        total_tasks = 0
        completed_tasks = 0
        
        # 메모리에서만 작업 (DB 쿼리 없음)
        for card in cards_with_tasks:
            for task in card.tasks.all():  # prefetch_related로 이미 로드됨
                total_tasks += 1
                # 이 태스크가 프로젝트에서 완료되었는지 확인
                is_completed = GuideTaskProgress.objects.filter(
                    task=task,
                    project=project,
                    is_completed=True
                ).exists()
                
                if is_completed:
                    completed_tasks += 1
        
        progress_percent = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
        
        guide_progress = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percent': progress_percent,
        }
    except:
        # GuideCard 모델이 없거나 데이터가 없으면 None으로 처리
        guide_progress = None
    
    return {
        "project": project,
        "team": team,
        "members": members,
        "members_with_level": members_with_level,
        "member_count_by_role": member_count_by_role,
        "season": season,
        "guide_progress": guide_progress,
    }


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
    """프로젝트 대시보드 조회 (진행 중인 프로젝트)"""
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
    
    context = _get_project_context(project, request.user)
    context["is_team_member"] = is_team_member
    
    return render(request, "projects/dashboard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def dashboard_update(request, project_id):
    """프로젝트 대시보드 조회 (진행 중인 프로젝트)"""
    project = get_object_or_404(Project, id=project_id)

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
        
        if form.is_valid():
            form.save()
            
            messages.success(request, "✅ 프로젝트 정보가 수정되었습니다.")
            return redirect("projects:dashboard_detail", project_id=project_id)
        else:
            messages.error(request, "❌ 입력 오류가 있습니다. 다시 확인해주세요.")
    else:
        form = ProjectDashboardEditForm(instance=project)
    
    context = _get_project_context(project, request.user)
    context["form"] = form
    context["is_team_member"] = is_team_member
    
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
    
    context = _get_project_context(project, request.user)
    
    return render(request, "projects/project_detail.html", context)


@login_required
@require_http_methods(["GET"])
def kitup_list(request):
    """모든 KITUP 프로젝트 리스트 (완료된 보관 프로젝트)"""
    # 보관된 프로젝트만 조회 (ARCHIVED 상태)
    projects = Project.objects.filter(
        status=Project.Status.ARCHIVED
    ).select_related('team')
    
    # 정렬 처리
    sort = request.GET.get('sort', 'popular')
    if sort == 'latest':
        projects = projects.order_by('-created_at')
    elif sort == 'oldest':
        projects = projects.order_by('created_at')
    # 내 프로젝트 필터링 옵션
    elif sort == 'my_projects':
        projects = projects.filter(
            team__members__user=request.user
        ).distinct().order_by('-created_at')

    else:  # popular (기본값)
        # annotate로 좋아요 개수 추가하여 정렬
        from django.db.models import Count
        projects = projects.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')
    
    context = {
        "projects": projects,
        "sort": sort,
    }
    return render(request, "projects/kitup_list.html", context)


@login_required
@require_http_methods(["GET"])
def kitup_detail(request, project_id):
    """모든 KITUP 프로젝트 상세 (보관된 프로젝트 조회만)"""
    project = get_object_or_404(Project, id=project_id, status=Project.Status.ARCHIVED)
    
    context = _get_project_context(project, request.user)
    
    return render(request, "projects/kitup_detail.html", context)


@login_required
@require_POST
@login_required
@require_POST
def toggle_project_like(request, project_id):
    """프로젝트 좋아요 토글 API"""
    from django.http import JsonResponse
    
    project = get_object_or_404(Project, id=project_id)
    
    # 좋아요 토글
    is_liked = project.toggle_like(request.user)
    like_count = project.get_like_count()
    
    return JsonResponse({
        'success': True,
        'is_liked': is_liked,
        'like_count': like_count,
    })


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
