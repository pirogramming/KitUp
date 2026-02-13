from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Season(models.Model):
    """
    시즌 관리
    - 관리자가 팀매칭 기간과 프로젝트 기간을 설정
    - 여러 시즌 동시 운영 가능
    """
    
    class Status(models.TextChoices):
        UPCOMING = "UPCOMING", "예정"
        MATCHING = "MATCHING", "팀매칭 중"
        IN_PROJECT = "IN_PROJECT", "프로젝트 진행 중"
        ENDED = "ENDED", "종료"
    
    name = models.CharField(
        max_length=100,
        help_text="시즌명 (예: 2026년 1월 시즌)",
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPCOMING,
    )
    
    # 팀매칭 기간
    matching_start = models.DateTimeField(help_text="팀매칭 시작")
    matching_end = models.DateTimeField(help_text="팀매칭 종료")
    
    # 프로젝트 기간
    project_start = models.DateTimeField(help_text="프로젝트 시작")
    project_end = models.DateTimeField(help_text="프로젝트 종료")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "seasons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.status})"
    
    def is_matching_period(self) -> bool:
        """팀매칭 기간인지 확인"""
        now = timezone.now()
        return self.matching_start <= now <= self.matching_end
    
    def is_project_period(self) -> bool:
        """프로젝트 기간인지 확인"""
        now = timezone.now()
        return self.project_start <= now <= self.project_end
    
    @classmethod
    def get_active_season(cls):
        """현재 활성화된 시즌 반환 (진행 중인 시즌)"""
        return cls.objects.filter(
            status__in=[cls.Status.MATCHING, cls.Status.IN_PROJECT]
        ).order_by('-created_at').first()


class Project(models.Model):
    """
    프로젝트
    - 1 project = 1 team (1:1 관계)
    - 팀 구성: PM 1명 / FE 2명 / BE 2명 (총 5명)
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "임시저장"
        OPEN = "OPEN", "모집중"
        MATCHED = "MATCHED", "매칭완료"
        IN_PROGRESS = "IN_PROGRESS", "진행중"
        COMPLETED = "COMPLETED", "완료"
        ARCHIVED = "ARCHIVED", "보관됨"

    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
        help_text="속한 시즌",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_projects",
        help_text="프로젝트 생성자",
    )

    title = models.CharField(
        max_length=120,
        help_text="프로젝트 제목",
    )

    description = models.TextField(
        null=True,
        blank=True,
        help_text="프로젝트 설명",
    )

    duration_weeks = models.SmallIntegerField(
        default=6,
        validators=[MinValueValidator(1)],
        help_text="프로젝트 기간 (주)",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        help_text="프로젝트 상태",
    )

    starts_at = models.DateField(
        null=True,
        blank=True,
        help_text="시작 예정일",
    )

    ends_at = models.DateField(
        null=True,
        blank=True,
        help_text="종료 예정일",
    )

    region = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        help_text="활동 지역 (오프라인 시)",
    )

    # 대시보드에서 팀원이 수정 가능한 필드
    project_image = models.ImageField(
        upload_to="projects/",
        null=True,
        blank=True,
        help_text="프로젝트 프로필 사진",
    )

    team_rules = models.TextField(
        null=True,
        blank=True,
        help_text="팀 규칙 (마크다운)",
    )

    related_links = models.TextField(
        null=True,
        blank=True,
        help_text="관련 링크 (마크다운)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.title
    
    def get_like_count(self) -> int:
        """좋아요 개수 반환"""
        return self.likes.count()
    
    def is_liked_by(self, user) -> bool:
        """특정 사용자가 좋아요를 눌렀는지 확인"""
        if not user or user.is_anonymous:
            return False
        return self.likes.filter(user=user).exists()
    
    def toggle_like(self, user):
        """사용자의 좋아요 상태 토글"""
        like_obj, created = self.likes.get_or_create(user=user)
        if not created:
            like_obj.delete()
        return created  # True: 좋아요 추가, False: 좋아요 제거


class ProjectLike(models.Model):
    """
    프로젝트 좋아요
    - 사용자가 프로젝트에 좋아요를 누를 수 있음
    - 중복 좋아요 방지 (User + Project 유니크)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_likes",
        help_text="좋아요 누른 사용자",
    )
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name="likes",
        help_text="좋아요 받은 프로젝트",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "project_likes"
        unique_together = ("user", "project")
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["user"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.user} ❤️ {self.project}"
