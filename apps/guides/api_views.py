from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from apps.projects.models import Project
from .models import GuideCard, GuideTask, GuideTaskProgress, ProjectProgress


@login_required
@require_POST
def toggle_card(request, card_id):
    """카드 완료/미완료 토글"""
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        is_completed = data.get('is_completed')
        
        project = get_object_or_404(Project, id=project_id)
        card = get_object_or_404(GuideCard, id=card_id)
        
        # 카드의 모든 태스크 완료/미완료 처리
        tasks = card.tasks.all()
        for task in tasks:
            GuideTaskProgress.objects.update_or_create(
                task=task,
                project=project,
                defaults={'is_completed': is_completed}
            )
        
        # ProjectProgress 업데이트
        update_project_progress(project, card.role)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def update_project_progress(project, role):
    """역할별 진척도 업데이트"""
    role_cards = GuideCard.objects.filter(role=role, is_active=True)
    all_tasks = GuideTask.objects.filter(card__in=role_cards)
    
    total = all_tasks.count()
    completed = GuideTaskProgress.objects.filter(
        task__in=all_tasks,
        project=project,
        is_completed=True
    ).count()
    
    ProjectProgress.objects.update_or_create(
        project=project,
        role=role,
        defaults={
            'total_tasks': total,
            'completed_tasks': completed
        }
    )