from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ngettext
from django.contrib import messages

from .models import User, Role, UserRoleLevel, TechStack, Report


class UserRoleLevelInline(admin.TabularInline):
    model = UserRoleLevel
    extra = 0
    fields = ["role", "level", "last_diagnosed_at"]
    readonly_fields = ["last_diagnosed_at"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["id", "username", "nickname", "email", "passion_level", "team_ban_count", "email_notifications_enabled", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_active", "created_at", "passion_level"]
    search_fields = ["username", "nickname", "email"]
    ordering = ["-created_at"]
    inlines = [UserRoleLevelInline]
    actions = ["clear_passion_level", "clear_team_ban", "ban_user"]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ("프로필 정보", {"fields": ("nickname", "profile_image", "bio", "tech_stacks")}),
        ("알림 설정", {"fields": ("email_notifications_enabled",)}),
        ("관리 정보", {"fields": ("passion_level", "team_ban_count")}),
    )
    
    def clear_passion_level(self, request, queryset):
        """열정 레벨 초기화"""
        count = queryset.update(passion_level=None)
        self.message_user(
            request,
            ngettext(
                f"{count}명의 열정 레벨이 초기화되었습니다.",
                f"{count}명의 열정 레벨이 초기화되었습니다.",
                count,
            ),
        )
    clear_passion_level.short_description = "🔄 선택된 사용자의 열정 레벨 초기화"
    
    def clear_team_ban(self, request, queryset):
        """팀 밴 횟수 초기화"""
        count = queryset.update(team_ban_count=0)
        self.message_user(
            request,
            ngettext(
                f"{count}명의 팀플 금지가 해제되었습니다.",
                f"{count}명의 팀플 금지가 해제되었습니다.",
                count,
            ),
        )
    clear_team_ban.short_description = "🔓 선택된 사용자의 팀플 금지 해제"
    
    def ban_user(self, request, queryset):
        """사용자에게 팀 밴 1회 추가"""
        count = 0
        for user in queryset:
            user.team_ban_count += 1
            user.save()
            count += 1
        self.message_user(
            request,
            ngettext(
                f"{count}명에게 팀플 금지 1회가 추가되었습니다.",
                f"{count}명에게 팀플 금지 1회가 추가되었습니다.",
                count,
            ),
        )
    ban_user.short_description = "⛔ 선택된 사용자에게 팀 밴 1회 추가"


@admin.register(TechStack)
class TechStackAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "category", "user_count", "created_at"]
    list_filter = ["category"]
    search_fields = ["name"]
    ordering = ["category", "name"]
    fieldsets = [
        ("기본 정보", {"fields": ["name", "category"]}),
    ]
    
    def get_queryset(self, request):
        """N+1 쿼리 최적화: annotate로 user_count 미리 계산"""
        from django.db.models import Count
        queryset = super().get_queryset(request)
        return queryset.annotate(_user_count=Count('users', distinct=True))
    
    def user_count(self, obj):
        """annotate된 _user_count 사용 (DB 쿼리 없음)"""
        return obj._user_count
    user_count.short_description = "사용자 수"


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "name", "created_at"]
    search_fields = ["code", "name"]
    ordering = ["code"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "reporter", "reported_user", "reason_preview", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["reporter__nickname", "reported_user__nickname", "reason"]
    ordering = ["-created_at"]
    actions = ["approve_and_ban"]
    readonly_fields = ["reporter", "reported_user", "reason", "created_at"]
    
    def reason_preview(self, obj):
        """신고 사유 미리보기 (50자)"""
        return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
    reason_preview.short_description = "신고 사유"
    
    def approve_and_ban(self, request, queryset):
        """신고 승인 및 피신고자 밴"""
        pending_reports = queryset.filter(status=Report.Status.PENDING)
        count = 0
        
        for report in pending_reports:
            # 피신고자에게 팀 밴 2회 추가
            report.reported_user.team_ban_count += 2
            # TODO 팀에서 피신고자 제거하기 
            
            report.reported_user.save()
            
            # 신고 상태 업데이트
            report.status = Report.Status.APPROVED
            report.admin_note = f"관리자 일괄 처리: {request.user.username}"
            report.save()
            count += 1
        
        self.message_user(
            request,
            ngettext(
                f"{count}명이 밴 처리되었습니다.",
                f"{count}명이 밴 처리되었습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    approve_and_ban.short_description = "✅ 신고 승인 및 피신고자 밴"


@admin.register(UserRoleLevel)
class UserRoleLevelAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "role", "level", "last_diagnosed_at", "updated_at"]
    list_filter = ["role", "level"]
    search_fields = ["user__nickname", "user__username"]
    ordering = ["-updated_at"]
