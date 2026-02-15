from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


from rest_framework import viewsets
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.accounts.models import Role, UserRoleLevel
from apps.projects.models import Season

from .models import Team, TeamMember
from .serializers import TeamSerializer, TeamCreateSerializer, TeamMemberSerializer


# ================================
# Template Views (HTML 렌더링)
# ================================

@login_required
@require_POST
def enable_email_notifications(request):
    """
    사용자의 이메일 알림을 활성화하고 team_apply로 리다이렉트
    """
    user = request.user
    user.email_notifications_enabled = True
    user.save()
    
    messages.success(request, "✅ 알림을 활성화했습니다.")
    return redirect("teams:team_apply")


@login_required
def team_matching_router(request):
    """
    사용자의 상태를 확인하여 매칭 신청 페이지 또는 결과 페이지로 보냄
    """
    season = Season.get_active_season()
    
    # 1. 사용자가 이미 팀에 속해 있는지 확인
    user_has_team = TeamMember.objects.filter(user=request.user).exists()
    
    # 2. 팀이 있다면 결과 페이지(team.html)로 이동
    if user_has_team:
        return redirect('teams:team_status')
    
    # 3. 팀이 없다면 신청 페이지(team_apply.html)로 이동
    return redirect('teams:team_apply')

@login_required
def team_apply(request):
    """
    팀 매칭 신청 페이지
    
    - 활성화된 시즌 확인
    - 팀매칭 기간인지 확인
    - 유저의 역할별 레벨 정보를 함께 전달
    - 'teams/team_apply.html' 템플릿을 렌더링
    - 딕셔너리 형태로 역할 코드와 UserRoleLevel 객체 전달
    - is_matching_period 플래그로 분기 처리
    """
    user = request.user
    season = Season.get_active_season()

    # 유저의 역할별 레벨
    role_levels = (
        UserRoleLevel.objects
        .filter(user=user)
        .select_related("role")
    )

    role_level_map = {
        rl.role.code: rl.level
        for rl in role_levels
    }
    
    # 팀 매칭 기간 여부
    is_matching_period = season and season.is_matching_period() if season else False

    context = {
        "user_obj": user,
        "role_levels": role_level_map,
        "season": season,
        "is_matching_period": is_matching_period,
    }

    return render(request, "teams/team_apply.html", context)


@login_required
def passion_test(request):
    """
    열정 테스트 페이지
    
    - 열정 레벨이 이미 있으면 team_status로 리다이렉트
    - 없으면 'teams/passion_test.html' 템플릿을 렌더링
    - URL 파라미터 ?role=PM|FRONTEND|BACKEND에서 선택 역할 받음
    """
    if request.user.passion_level:
        # 이미 열정 테스트 완료
        return redirect("teams:team_status")
    
    # URL 파라미터에서 role 받기
    role = request.GET.get("role", "")
    
    context = {
        "role": role,
    }
    
    return render(request, "teams/passion_test.html", context)

@login_required
@require_POST
def passion_submit_api(request):
    """
    열정 테스트 결과 제출 처리 (API)
    
    - POST 요청으로 passion_level과 role(선호 직군)을 JSON으로 받음
    - User 모델에 열정 레벨과 선호 역할 저장
    - JSON 응답으로 success 여부 반환
    """
    try:
        data = json.loads(request.body)
        passion_level = data.get("passion_level")
        role_code = data.get("role")  # PM, FRONTEND, BACKEND
        
        if passion_level is None:
            return JsonResponse({"success": False, "error": "필수 데이터가 없습니다."})
        
        request.user.passion_level = int(passion_level)
        
        # preferred_role 저장
        if role_code:
            try:
                from apps.accounts.models import Role
                role = Role.objects.get(code=role_code)
                request.user.preferred_role = role
            except Role.DoesNotExist:
                pass  # 역할이 없으면 무시
        
        request.user.save(update_fields=["passion_level", "preferred_role"])
        
        return JsonResponse({"success": True})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "잘못된 JSON 형식입니다."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def passion_submit(request):
    """
    열정 테스트 결과 제출 처리
    
    - POST 요청으로 열정 레벨(passion_level)과 역할(role)을 전달받음
    - User 모델에 열정 레벨과 선호 역할 저장
    - 제출 후 팀 매칭 결과 페이지로 리다이렉트
    """
    if request.method != "POST":
        return HttpResponseBadRequest("잘못된 요청입니다.")
    
    passion_level = request.POST.get("passion_level")
    role_code = request.POST.get("role")  # PM, FRONTEND, BACKEND
    
    request.user.passion_level = int(passion_level)
    
    # preferred_role 저장
    if role_code:
        try:
            from apps.accounts.models import Role
            role = Role.objects.get(code=role_code)
            request.user.preferred_role = role
        except Role.DoesNotExist:
            pass  # 역할이 없으면 무시
    
    request.user.save(update_fields=["passion_level", "preferred_role"])
    
    return redirect("teams:team_status")

@login_required
def team_matching_cancel(request):
    """
    팀 매칭 신청 취소
    
    - 팀 매칭 기간 중에만 취소 가능
    - 프로젝트 기간이면 취소 불가능
    - 사용자의 TeamMember 레코드 삭제
    - passion_level을 NULL로 초기화 (다시 열정 테스트 강제)
    """
    if request.method != "POST":
        return HttpResponseBadRequest("잘못된 요청입니다.")
    
    season = Season.get_active_season()
    
    # 팀 매칭 기간이 아니면 취소 불가능
    if not season or not season.is_matching_period():
        messages.error(request, "❌ 팀 매칭 기간이 아닙니다. 취소할 수 없습니다.")
        return redirect("teams:team_status")
    
    # 열정 레벨, preferred_role 초기화 및 이메일 알림 비활성화
    request.user.passion_level = None
    request.user.preferred_role = None
    request.user.email_notifications_enabled = False
    request.user.save(update_fields=["passion_level", "preferred_role", "email_notifications_enabled"])
    
    messages.success(request, "✅ 팀 매칭 신청이 취소되었습니다.")
    return redirect("teams:team_apply")


@login_required
def team_status(request):
    """
    팀 매칭 결과/대기 페이지
    
    - 팀 매칭 기간: 매칭 대기 화면
    - 프로젝트 기간: 팀원 정보 화면
    - 'teams/team.html' 템플릿을 렌더링
    - is_matching_period 플래그로 분기 처리
    - 팀 매칭 여부(team_matched) 전달
    """
    season = Season.get_active_season()
    team = None
    team_members_data = []
    team_matched = False
    
    if season:
        # 현재 사용자의 팀 조회
        team = Team.objects.filter(
            members__user=request.user
        ).prefetch_related(
            'members__user',
            'members__role'
        ).distinct().first()
        
        # 팀이 존재하면 매칭됨
        team_matched = team is not None
        
        # 프로젝트 기간에만 팀원 정보 수집
        if team and season.is_project_period():
            for member in team.members.all():
                # 해당 역할의 레벨 조회
                role_level = UserRoleLevel.objects.filter(
                    user=member.user,
                    role=member.role
                ).first()
                
                team_members_data.append({
                    'user': member.user,
                    'role': member.role,
                    'level': role_level.level if role_level else None,
                })
    
    context = {
        "season": season,
        "team": team,
        "team_members": team_members_data,
        "is_matching_period": season.is_matching_period() if season else False,
        "team_matched": team_matched,  # ✅ 팀 매칭 여부
    }
    return render(request, "teams/team.html", context)


# ================================
# API Views (DRF ViewSets)
# ================================


@extend_schema_view(
    list=extend_schema(summary="팀 목록 조회", tags=["Teams"]),
    retrieve=extend_schema(summary="팀 상세 조회", tags=["Teams"]),
    create=extend_schema(summary="팀 생성", tags=["Teams"]),
    update=extend_schema(summary="팀 전체 수정", tags=["Teams"]),
    partial_update=extend_schema(summary="팀 부분 수정", tags=["Teams"]),
    destroy=extend_schema(summary="팀 삭제", tags=["Teams"]),
)
class TeamViewSet(viewsets.ModelViewSet):
    """팀 CRUD API"""
    queryset = Team.objects.all().prefetch_related('members__user', 'members__role')

    def get_serializer_class(self):
        if self.action == 'create':
            return TeamCreateSerializer
        return TeamSerializer


@extend_schema_view(
    list=extend_schema(summary="팀 멤버 목록 조회", tags=["Team Members"]),
    retrieve=extend_schema(summary="팀 멤버 상세 조회", tags=["Team Members"]),
    create=extend_schema(summary="팀 멤버 추가", tags=["Team Members"]),
    update=extend_schema(summary="팀 멤버 전체 수정", tags=["Team Members"]),
    partial_update=extend_schema(summary="팀 멤버 부분 수정", tags=["Team Members"]),
    destroy=extend_schema(summary="팀 멤버 삭제", tags=["Team Members"]),
)
class TeamMemberViewSet(viewsets.ModelViewSet):
    """팀 멤버 CRUD API"""
    queryset = TeamMember.objects.all().select_related('team', 'user', 'role')
    serializer_class = TeamMemberSerializer
