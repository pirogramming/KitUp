from rest_framework import serializers
from .models import Team, TeamMember


class TeamMemberSerializer(serializers.ModelSerializer):
    """팀 멤버 Serializer"""
    username = serializers.CharField(source='user.nickname', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = TeamMember
        fields = ['id', 'team', 'user', 'username', 'role', 'role_code', 'role_name', 'is_active', 'joined_at', 'left_at']
        read_only_fields = ['id', 'joined_at']


class TeamSerializer(serializers.ModelSerializer):
    """팀 기본 Serializer"""
    members = TeamMemberSerializer(many=True, read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'project', 'project_title',
            'created_at', 'members', 'member_count'
        ]
        read_only_fields = ['id', 'created_at']

    def get_member_count(self, obj) -> int:
        return obj.members.filter(is_active=True).count()


class TeamCreateSerializer(serializers.ModelSerializer):
    """팀 생성용 Serializer"""

    class Meta:
        model = Team
        fields = ['id', 'name', 'project']
        read_only_fields = ['id']
