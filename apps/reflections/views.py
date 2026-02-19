from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from .models import Retrospective, RetrospectiveAsset
from .serializers import (
    RetrospectiveReadSerializer,
    RetrospectiveWriteSerializer,
    RetrospectiveAssetUploadSerializer, 
)
from .services.retrospective_guide import load_guide, build_markdown

from apps.projects.models import Project
from apps.teams.models import TeamMember


def _get_my_projects_and_roles(user):
    """
    내 프로젝트와 프로젝트에서의 내 역할 찾기
    """
    my_project_ids = (
        TeamMember.objects
        .filter(user=user)
        .values_list("team__project_id", flat=True)
        .distinct()
    )

    my_projects = (
        Project.objects
        .filter(Q(id__in=my_project_ids) | Q(owner=user))
        .order_by("title")
    )

    # 프로젝트별 내 role 코드(TeamMember.role.code) 매핑
    role_map = {}
    tm_qs = (
        TeamMember.objects
        .filter(user=user, team__project__in=my_projects)
        .select_related("role", "team__project")
    )
    for tm in tm_qs:
        pid = tm.team.project_id
        # 같은 프로젝트에 팀멤버가 여러개면(이상 케이스) 첫 값 유지
        role_map.setdefault(pid, getattr(tm.role, "code", None))

    return my_projects, role_map


@login_required
def note_list(request):
    """
    회고 목록 조회

    쿼리스트링: 
      :q: 검색
      :roles: 스택 필터링 ("BACKEND", "PM" 식의 복수 선택 가능, none은 개인 회고 조회)
      :bookmarked: 북마크 필터링
      :sort: 정렬 키워드 (new, old, title)
    """
    qs = (
        Retrospective.objects
        .filter(user = request.user)  # 해당 유저의 회고만
        .select_related("project")    # 
        .order_by("-created_at")      # 시간 최신순
    )

    # 검색(제목/본문/프로젝트명)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | 
            Q(content_md__icontains=q) | 
            Q(project__title__icontains=q)
        )
    
    # 스택 필터
    role = (request.GET.get("roles") or "").strip()

    if role == "none":
        qs = qs.filter(project__isnull=True)

    elif role in ("PM", "FRONTEND", "BACKEND"):
        role_project_ids = (
            TeamMember.objects
            .filter(user=request.user, role__code=role)
            .values_list("team__project_id", flat=True)
            .distinct()
        )
        # ✅ 매칭 프로젝트가 없으면 결과 0개가 맞음
        qs = qs.filter(project_id__in=role_project_ids)

    # 북마크 필터
    bookmarked = request.GET.get("bookmarked")
    if bookmarked in ("1", "true", "True"):
        qs = qs.filter(bookmarked=True)

    # 정렬
    sort = request.GET.get("sort", "new")
    if sort == "old":
        qs = qs.order_by("created_at")
    elif sort == "title":
        qs = qs.order_by("title")
    else:
        qs = qs.order_by("-created_at")
    
    my_project_ids = (
        TeamMember.objects
        .filter(user=request.user)
        .values_list("team__project_id", flat=True)
        .distinct()
    )

    my_projects = (
        Project.objects
        .filter(Q(id__in=my_project_ids) | Q(owner=request.user))
        .order_by("title")
    )

    context = {
        "notes" : qs,
        "my_projects": my_projects, # 내 프로젝트 조회 -> 필터에 보여주기
        "role": role,
        "q" : q,
        "bookmarked": bookmarked,
        "sort": sort,
    }
    return render(request, "reflections/note_list.html", context)


@login_required
def note_create(request):
    """
    회고 작성
    
    쿼리스트링:
      :tpl: 선택할 질문 템플릿 (현재는 default 하나만)
      
    """
    tpl_key = request.GET.get("tpl") or "compact"
    guide = load_guide(tpl_key)

    # ✅ draft_key 발급/유지
    if "retro_draft_key" not in request.session:
        request.session["retro_draft_key"] = str(uuid.uuid4())
    draft_key = request.session["retro_draft_key"]
    
    my_projects, my_role_map = _get_my_projects_and_roles(request.user)

    if request.method == "POST":
        title = (request.POST.get("title") or "빈 제목").strip()
        project_id_raw = (request.POST.get("project_id") or "").strip()
        role_code = (request.POST.get("role") or "").strip()

        if not title:
            context = {"guide": guide, "tpl": tpl_key, "error": "제목은 필수입니다."}
            return render(request, "reflections/note_create.html", context)
        
        project = None
        if project_id_raw:
            project = get_object_or_404(Project, id=project_id_raw)

            # 보안/권한: 내 프로젝트가 아니면 막기
            if project not in my_projects:
                messages.error(request, "내 프로젝트만 선택할 수 있습니다.")
                return redirect("reflections:note_create")

            # role 자동 채움 정책: role이 비어있으면 프로젝트 기준 role_map에서 채움
            if not role_code:
                role_code = my_role_map.get(project.id) or ""

        answers = dict() # qid: "답변 내용" 형식
        for q in guide["questions"]:
            qid = q["id"]
            answers[qid] = (request.POST.get(f"a__{qid}") or "빈 답변 내용").strip()
        
        content_md = build_markdown(guide, answers)

        note = Retrospective.objects.create(
            user= request.user,
            project=project,
            template_key=tpl_key,
            title=title,
            answers_json=answers,
            content_md = content_md,
        )

        # ✅ draft로 업로드된 이미지들을 note에 연결
        RetrospectiveAsset.objects.filter(
            user=request.user,
            draft_key=draft_key,
            retrospective__isnull=True,
        ).update(retrospective=note, draft_key=None)

        # ✅ draft_key 정리
        request.session.pop("retro_draft_key", None)

        return redirect("reflections:note_list")
    context = {
        "guide": guide,
        "tpl": tpl_key,
        "answers": {},
        "draft_key": draft_key,
        "my_projects": my_projects,
        "my_role_map": my_role_map,  
        "note": None
    }
    return render(request, "reflections/note_create.html", context)


@login_required
def note_detail(request, note_id):
    """회고 상세"""
    # TODO: 회고 상세 로직 구현
    note = get_object_or_404(Retrospective, id=note_id, user=request.user)
    context = {
        "note": note,
        "guide": load_guide(note.template_key),
        "answers": note.answers_json or {},
    }
    return render(request, "reflections/note_detail.html", context)


@login_required
def note_update(request, note_id):
    """회고 수정 - note_create와 동일하게 guide 기반으로 렌더/저장"""
    note = get_object_or_404(Retrospective, id=note_id, user=request.user)

    tpl = note.template_key or "compact"
    guide = load_guide(tpl)

    # 기존 답변(answers_json)로 textarea 기본값 채우기
    existing_answers = note.answers_json or {}

    my_projects, my_role_map = _get_my_projects_and_roles(request.user)

    if request.method == "POST":
        title = (request.POST.get("title") or "빈 제목").strip()
        project_id_raw = (request.POST.get("project_id") or "").strip()
        role_code = (request.POST.get("role") or "").strip()
        
        if not title:
            context = {
                "note": note,
                "guide": guide,
                "tpl": tpl,
                "answers": existing_answers,
                "error": "제목은 필수입니다.",
            }
            return render(request, "reflections/note_update.html", context)
        
        project = None
        if project_id_raw:
            project = get_object_or_404(Project, id=project_id_raw)
            if project not in my_projects:
                messages.error(request, "내 프로젝트만 선택할 수 있습니다.")
                return redirect("reflections:note_update", note_id=note.id)

            # role 비어있으면 자동, 있으면 사용자가 고른 값 존중
            if not role_code:
                role_code = my_role_map.get(project.id) or ""

        answers = {}
        for q in guide["questions"]:
            qid = q["id"]
            answers[qid] = (request.POST.get(f"a__{qid}") or "").strip()

        content_md = build_markdown(guide, answers)

        note.title = title
        note.project = project
        note.answers_json = answers
        note.content_md = content_md
        note.save(update_fields=["title", "answers_json", "content_md", "updated_at"])

        return redirect("reflections:note_detail", note_id=note.id)

    context = {
        "note": note,
        "guide": guide,
        "tpl": tpl,
        "answers": existing_answers,
        "my_projects": my_projects or {},
        "my_role_map": my_role_map or [],
    }
    return render(request, "reflections/note_update.html", context)



@login_required
def note_delete(request, note_id):
    """회고 삭제"""
    # TODO: 회고 삭제 로직 구현
    note = get_object_or_404(Retrospective, id=note_id, user=request.user)
    if request.method == "POST":
        note.delete()
        messages.success(request, "회고가 삭제되었습니다.")
        return redirect("reflections:note_list")
    return redirect("reflections:note_detail", note_id=note_id)


@extend_schema_view(
    list=extend_schema(
        summary="회고 목록 조회",
        tags=["Retrospectives"],
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                description="검색 (title/content_md/project.name 부분일치)",
            ),
            OpenApiParameter(
                name="roles",
                type=OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                description='스택 필터(복수 가능). 예: roles=BACKEND&roles=PM 또는 roles=none(개인회고)',
                many=True,
            ),
            OpenApiParameter(
                name="bookmarked",
                type=OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                description='북마크 필터. true/1/True면 bookmarked=True',
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                description="정렬 (new, old, title). 기본 new",
            ),
        ],
    ),
    retrieve=extend_schema(summary="회고 상세 조회", tags=["Retrospectives"]),
    create=extend_schema(summary="회고 생성", tags=["Retrospectives"]),
    update=extend_schema(summary="회고 전체 수정", tags=["Retrospectives"]),
    partial_update=extend_schema(summary="회고 부분 수정", tags=["Retrospectives"]),
    destroy=extend_schema(summary="회고 삭제", tags=["Retrospectives"]),
)
class RetrospectiveViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RetrospectiveReadSerializer
        return RetrospectiveWriteSerializer

    def get_queryset(self):
        u = self.request.user
        if not u.is_authenticated:
            return Retrospective.objects.none()

        # base qs
        qs = (
            Retrospective.objects
            .filter(user=u)                 # 해당 유저의 회고만
            .select_related("project", "user")
            .order_by("-created_at")        # 기본 최신순
        )

        # 검색(제목/본문/프로젝트명)
        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(content_md__icontains=q) |
                Q(project__title__icontains=q)
            )

        # 스택 필터(roles=BACKEND&roles=PM&roles=none ...)
        role_codes = self.request.query_params.getlist("roles")
        if role_codes:
            get_personal_retro = "none" in role_codes

            # 원본 로직 그대로: TeamMember에서 role__code로 필터, project_id 목록 추출
            role_project_ids = (
                TeamMember.objects
                .filter(user=u, role__code__in=role_codes)
                .values_list("team__project_id", flat=True)
                .distinct()
            )

            if get_personal_retro and role_project_ids:
                qs = qs.filter(Q(project__isnull=True) | Q(project_id__in=role_project_ids))
            elif get_personal_retro:
                qs = qs.filter(project__isnull=True)
            elif role_project_ids:
                qs = qs.filter(project_id__in=role_project_ids)
            else:
                # roles는 있는데 매칭되는 project가 하나도 없고 none도 없으면 결과 없음
                qs = qs.none()

        # 북마크 필터
        bookmarked = self.request.query_params.get("bookmarked")
        if bookmarked in ("1", "true", "True"):
            qs = qs.filter(bookmarked=True)

        # 정렬
        sort = self.request.query_params.get("sort", "new")
        if sort == "old":
            qs = qs.order_by("created_at")
        elif sort == "title":
            qs = qs.order_by("title")
        else:
            qs = qs.order_by("-created_at")

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated()
        obj = super().get_object()
        if obj.user_id != self.request.user.id:
            raise PermissionDenied("본인 회고만 접근 가능합니다.")
        return obj

    def create(self, request, *args, **kwargs):
        # 생성 후 ReadSerializer로 응답(원하면 제거 가능)
        write = RetrospectiveWriteSerializer(data=request.data, context=self.get_serializer_context())
        write.is_valid(raise_exception=True)
        obj = write.save(user=request.user)
        read = RetrospectiveReadSerializer(obj, context=self.get_serializer_context())
        return Response(read.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="회고 이미지 업로드",
        tags=["Retrospectives"],
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "format": "binary"},
                    "alt_text": {"type": "string"},
                },
                "required": ["image"],
            }
        },
        responses={201: RetrospectiveAssetUploadSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="assets",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_asset(self, request, pk=None):
        retro = self.get_object()  # 여기서 본인 회고 체크됨

        f = request.FILES.get("image")
        if not f:
            return Response({"detail": "image 파일이 필요합니다."}, status=400)

        # 간단한 이미지 타입 체크(추가 안전장치)
        ct = (getattr(f, "content_type", "") or "").lower()
        if ct and not ct.startswith("image/"):
            return Response({"detail": "이미지 파일만 업로드 가능합니다."}, status=400)

        alt_text = (request.data.get("alt_text") or "").strip()

        asset = RetrospectiveAsset.objects.create(
            retrospective=retro,
            user=request.user,
            image=f,
            alt_text=alt_text,
        )

        data = RetrospectiveAssetUploadSerializer(asset, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    @extend_schema(        
        summary="회고 이미지 삭제",
        tags=["Retrospectives"]
    )
    @action(
        detail=True, 
        methods=["delete"], 
        url_path=r"assets/(?P<asset_id>\d+)"
    )
    def delete_asset(self, request, pk=None, asset_id=None):
        retro = self.get_object()  # 본인 회고인지 포함해서 체크된다고 가정

        asset = RetrospectiveAsset.objects.filter(
            id=asset_id,
            retrospective=retro,
            user=request.user,
        ).first()
        if not asset:
            return Response({"detail": "asset not found"}, status=404)

        asset.delete()  # ✅ 여기서 DB 삭제 + (아래 시그널/오버라이드 있으면 파일도 삭제)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(        
        summary="회고 이미지 임시 업로드",
        tags=["Retrospectives"]
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="assets/temp",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_temp_asset(self, request):
        draft_key = request.data.get("draft_key")
        if not draft_key:
            return Response({"detail": "draft_key 필요"}, status=400)

        try:
            draft_uuid = uuid.UUID(str(draft_key))
        except ValueError:
            return Response({"detail": "draft_key 형식 오류"}, status=400)

        f = request.FILES.get("image")
        if not f:
            return Response({"detail": "image 파일 필요"}, status=400)

        ct = (getattr(f, "content_type", "") or "").lower()
        if ct and not ct.startswith("image/"):
            return Response({"detail": "이미지 파일만 업로드 가능합니다."}, status=400)

        alt_text = (request.data.get("alt_text") or "").strip()

        asset = RetrospectiveAsset.objects.create(
            user=request.user,
            draft_key=draft_uuid,
            retrospective=None,
            image=f,
            alt_text=alt_text,
        )

        url = asset.image.url
        md = f"![{alt_text or 'image'}]({url})"
        return Response({"id": asset.id, "url": url, "md": md}, status=status.HTTP_201_CREATED)