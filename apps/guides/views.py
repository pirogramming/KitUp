from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from apps.projects.models import Project
from apps.teams.models import TeamMember
from apps.accounts.models import Role
from .models import GuideCard, GuideTaskProgress, ProjectProgress


@login_required
def mission(request):
    """미션 페이지"""
    project = Project.objects.filter(
        team__members__user=request.user,
        team__members__is_active=True
    ).first()
    
    if not project:
        return render(request, "guides/mission.html", {"project": None})
    
    team_member = get_object_or_404(
        TeamMember,
        team=project.team,
        user=request.user,
        is_active=True
    )
    role = team_member.role
    
    # 역할별 미션 카드
    guide_cards = GuideCard.objects.filter(
        role=role,
        is_active=True
    ).order_by('order_no').prefetch_related('tasks')
    
    # 미션 데이터 구성
    mission_data = []
    for card in guide_cards:
        tasks = card.tasks.all()
        
        # 완료된 태스크 개수
        completed_count = GuideTaskProgress.objects.filter(
            task__in=tasks,
            project=project,
            is_completed=True
        ).count()
        
        # 카드 완료 여부
        is_card_completed = completed_count == tasks.count() if tasks.count() > 0 else False
        
        task_progress_data = []
        for task in tasks:
            progress = GuideTaskProgress.objects.filter(
                task=task,
                project=project
            ).first()
            
            task_progress_data.append({
                'task': task,
                'is_completed': progress.is_completed if progress else False,
            })
        
        mission_data.append({
            'card': card,
            'task_progress_data': task_progress_data,
            'is_completed': is_card_completed,
        })
    
    # 모든 역할의 진척도 계산
    all_role_progress = []
    
    # 프로젝트에 속한 모든 팀원의 역할 가져오기
    team_members_data = TeamMember.objects.filter(
        team=project.team,
        is_active=True
    ).values('role').distinct()
    
    team_role_ids = [member['role'] for member in team_members_data]
    team_roles = Role.objects.filter(id__in=team_role_ids)
    
    for team_role in team_roles:
        # 해당 역할의 모든 미션 카드
        cards = GuideCard.objects.filter(
            role=team_role,
            is_active=True
        ).prefetch_related('tasks')
        
        # 전체 태스크 수 및 완료된 태스크 수
        total_tasks = 0
        completed_tasks = 0
        
        for card in cards:
            for task in card.tasks.all():
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
        
        all_role_progress.append({
            'role': team_role,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percent': progress_percent,
        })
    
    context = {
        'project': project,
        'role': role,
        'mission_data': mission_data,
        'all_role_progress': all_role_progress,
    }
    return render(request, "guides/mission.html", context)