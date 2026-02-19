from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import ngettext

from .models import Team, TeamMember


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    fields = ["user", "role", "is_active", "joined_at", "left_at"]
    readonly_fields = ["joined_at"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "project", "created_at"]
    search_fields = ["name", "project__title"]
    ordering = ["-created_at"]
    inlines = [TeamMemberInline]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "user", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__nickname", "team__name"]
    ordering = ["-joined_at"]
    actions = ["deactivate_members", "reactivate_members"]
    
    def deactivate_members(self, request, queryset):
        """팀 멤버 비활성화 (탈퇴 처리)"""
        now = timezone.now()
        count = 0
        
        for member in queryset.filter(is_active=True):
            member.is_active = False
            member.left_at = now
            member.save()
            count += 1
        
        self.message_user(
            request,
            ngettext(
                f"{count}명이 팀에서 제거되었습니다.",
                f"{count}명이 팀에서 제거되었습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    deactivate_members.short_description = "🚪 선택된 멤버 비활성화 (탈퇴)"
    
    def reactivate_members(self, request, queryset):
        """팀 멤버 재활성화"""
        count = queryset.filter(is_active=False).update(is_active=True, left_at=None)
        self.message_user(
            request,
            ngettext(
                f"{count}명이 팀에 재입장했습니다.",
                f"{count}명이 팀에 재입장했습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    reactivate_members.short_description = "🔄 선택된 멤버 재활성화"
