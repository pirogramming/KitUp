from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import ngettext

from .models import Season, Project, ProjectApplication
from .services import TeamMatchingService


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "is_active", "matching_start", "matching_end", "project_start", "project_end"]
    list_filter = ["status", "is_active", "created_at"]
    search_fields = ["name"]
    ordering = ["-created_at"]
    actions = ["activate_season", "deactivate_season", "run_team_matching"]
    
    def activate_season(self, request, queryset):
        """시즌 활성화 (이전 활성 시즌은 자동 비활성화)"""
        # 모든 시즌 비활성화
        Season.objects.all().update(is_active=False)
        # 선택된 시즌만 활성화
        queryset.update(is_active=True)
        self.message_user(request, "시즌이 활성화되었습니다.")
    
    def deactivate_season(self, request, queryset):
        """시즌 비활성화"""
        queryset.update(is_active=False)
        self.message_user(request, "시즌이 비활성화되었습니다.")
    
    def run_team_matching(self, request, queryset):
        """팀 매칭 알고리즘 실행"""
        for season in queryset:
            try:
                result = TeamMatchingService.run_matching(season.id)
                self.message_user(
                    request,
                    f"✅ [{season.name}] 팀 매칭 완료: "
                    f"{result['teams_created']}팀 생성, "
                    f"{result['total_matched']}명 매칭",
                    messages.SUCCESS,
                )
            except ValidationError as e:
                self.message_user(
                    request,
                    f"❌ [{season.name}] 팀 매칭 실패: {str(e)}",
                    messages.ERROR,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"❌ [{season.name}] 팀 매칭 오류: {str(e)}",
                    messages.ERROR,
                )
    run_team_matching.short_description = "🤝 팀 매칭 알고리즘 실행"
    
    activate_season.short_description = "✅ 선택된 시즌 활성화"
    deactivate_season.short_description = "❌ 선택된 시즌 비활성화"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "owner", "status", "duration_weeks", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]
    actions = [
        "change_status_to_open",
        "change_status_to_matched",
        "change_status_to_in_progress",
        "change_status_to_completed",
        "change_status_to_archived",
    ]
    
    def change_status_to_open(self, request, queryset):
        """상태 변경: 모집중"""
        count = queryset.update(status=Project.Status.OPEN)
        self.message_user(
            request,
            ngettext(
                f"{count}개 프로젝트가 '모집중' 상태로 변경되었습니다.",
                f"{count}개 프로젝트가 '모집중' 상태로 변경되었습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    change_status_to_open.short_description = "📢 상태 변경: 모집중"
    
    def change_status_to_matched(self, request, queryset):
        """상태 변경: 매칭완료"""
        count = queryset.update(status=Project.Status.MATCHED)
        self.message_user(
            request,
            ngettext(
                f"{count}개 프로젝트가 '매칭완료' 상태로 변경되었습니다.",
                f"{count}개 프로젝트가 '매칭완료' 상태로 변경되었습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    change_status_to_matched.short_description = "✅ 상태 변경: 매칭완료"
    
    def change_status_to_in_progress(self, request, queryset):
        """상태 변경: 진행중"""
        count = queryset.update(status=Project.Status.IN_PROGRESS)
        self.message_user(
            request,
            ngettext(
                f"{count}개 프로젝트가 '진행중' 상태로 변경되었습니다.",
                f"{count}개 프로젝트가 '진행중' 상태로 변경되었습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    change_status_to_in_progress.short_description = "⚙️ 상태 변경: 진행중"
    
    def change_status_to_completed(self, request, queryset):
        """상태 변경: 완료"""
        count = queryset.update(status=Project.Status.COMPLETED)
        self.message_user(
            request,
            ngettext(
                f"{count}개 프로젝트가 '완료' 상태로 변경되었습니다.",
                f"{count}개 프로젝트가 '완료' 상태로 변경되었습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    change_status_to_completed.short_description = "🎉 상태 변경: 완료"
    
    def change_status_to_archived(self, request, queryset):
        """상태 변경: 보관됨"""
        count = queryset.update(status=Project.Status.ARCHIVED)
        self.message_user(
            request,
            ngettext(
                f"{count}개 프로젝트가 '보관됨' 상태로 변경되었습니다.",
                f"{count}개 프로젝트가 '보관됨' 상태로 변경되었습니다.",
                count,
            ),
            messages.SUCCESS,
        )
    change_status_to_archived.short_description = "📦 상태 변경: 보관됨"


@admin.register(ProjectApplication)
class ProjectApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "user", "role", "passion_level", "status", "applied_at"]
    list_filter = ["status", "role", "passion_level"]
    search_fields = ["project__title", "user__nickname"]
    ordering = ["-applied_at"]
