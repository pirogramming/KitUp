# reflections/models.py
import os
import uuid

from django.conf import settings
from django.db import models


class Retrospective(models.Model):
    """
    회고
    - 프로젝트별 개인 회고 작성
    - 마크다운 형식
    """

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="retrospectives",
        null=True,
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="retrospectives",
    )

    # 어떤 질문 템플릿으로 작성했는지 (default/compact)
    template_key = models.CharField(
        max_length=32,
        default="default",
        help_text="회고 질문 템플릿 키 (e.g., default, compact)",
    )

    title = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="회고 제목",
    )

    # 질문별 답변 원본(JSON): { "q1_work_done": "...md...", ... }
    answers_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="질문별 답변 원본(JSON). 값은 마크다운 텍스트 문자열을 권장",
    )

    content_md = models.TextField(
        help_text="회고 내용 (마크다운)",
        blank=True,
        default="",
    )

    bookmarked = models.BooleanField(
        default=False,
        help_text="찜 여부",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "retrospectives"
        indexes = [
            models.Index(fields=["project", "user"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["template_key", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.project}: {self.title or '회고'}"


def retrospective_asset_upload_to(instance: "RetrospectiveAsset", filename: str) -> str:
    """
    저장 경로:
    media/retrospectives/<user_id>/<retrospective_id>/<uuid>.<ext>
    """
    _, ext = os.path.splitext(filename)
    ext = (ext or "").lower()
    return f"retrospectives/{instance.user_id}/{instance.retrospective_id}/{uuid.uuid4().hex}{ext}"


class RetrospectiveAsset(models.Model):
    """
    회고 첨부 이미지
    - 업로드 후 반환되는 image.url을 md 문법으로 본문에 삽입: ![alt](/media/...)
    """

    retrospective = models.ForeignKey(
        Retrospective,
        on_delete=models.CASCADE,
        related_name="assets",
        null=True, blank=True,
    )

    # 권한/조회 편의용 (중복이지만 실무에서 유용)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="retrospective_assets",
    )

    # 임시 저장용 키 (회고 작성 중 업로드된 이미지 구분용)
    draft_key = models.UUIDField(
        null=True, blank=True, db_index=True
    )  

    image = models.ImageField(
        upload_to=retrospective_asset_upload_to,
        help_text="첨부 이미지",
    )

    alt_text = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="마크다운 이미지 alt 텍스트",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "retrospective_assets"
        indexes = [
            models.Index(fields=["retrospective", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # retrospective.user와 항상 일치시키기
        if self.retrospective_id and (not self.user_id):
            self.user = self.retrospective.user
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"asset:{self.id} retro:{self.retrospective_id} user:{self.user_id}"
