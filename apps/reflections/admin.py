from django.contrib import admin

from .models import Retrospective


@admin.register(Retrospective)
class RetrospectiveAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "user", "title", "created_at", "updated_at"]
    list_filter = ["created_at", "project"]
    search_fields = ["title", "user__nickname", "project__title"]
    ordering = ["-created_at"]
