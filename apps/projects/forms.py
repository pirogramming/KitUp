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
            "is_favorite",  # 즐겨찾기
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
                "placeholder": "팀 규칙을 마크다운 형식으로 작성해주세요\n\n예:\n# 회의 규칙\n- 주 1회 수요일 19시\n- 지각 3회 = 경고\n\n# 코드 리뷰\n- PR 생성 후 2시간 내 리뷰\n- 최소 2명 승인 필수",
                "rows": 6,
            }),
            "is_favorite": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_title(self):
        """서비스명 유효성 검사"""
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError("서비스명은 필수입니다.")
        return title


class ProjectRelatedLinksForm(forms.Form):
    """
    관련 링크 별도 폼 (AJAX 업데이트용)
    """

    notion_url = forms.URLField(
        required=False,
        label="Notion",
        widget=forms.URLInput(attrs={
            "class": "form-control",
            "placeholder": "Notion 링크를 입력하세요",
        }),
    )

    figma_url = forms.URLField(
        required=False,
        label="Figma",
        widget=forms.URLInput(attrs={
            "class": "form-control",
            "placeholder": "Figma 링크를 입력하세요",
        }),
    )

    github_url = forms.URLField(
        required=False,
        label="GitHub",
        widget=forms.URLInput(attrs={
            "class": "form-control",
            "placeholder": "GitHub 링크를 입력하세요",
        }),
    )

    def clean(self):
        """링크가 1개 이상 입력되는지 확인"""
        cleaned_data = super().clean()
        has_link = any([
            cleaned_data.get("notion_url"),
            cleaned_data.get("figma_url"),
            cleaned_data.get("github_url"),
        ])
        if not has_link:
            raise forms.ValidationError("최소 1개 이상의 링크를 입력해주세요.")
        return cleaned_data

    def to_dict(self):
        """폼 데이터를 딕셔너리로 변환 (JSONField용)"""
        if not self.is_valid():
            return {}
        
        return {
            "notion": self.cleaned_data.get("notion_url") or None,
            "figma": self.cleaned_data.get("figma_url") or None,
            "github": self.cleaned_data.get("github_url") or None,
        }
