"""
가이드 관련 비즈니스 로직
"""
import markdown
import bleach
from django.db.models import Count

from .models import GuideCard, GuideTask, GuideTaskProgress, ProjectProgress


class GuideService:
    """가이드 서비스"""
    
    @staticmethod
    def render_markdown(content):
        """마크다운을 HTML로 변환 (XSS 방지)"""
        if not content:
            return ""
        
        html = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'nl2br', 'toc']
        )
        
        # XSS 방지: 안전한 태그만 허용
        allowed_tags = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'strong', 'em', 'u', 'del',
            'ul', 'ol', 'li',
            'blockquote',
            'code', 'pre',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'a', 'img',
        ]
        
        allowed_attributes = {
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title'],
            'code': ['class'],
        }
        
        html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
        return html
    
    @staticmethod
    def get_role_progress(project, role):
        """
        역할별 진척도 조회
        
        Returns:
            {
                'role': Role,
                'completed_tasks': int,
                'total_tasks': int,
                'progress_percent': int,
            }
        """
        guide_cards = GuideCard.objects.filter(role=role, is_active=True)
        
        total_tasks = 0
        completed_tasks = 0
        
        for card in guide_cards:
            tasks = card.tasks.all()
            total_tasks += tasks.count()
            
            completed = GuideTaskProgress.objects.filter(
                task__in=tasks,
                project=project,
                is_completed=True
            ).count()
            completed_tasks += completed
        
        progress_percent = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
        
        return {
            'role': role,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'progress_percent': progress_percent,
        }
    
    @staticmethod
    def get_all_role_progress(project):
        """프로젝트의 모든 역할 진척도"""
        progress_list = []
        
        for proj_progress in ProjectProgress.objects.filter(project=project):
            progress_list.append({
                'role': proj_progress.role,
                'completed_tasks': proj_progress.completed_tasks,
                'total_tasks': proj_progress.total_tasks,
                'progress_percent': proj_progress.progress_percent,
            })
        
        return progress_list
