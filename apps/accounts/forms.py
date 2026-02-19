from django import forms
import re
from .models import User, TechStack


# ============ 공통 Validator ============
class NicknameValidator:
    """닉네임 검증 로직 통합"""
    MIN_LENGTH = 2
    MAX_LENGTH = 20
    PATTERN = r'^[a-zA-Z0-9가-힣_-]+$'
    
    @staticmethod
    def validate(nickname, exclude_user_pk=None):
        """
        닉네임 검증 (길이 + 패턴 + 중복)
        
        Args:
            nickname: 검증할 닉네임
            exclude_user_pk: 제외할 사용자 PK (프로필 수정 시)
            
        Returns:
            (valid, message) 튜플
        """
        nickname = (nickname or "").strip()
        
        # 필수값 확인
        if not nickname:
            return False, "닉네임은 필수입니다."
        
        # 길이 검증
        if len(nickname) < NicknameValidator.MIN_LENGTH:
            return False, f"닉네임은 최소 {NicknameValidator.MIN_LENGTH}자 이상이어야 합니다."
        if len(nickname) > NicknameValidator.MAX_LENGTH:
            return False, f"닉네임은 최대 {NicknameValidator.MAX_LENGTH}자 이하여야 합니다."
        
        # 특수문자 검증
        if not re.match(NicknameValidator.PATTERN, nickname):
            return False, "닉네임은 한글, 영문, 숫자, 밑줄(_), 하이픈(-)만 사용 가능합니다."
        
        # 중복 검증
        query = User.objects.filter(nickname=nickname)
        if exclude_user_pk:
            query = query.exclude(pk=exclude_user_pk)
        
        if query.exists():
            return False, "이미 사용 중인 닉네임입니다."
        
        return True, "사용 가능한 닉네임입니다."


# ============ Forms ============


class OnboardingForm(forms.ModelForm):
    tech_stacks = forms.ModelMultipleChoiceField(
        queryset=TechStack.objects.all().order_by("category", "name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="기술 스택 (선택)",
        help_text="보유한 기술을 선택하세요",
    )

    class Meta:
        model = User
        fields = ["nickname", "github_id", "profile_image", "tech_stacks"]
        widgets = {
            "nickname": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "닉네임을 입력하세요",
            }),
            "github_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "GitHub 아이디 (선택)",
            }),
            "profile_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tech_stacks"].initial = self.instance.tech_stacks.all()

    def clean_nickname(self):
        nick = self.cleaned_data.get("nickname") or ""
        valid, message = NicknameValidator.validate(nick, self.instance.pk)
        if not valid:
            raise forms.ValidationError(message)
        return nick.strip()

    def clean_github_id(self):
        github_id = (self.cleaned_data.get("github_id") or "").strip()
        if github_id and User.objects.filter(github_id=github_id).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("이미 등록된 GitHub 아이디입니다.")
        return github_id or None

    def save(self, commit=True):
        user = super().save(commit=False)
        # Always save user record first (with profile_image)
        user.save()
        if "tech_stacks" in self.cleaned_data:
            user.tech_stacks.set(self.cleaned_data.get("tech_stacks", []))
        return user


class ProfileUpdateForm(forms.ModelForm):
    tech_stacks = forms.ModelMultipleChoiceField(
        queryset=TechStack.objects.all().order_by("category", "name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="기술 스택 (선택)",
        help_text="보유한 기술을 선택하세요",
    )

    class Meta:
        model = User
        fields = ["nickname", "github_id", "profile_image", "bio", "tech_stacks"]
        widgets = {
            "nickname": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "닉네임을 입력하세요",
            }),
            "github_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "GitHub 아이디 (선택)",
            }),
            "profile_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "bio": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "자기소개를 입력하세요",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tech_stacks"].initial = self.instance.tech_stacks.all()

    def clean_nickname(self):
        nick = self.cleaned_data.get("nickname") or ""
        valid, message = NicknameValidator.validate(nick, self.instance.pk)
        if not valid:
            raise forms.ValidationError(message)
        return nick.strip()

    def clean_github_id(self):
        github_id = (self.cleaned_data.get("github_id") or "").strip()
        if github_id and User.objects.filter(github_id=github_id).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("이미 등록된 GitHub 아이디입니다.")
        return github_id or None

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            if "tech_stacks" in self.cleaned_data:
                user.tech_stacks.set(self.cleaned_data.get("tech_stacks", []))
        return user
