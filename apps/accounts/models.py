from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class TechStack(models.Model):
    """
    기술 스택 (마스터 데이터)
    - 프로그래밍 언어, 프레임워크, 도구 등
    - 관리자만 추가/수정 가능
    """

    class Category(models.TextChoices):
        FRONTEND = "FRONTEND", "프론트엔드"
        BACKEND = "BACKEND", "백엔드"
        PM = "PM", "기획"

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="기술 이름 (Python, React 등)",
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        help_text="기술 카테고리",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tech_stacks"
        ordering = ["category", "name"]
        indexes = [
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """
    Custom User for StartLine.dev
    - allauth 사용 (password_hash는 Django가 내부적으로 관리)
    - 로그인 후 프로필 설정 화면에서 nickname 입력
    """

    nickname = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="서비스 내 표시 닉네임",
    )

    profile_image = models.ImageField(
        upload_to="profiles/",
        null=True,
        blank=True,
        help_text="프로필 이미지",
    )

    bio = models.TextField(
        null=True,
        blank=True,
        help_text="자기소개",
    )

    github_id = models.CharField(
        max_length=39,
        unique=True,
        null=True,
        blank=True,
        help_text="GitHub 아이디",
    )

    passion_level = models.SmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="열정 레벨 (1~4)",
    )

    tech_stacks = models.ManyToManyField(
        TechStack,
        related_name="users",
        blank=True,
        help_text="사용자가 보유한 기술 스택",
    )

    team_ban_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="남은 팀플 참여 금지 횟수",
    )

    email_notifications_enabled = models.BooleanField(
        default=False,
        help_text="이메일 알림 수신 여부",
    )

    preferred_role = models.ForeignKey(
        "Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applicants",
        help_text="팀매칭 신청 시 선택한 직군",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_banned(self) -> bool:
        """팀플 참여 금지 상태 여부"""
        return self.team_ban_count > 0

    def is_profile_completed(self) -> bool:
        """프로필 설정 완료 여부"""
        return bool(self.nickname)

    def get_role_level(self, role_code: str) -> int:
        """특정 역할의 레벨 조회 (1~4, 없으면 0)"""
        try:
            role = Role.objects.get(code=role_code)
            user_level = self.role_levels.filter(role=role).first()
            return user_level.level if user_level else 0
        except Role.DoesNotExist:
            return 0

    def __str__(self) -> str:
        return self.nickname or self.username


class Role(models.Model):
    """
    역할 (시드 데이터, 고정)
    - PM: 기획
    - FRONTEND: 프론트엔드
    - BACKEND: 백엔드
    """

    class RoleCode(models.TextChoices):
        PM = "PM", "PM(기획)"
        FRONTEND = "FRONTEND", "프론트엔드"
        BACKEND = "BACKEND", "백엔드"

    code = models.CharField(
        max_length=20,
        unique=True,
        choices=RoleCode.choices,
        help_text="역할 코드 (PM/FRONTEND/BACKEND)",
    )

    name = models.CharField(
        max_length=30,
        help_text="역할 표시명",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"

    def __str__(self) -> str:
        return self.name


class UserRoleLevel(models.Model):
    """
    사용자별 역할 레벨 (1~4)
    - 역할별로 다른 레벨 관리
    - 설문 기반 진단, 재진단 가능
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="role_levels",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_levels",
    )

    level = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="실력 레벨 (1~4)",
    )

    last_diagnosed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="마지막 진단 일시",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_role_levels"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="uq_user_role_level",
            ),
            models.CheckConstraint(
                check=models.Q(level__gte=1, level__lte=4),
                name="ck_user_role_level_range",
            ),
        ]
        indexes = [
            models.Index(fields=["role", "level"]),
        ]

    def __str__(self) -> str:
        return f"{self.user}:{self.role.code}=Lv.{self.level}"


class Report(models.Model):
    """
    사용자 신고
    - 팀원을 신고하면 사유를 작성
    - 운영자가 승인 시 피신고자에게 팀플 2회 금지 제재
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "대기중"
        APPROVED = "APPROVED", "승인"
        REJECTED = "REJECTED", "거절"

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports_made",
        help_text="신고자",
    )

    reported_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports_received",
        help_text="피신고자",
    )

    reason = models.TextField(
        help_text="신고 사유",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="신고 처리 상태",
    )

    admin_note = models.TextField(
        null=True,
        blank=True,
        help_text="운영자 메모",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="처리 일시",
    )

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def approve(self):
        """신고 승인 - 피신고자에게 2회 팀플 금지 제재"""
        from django.utils import timezone
        self.status = self.Status.APPROVED
        self.processed_at = timezone.now()
        self.reported_user.team_ban_count += 2
        self.reported_user.save(update_fields=["team_ban_count"])
        self.save()

    def reject(self, admin_note: str = None):
        """신고 거절"""
        from django.utils import timezone
        self.status = self.Status.REJECTED
        self.processed_at = timezone.now()
        if admin_note:
            self.admin_note = admin_note
        self.save()

    def __str__(self) -> str:
        return f"{self.reporter} → {self.reported_user} ({self.get_status_display()})"
