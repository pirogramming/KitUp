from django import forms
from .models import Project


class ProjectDashboardEditForm(forms.ModelForm):
    """
    프로젝트 대시보드 수정 폼
    팀원이 수정 가능한 필드만 포함
    """

    class Meta:
        model = Project
        fields = [
            "title",  # 서비스명
            "description",  # 서비스 소개
            "project_image",  # 프로젝트 프로필 사진
            "team_rules",  # 팀 규칙
            "related_links",  # 관련 링크
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "서비스명을 입력하세요",
                "maxlength": "120",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "서비스에 대해 설명해주세요",
                "rows": 4,
            }),
            "project_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "team_rules": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "팀 규칙을 마크다운으로 작성해주세요\n\n예:\n# 회의\n- 주 1회 수요일 19시\n- 지각 3회 = 경고\n\n# 코드 리뷰\n- PR 2시간 내 리뷰\n- 2명 승인 필수",
                "rows": 6,
            }),
            "related_links": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "관련 링크를 마크다운으로 입력해주세요\n\n예:\n[Notion](https://notion.so/...)\n[Figma](https://figma.com/...)\n[GitHub](https://github.com/...)",
                "rows": 6,
            }),
        }

    def clean_title(self):
        """서비스명 유효성 검사"""
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError("서비스명은 필수입니다.")
        return title

    def clean_related_links(self):
        """관련 링크 정리 - "{}" 같은 빈 값 제거"""
        related_links = self.cleaned_data.get("related_links", "").strip()
        # "{}" 또는 빈 문자열이면 None 반환
        if not related_links or related_links == "{}":
            return None
        return related_links
