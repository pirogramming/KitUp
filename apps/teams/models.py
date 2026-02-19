from django.conf import settings
from django.db import models


class Team(models.Model):
    """
    팀
    - 1 project = 1 team (1:1 관계)
    - 팀 구성: PM 1명 / FE 2명 / BE 2명 (총 5명)
    """

    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="team",
        help_text="연결된 프로젝트 (1:1)",
    )

    name = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        help_text="팀 이름",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "teams"

    def __str__(self) -> str:
        return self.name or f"Team#{self.id}"

    def get_member_count_by_role(self) -> dict:
        """역할별 현재 멤버 수 반환"""
        from django.db.models import Count
        counts = self.members.filter(is_active=True).values("role__code").annotate(count=Count("id"))
        return {item["role__code"]: item["count"] for item in counts}


class TeamMember(models.Model):
    """
    팀 멤버
    - 역할별로 배정
    - PM 1명 / FE 2명 / BE 2명 구성은 서비스 로직에서 검증
    """

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )

    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.PROTECT,
        related_name="team_members",
        help_text="배정된 역할",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="활성 상태 (탈퇴 시 False)",
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    left_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="탈퇴 일시",
    )

    class Meta:
        db_table = "team_members"
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="uq_team_member",
            ),
        ]
        indexes = [
            models.Index(fields=["team", "role"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.team} ({self.role.code})"
