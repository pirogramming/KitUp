from django.conf import settings
from django.db import models
from django.db.models import Count, Q


class GuideCard(models.Model):
    """
    역할별 미션 카드
    - 순차적으로 진행되는 미션
    - 역할(PM/FE/BE)별로 개별 미션 제공
    """

    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.CASCADE,
        related_name="guide_cards",
        help_text="대상 역할 (PM/FRONTEND/BACKEND)",
    )

    title = models.CharField(
        max_length=120,
        help_text="미션 제목",
    )

    content_md = models.TextField(
        help_text="미션 설명 (마크다운)",
    )

    order_no = models.IntegerField(
        default=0,
        help_text="역할별 미션 순서",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "guide_cards"
        ordering = ["role", "order_no"]
        indexes = [
            models.Index(fields=["role", "order_no"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.role.code} 미션 {self.order_no}: {self.title}"

    def get_progress(self, project) -> dict:
        """프로젝트별 이 미션의 완료율"""
        tasks = self.tasks.all()
        completed = tasks.filter(
            progress__project=project,
            progress__is_completed=True
        ).distinct().count()
        total = tasks.count()
        
        return {
            "completed": completed,
            "total": total,
            "percent": int((completed / total * 100) if total > 0 else 0),
        }


class GuideTask(models.Model):
    """
    가이드 태스크 (체크리스트 항목)
    - 각 미션(카드)에 포함된 세부 할 일
    """

    card = models.ForeignKey(
        GuideCard,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    title = models.CharField(
        max_length=140,
        help_text="태스크 제목",
    )

    description = models.TextField(
        null=True,
        blank=True,
        help_text="태스크 상세 설명",
    )

    order_no = models.IntegerField(
        default=0,
        help_text="정렬 순서",
    )

    is_required = models.BooleanField(
        default=True,
        help_text="필수 여부",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "guide_tasks"
        ordering = ["card", "order_no"]
        indexes = [
            models.Index(fields=["card", "order_no"]),
        ]

    def __str__(self) -> str:
        return f"{self.card.title} - {self.title}"


class GuideTaskProgress(models.Model):
    """
    가이드 태스크 진행 상황
    - 프로젝트 × 태스크 별 완료 여부
    - 역할별 진척도를 추적
    """

    task = models.ForeignKey(
        GuideTask,
        on_delete=models.CASCADE,
        related_name="progress",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="guide_task_progress",
    )

    is_completed = models.BooleanField(
        default=False,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "guide_task_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "project"],
                name="uq_task_project",
            ),
        ]
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["task"]),
        ]

    def __str__(self) -> str:
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.task.title} ({self.project})"


class ProjectProgress(models.Model):
    """
    프로젝트 역할별 진척도
    - 각 역할(PM/FE/BE)의 미션 진행 상황 요약
    """

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="role_progress",
    )

    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.CASCADE,
        related_name="project_progress",
    )

    completed_tasks = models.IntegerField(
        default=0,
        help_text="완료한 태스크 수",
    )

    total_tasks = models.IntegerField(
        default=0,
        help_text="전체 태스크 수",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "role"],
                name="uq_project_role",
            ),
        ]

    def __str__(self) -> str:
        percent = int((self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0)
        return f"{self.project} - {self.role.code}: {percent}%"

    @property
    def progress_percent(self) -> int:
        """진척도 퍼센트"""
        return int((self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0)
