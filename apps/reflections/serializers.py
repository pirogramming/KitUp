# reflections/serializers.py
from rest_framework import serializers
from .models import Retrospective, RetrospectiveAsset 
from .services.retrospective_guide import load_guide, build_markdown


class RetrospectiveReadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.nickname", read_only=True)
    project_id = serializers.IntegerField(source="project.id", read_only=True)

    class Meta:
        model = Retrospective
        fields = [
            "id",
            "project_id",
            "user",
            "username",
            "title",
            "template_key",
            "answers_json",
            "content_md",
            "bookmarked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", 
            "project_id",
            "user", 
            "username", 
            "created_at", 
            "updated_at"
        ]
    def validate_content_md(self, value):
        if not value.strip():
            raise serializers.ValidationError("내용은 비어 있을 수 없습니다.")
        return value


class RetrospectiveWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retrospective
        fields = (
            "id",
            "project",
            "title",
            "template_key",
            "answers_json",
            "bookmarked",
        )
        extra_kwargs = {
            "template_key": {"required": False},
            "answers_json": {"required": False},
        }

    def validate_answers_json(self, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise serializers.ValidationError("answers_json은 객체(JSON dict)여야 합니다.")
        return v

    def _rebuild_content_md(self, instance_or_data: dict, template_key: str, answers_json: dict, title: str | None):
        guide = load_guide(template_key)
        return build_markdown(guide, answers_json, title=title)

    def create(self, validated_data):
        template_key = validated_data.get("template_key") or "compact"
        answers_json = validated_data.get("answers_json") or {}
        title = validated_data.get("title")

        validated_data["content_md"] = self._rebuild_content_md(
            validated_data, template_key, answers_json, title
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 기존 값과 병합해서 md 재생성
        template_key = validated_data.get("template_key", instance.template_key or "compact")
        answers_json = validated_data.get("answers_json", instance.answers_json or {})
        title = validated_data.get("title", instance.title)

        validated_data["content_md"] = self._rebuild_content_md(
            validated_data, template_key, answers_json, title
        )
        return super().update(instance, validated_data)
    
class RetrospectiveAssetUploadSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    md = serializers.SerializerMethodField()

    class Meta:
        model = RetrospectiveAsset
        fields = ["id", "alt_text", "image", "url", "md", "created_at"]
        read_only_fields = ["id", "url", "md", "created_at"]

    def get_url(self, obj):
        return obj.image.url if obj.image else ""

    def get_md(self, obj):
        alt = obj.alt_text or "image"
        url = self.get_url(obj)
        return f"![{alt}]({url})" if url else ""