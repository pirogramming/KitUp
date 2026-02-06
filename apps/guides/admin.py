from django.contrib import admin

from .models import GuideCard, GuideTask, GuideTaskProgress, ProjectProgress


class GuideTaskInline(admin.TabularInline):
    model = GuideTask
    extra = 0
    fields = ["title", "description", "order_no", "is_required"]


@admin.register(GuideCard)
class GuideCardAdmin(admin.ModelAdmin):
    list_display = ["id", "role", "order_no", "title", "is_active", "created_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["title"]
    ordering = ["role", "order_no"]
    inlines = [GuideTaskInline]


@admin.register(GuideTask)
class GuideTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "card", "title", "order_no", "is_required"]
    list_filter = ["is_required", "card__role"]
    search_fields = ["title"]
    ordering = ["card__role", "card__order_no", "order_no"]


@admin.register(GuideTaskProgress)
class GuideTaskProgressAdmin(admin.ModelAdmin):
    list_display = ["id", "task", "project", "is_completed", "completed_at"]
    list_filter = ["is_completed", "project"]
    search_fields = ["task__title", "project__title"]
    ordering = ["-updated_at"]


@admin.register(ProjectProgress)
class ProjectProgressAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "role", "completed_tasks", "total_tasks", "progress_percent"]
    list_filter = ["role", "project"]
    search_fields = ["project__title"]
    ordering = ["-updated_at"]
