import json
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .forms import OnboardingForm, ProfileUpdateForm
from .models import Role, User, UserRoleLevel, Report
from .serializers import ReportCreateRequestSerializer, ReportCreateResponseSerializer


@require_GET
def check_username(request):
    """아이디 중복 확인 API"""
    username = request.GET.get("username", "").strip()
    
    if not username:
        return JsonResponse({"available": False, "message": "아이디를 입력해주세요."})
    
    if len(username) < 4:
        return JsonResponse({"available": False, "message": "아이디는 4자 이상이어야 합니다."})
    
    if User.objects.filter(username=username).exists():
        return JsonResponse({"available": False, "message": "이미 사용 중인 아이디입니다."})
    
    return JsonResponse({"available": True, "message": "사용 가능한 아이디입니다."})


@require_GET
def check_email(request):
    """이메일 중복 확인 API"""
    email = request.GET.get("email", "").strip()
    
    if not email:
        return JsonResponse({"available": False, "message": "이메일을 입력해주세요."})
    
    if User.objects.filter(email=email).exists():
        return JsonResponse({"available": False, "message": "이미 사용 중인 이메일입니다."})
    
    return JsonResponse({"available": True, "message": "사용 가능한 이메일입니다."})


@require_GET
def check_nickname(request):
    """닉네임 중복 확인 API"""
    from .forms import NicknameValidator
    
    nickname = request.GET.get("nickname", "").strip()
    user_id = request.GET.get("user_id")  # 프로필 수정 시 자신의 닉네임 제외
    
    valid, message = NicknameValidator.validate(nickname, exclude_user_pk=user_id)
    
    return JsonResponse({
        "available": valid,
        "message": message,
    })


@login_required
def level_test(request):
    """
    레벨 진단 테스트 페이지 렌더링
    
    - 특정 역할(role_code)에 대한 테스트를 진행
    - role_code는 GET 파라미터로 전달받음 -> 프론트에서 설정 필요
    - 'account/level_test.html' 템플릿을 렌더링
    """
    role_code = request.GET.get("role")
    context = {"role_code": role_code}
    return render(request, "account/level_test.html", context)

@login_required
@require_POST
def level_submit(request):
    """
    레벨 테스트 결과 제출 처리 (API)
    
    - POST 요청으로 track(역할 코드), level, total_score, answers를 JSON으로 받음
    - UserRoleLevel 모델에 결과 저장 또는 업데이트
    - JSON 응답으로 success 여부 반환
    """
    try:
        data = json.loads(request.body)
        role_code = data.get("track")
        level = data.get("level")
        
        if not role_code or level is None:
            return JsonResponse({"success": False, "error": "필수 데이터가 없습니다."})
        
        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            return JsonResponse({"success": False, "error": f"역할을 찾을 수 없습니다: {role_code}"})
        
        UserRoleLevel.objects.update_or_create(
            user=request.user,
            role=role,
            defaults={
                "level": int(level),
                "last_diagnosed_at": timezone.now(),
            },
        )
        
        return JsonResponse({"success": True})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "잘못된 JSON 형식입니다."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": "오류가 발생했습니다."})
        return JsonResponse({"success": False, "error": str(e)})

@login_required
def test_result(request):
    """
    레벨 테스트 결과
    
    - 특정 역할(role_code)에 대한 사용자의 레벨 정보를 조회
    - 'test/test_result.html' 템플릿을 렌더링
    - 템플릿에 사용자 정보, 역할명, 레벨 전달
    """
    role_code = request.GET.get("role")

    role = get_object_or_404(Role, code=role_code)
    url_level = (
        UserRoleLevel.objects.filter(user=request.user, role=role)
        .select_related("role")
        .first()
    )

    context = {
        "user_obj": request.user,
        "role": role,  # role.name 출력 가능
        "level": url_level.level if url_level else None,
    }
    return render(request, "account/test_result.html", context)


@login_required
def profile_edit(request):
    """프로필 수정"""
    if request.method == "POST":
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "프로필이 수정되었습니다.")
            return redirect("accounts:mypage")
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {"form": form}
    return render(request, "account/profile_edit.html", context)


@login_required
def onboarding_profile(request):
    """온보딩: 최초 프로필 설정"""
    if request.method == "POST":
        form = OnboardingForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            return redirect("/")
    else:
        form = OnboardingForm(instance=request.user)

    context = {"form": form}
    return render(request, "account/onboarding_profile.html", context)


@login_required
def mypage(request):
    """
    마이페이지 조회 뷰

    - 로그인한 사용자의 정보, 역할 레벨, 팀 프로젝트 참여 내역 등을 조회
    - 'account/mypage.html' 템플릿을 렌더링
    - 프로젝트 내역은 team_memberships -> team -> project 경로로 조회한다.
    """

    user = request.user

    # 역할별 스킬 레벨 (user_role_levels + roles)
    role_levels = user.role_levels.select_related("role").all()

    # 팀 프로젝트 참여 내역 (team_memberships + role + team + project)
    memberships = (
        user.team_memberships
            .select_related("team__project", "role")
            .order_by("-joined_at")
    )

    context = {
        "user_obj": user,
        "role_levels": role_levels,
        "memberships": memberships,
    }
    return render(request, "account/mypage.html", context)


@login_required
def withdraw(request):
    """회원 탈퇴"""
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "회원 탈퇴가 완료되었습니다.")
        return redirect("/")

    return render(request, "account/withdraw.html")

@extend_schema(
    tags=["Accounts"],
    summary="유저 신고 생성",
    request=ReportCreateRequestSerializer,
    responses={201: ReportCreateResponseSerializer, 400: None, 409: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_report(request):
    ser = ReportCreateRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    reported_user_id = ser.validated_data["reported_user_id"]
    reason = ser.validated_data["reason"]

    if not reported_user_id:
        return JsonResponse({"ok": False, "error": "reported_user_id is required"}, status=400)
    if not reason:
        return JsonResponse({"ok": False, "error": "reason is required"}, status=400)

    reported_user = get_object_or_404(User, pk=reported_user_id)

    # 자기 자신 신고 방지
    if reported_user.id == request.user.id:
        return JsonResponse({"ok": False, "error": "cannot report yourself"}, status=400)

    # (선택) 동일 대상 중복 신고 방지: 대기중(PENDING) 하나만 허용 같은 정책
    if Report.objects.filter(
        reporter=request.user,
        reported_user=reported_user,
        status=Report.Status.PENDING,
    ).exists():
        return JsonResponse({"ok": False, "error": "already reported (pending)"}, status=409)

    report = Report.objects.create(
        reporter=request.user,
        reported_user=reported_user,
        reason=reason,
    )

    return JsonResponse({"ok": True, "report_id": report.id}, status=201)



@login_required   
def mypage(request):
    user = request.user

    qs = user.role_levels.select_related("role").all()
    role_levels = {x.role.code.upper(): x.level for x in qs}  # {"FRONTEND": 3, ...}

    memberships = (
        user.team_memberships
        .select_related("team__project", "role")
        .order_by("-joined_at")
    )

    return render(request, "account/mypage.html", {
        "user_obj": user,
        "role_levels": role_levels,
        "memberships": memberships,
    })

