from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_GET

from .forms import OnboardingForm, ProfileUpdateForm
from .models import Role, User, UserRoleLevel


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
    nickname = request.GET.get("nickname", "").strip()
    current_user_id = request.GET.get("user_id")  # 프로필 수정 시 자신의 닉네임 제외
    
    if not nickname:
        return JsonResponse({"available": False, "message": "닉네임을 입력해주세요."})
    
    # 길이 검증 (2-20자)
    if len(nickname) < 2:
        return JsonResponse({"available": False, "message": "닉네임은 최소 2자 이상이어야 합니다."})
    
    if len(nickname) > 20:
        return JsonResponse({"available": False, "message": "닉네임은 최대 20자 이하여야 합니다."})
    
    # 특수문자 검증 (한글, 영문, 숫자, 밑줄, 하이픈만 허용)
    import re
    if not re.match(r'^[a-zA-Z0-9가-힣_-]+$', nickname):
        return JsonResponse({"available": False, "message": "닉네임은 한글, 영문, 숫자, 밑줄(_), 하이픈(-)만 사용 가능합니다."})
    
    # 중복 확인 (현재 사용자는 제외)
    query = User.objects.filter(nickname=nickname)
    if current_user_id:
        query = query.exclude(pk=current_user_id)
    
    if query.exists():
        return JsonResponse({"available": False, "message": "이미 사용 중인 닉네임입니다."})
    
    return JsonResponse({"available": True, "message": "사용 가능한 닉네임입니다."})


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
def level_submit(request):
    """
    레벨 테스트 결과 제출 처리
    
    - POST 요청으로 역할 코드(role_code)와 레벨(level)을 전달받음
    - UserRoleLevel 모델에 결과 저장 또는 업데이트
    - 제출 후 테스트 결과 페이지로 리다이렉트
    """
    if request.method != "POST":
        return HttpResponseBadRequest("잘못된 요청입니다.")
    
    role_code = request.POST.get("role")
    role = get_object_or_404(Role, code=role_code)
    level = request.POST.get("level")
    
    UserRoleLevel.objects.update_or_create(
        user=request.user,
        role=role,
        defaults={
            "level": int(level),
            "last_diagnosed_at": timezone.now(),
        },
    )
    
    return redirect(f"{reverse('accounts:test_result')}?role={role_code}")

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
