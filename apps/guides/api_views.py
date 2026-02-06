from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count
import json

from apps.projects.models import Project
from apps.teams.models import TeamMember
from .models import GuideTask, GuideTaskProgress, ProjectProgress, GuideCard


@login_required
@require_http_methods(["PATCH"])
def toggle_task_completion(request, project_id, task_id):
    """
    태스크 완료/미완료 토글
    
    Request:
        PATCH /api/guides/projects/{project_id}/tasks/{task_id}/toggle/
        {
            "is_completed": true
        }
    """
    try:
        # JSON body 파싱
        body = json.loads(request.body)
        is_completed = body.get('is_completed', False)
        
        # 권한 확인: 사용자가 이 프로젝트의 팀원인가?
        project = get_object_or_404(
            Project,
            id=project_id,
            team__members__user=request.user,
            team__members__is_active=True
        )
        
        task = get_object_or_404(GuideTask, id=task_id)
        
        # 태스크가 사용자의 역할에 속하는가?
        team_member = TeamMember.objects.get(
            team=project.team,
            user=request.user,
            is_active=True
        )
        
        if task.card.role != team_member.role:
            return JsonResponse(
                {"error": "이 미션은 당신의 역할이 아닙니다"},
                status=403
            )
        
        # GuideTaskProgress 생성 또는 업데이트
        progress, created = GuideTaskProgress.objects.get_or_create(
            task=task,
            project=project
        )
        
        # 완료 상태 변경
        if is_completed and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
        elif not is_completed and progress.is_completed:
            progress.is_completed = False
            progress.completed_at = None
        
        progress.save()
        
        # ProjectProgress 업데이트
        _update_project_progress(project, team_member.role)
        
        return JsonResponse({
            "success": True,
            "is_completed": progress.is_completed,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        })
    
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=400
        )


@login_required
@require_http_methods(["GET"])
def get_project_progress(request, project_id):
    """
    프로젝트의 역할별 진척도 조회
    
    Response:
        {
            "project": {...},
            "progress": [
                {
                    "role": "PM",
                    "completed_tasks": 5,
                    "total_tasks": 10,
                    "progress_percent": 50
                },
                ...
            ]
        }
    """
    try:
        # 권한 확인
        project = get_object_or_404(
            Project,
            id=project_id,
            team__members__user=request.user,
            team__members__is_active=True
        )
        
        # 모든 역할의 진척도
        progress_data = []
        for role_progress in ProjectProgress.objects.filter(project=project):
            progress_data.append({
                "role": role_progress.role.code,
                "completed_tasks": role_progress.completed_tasks,
                "total_tasks": role_progress.total_tasks,
                "progress_percent": role_progress.progress_percent,
            })
        
        return JsonResponse({
            "success": True,
            "project_id": project.id,
            "project_title": project.title,
            "progress": progress_data,
        })
    
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=400
        )


def _update_project_progress(project, role):
    """
    ProjectProgress 업데이트 로직
    특정 역할의 진척도를 계산하고 저장
    """
    from django.db.models import Count, Q
    
    # 1. 해당 역할의 모든 태스크 조회 (카드 통해서)
    guide_cards = GuideCard.objects.filter(
        role=role, 
        is_active=True
    ).prefetch_related('tasks')
    
    # 2. 모든 task_id 수집
    all_task_ids = []
    for card in guide_cards:
        all_task_ids.extend(card.tasks.values_list('id', flat=True))
    
    total_tasks = len(all_task_ids)
    
    # 3. 한 번에 모든 진행 상태 조회 (N+1 해결)
    completed_tasks = GuideTaskProgress.objects.filter(
        task_id__in=all_task_ids,
        project=project,
        is_completed=True
    ).count()
    
    # 4. ProjectProgress 생성 또는 업데이트
    progress, created = ProjectProgress.objects.get_or_create(
        project=project,
        role=role
    )
    
    progress.total_tasks = total_tasks
    progress.completed_tasks = completed_tasks
    progress.save()
