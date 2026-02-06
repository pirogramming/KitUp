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
    
    is_active = models.BooleanField(
        default=False,
        help_text="현재 진행 중인 시즌",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "seasons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
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
        """현재 활성화된 시즌 반환"""
        return cls.objects.filter(is_active=True).first()


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

    target_team_size = models.SmallIntegerField(
        default=5,
        help_text="목표 팀 인원 (PM1/FE2/BE2 = 5명)",
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

    related_links = models.JSONField(
        default=dict,
        blank=True,
        help_text="관련 링크 (Notion, Figma, GitHub 등)",
    )

    is_favorite = models.BooleanField(
        default=False,
        help_text="즐겨찾기 여부",
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


class ProjectApplication(models.Model):
    """
    프로젝트 지원
    - 열정 레벨 (1~4) 저장
    - 지원 역할 선택
    """

    class Status(models.TextChoices):
        APPLIED = "APPLIED", "지원됨"
        CANCELLED = "CANCELLED", "취소됨"
        MATCHED = "MATCHED", "매칭됨"
        REJECTED = "REJECTED", "거절됨"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.PROTECT,
        related_name="applications",
        help_text="지원 역할 (PM/FRONTEND/BACKEND)",
    )

    passion_level = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="열정 레벨 (1~4, 설문 결과)",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_applications"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="uq_project_application",
            ),
            models.CheckConstraint(
                check=models.Q(passion_level__gte=1, passion_level__lte=4),
                name="ck_passion_level_range",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "role", "status"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["passion_level"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.project} ({self.role.code})"
