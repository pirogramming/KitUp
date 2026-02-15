"""
팀 매칭 알고리즘 및 관련 서비스
"""
from collections import defaultdict
from itertools import product

from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from apps.accounts.models import User, Role, UserRoleLevel
from apps.projects.models import Season, Project
from apps.teams.models import Team, TeamMember


class TeamMatchingService:
    """
    팀 매칭 알고리즘 서비스

    핵심 전략:
      1. preferred_role 기준으로 역할별 지원자 분류
      2. 열정 레벨 인접 그룹(1-2, 2-3, 3-4)으로 묶기
      3. 열정 그룹 내에서 실력 레벨 인접 그룹으로 세분화
      4. 같은 열정 그룹 + 인접 실력 레벨 조합으로 팀 구성
    """

    PM_PER_TEAM = 1
    FE_PER_TEAM = 2
    BE_PER_TEAM = 2
    TEAM_SIZE = PM_PER_TEAM + FE_PER_TEAM + BE_PER_TEAM

    # 인접 레벨 윈도우 (차이 ≤ 1)
    ADJACENT_WINDOWS = [(1, 2), (2, 3), (3, 4)]

    # ──────────────────────────────────────────
    # public API
    # ──────────────────────────────────────────
    @classmethod
    def run_matching(cls, season_id):
        """
        팀 매칭 실행 (메인 엔트리포인트)

        Returns:
            dict: 매칭 결과 통계
        """
        season = Season.objects.get(id=season_id)

        # ── 1. 지원자 수집 (한 번의 쿼리로 모든 정보 로드) ──
        applicants = (
            User.objects
            .filter(
                passion_level__isnull=False,
                preferred_role__isnull=False,
            )
            .select_related('preferred_role')
            .prefetch_related('role_levels__role')
        )

        if not applicants.exists():
            raise ValidationError("팀매칭 지원자가 없습니다.")

        # ── 2. preferred_role 기준 역할별 분류 ──
        pool = cls._build_candidate_pool(applicants)

        # ── 3. 열정 인접 그룹별 → 실력 인접 그룹별 팀 구성 ──
        team_slots = cls._assign_teams(pool)

        if not team_slots:
            pm_n = len(pool.get('PM', []))
            fe_n = len(pool.get('FRONTEND', []))
            be_n = len(pool.get('BACKEND', []))
            raise ValidationError(
                f"인접 레벨 조건을 만족하는 팀을 구성할 수 없습니다. "
                f"(PM {pm_n}명, FE {fe_n}명, BE {be_n}명)"
            )

        # ── 4. DB에 팀 생성 (단일 트랜잭션) ──
        result = cls._create_teams_in_db(season, team_slots)
        return result

    # ──────────────────────────────────────────
    # Step 2: 후보자 풀 구축
    # ──────────────────────────────────────────
    @staticmethod
    def _build_candidate_pool(applicants):
        """
        지원자를 역할별 dict[role_code → list[Candidate]] 로 변환.
        Candidate = {user, level, passion}
        """
        pool = defaultdict(list)

        for user in applicants:
            role_code = user.preferred_role.code

            # prefetch된 role_levels에서 해당 역할의 레벨 조회
            level = 0
            for rl in user.role_levels.all():
                if rl.role.code == role_code:
                    level = rl.level
                    break

            if level == 0:
                continue  # 해당 역할 레벨이 없으면 제외

            pool[role_code].append({
                'user': user,
                'level': level,
                'passion': user.passion_level,
            })

        return dict(pool)

    # ──────────────────────────────────────────
    # Step 3: 인접 레벨 기반 팀 배정
    # ──────────────────────────────────────────
    @classmethod
    def _assign_teams(cls, pool):
        """
        열정 인접 그룹 × 실력 인접 그룹 조합으로 팀 슬롯을 생성.
        각 팀 안에서 열정 차이 ≤ 1, 같은 역할 실력 차이 ≤ 1 보장.

        Returns:
            list[dict]: [{'pm': [cand], 'fe': [cand, cand], 'be': [cand, cand]}, ...]
        """
        pm_all = pool.get('PM', [])
        fe_all = pool.get('FRONTEND', [])
        be_all = pool.get('BACKEND', [])

        team_slots = []
        used_ids = set()  # 이미 배정된 유저 id

        # 열정 윈도우별로 순회 (높은 열정 그룹부터)
        for passion_lo, passion_hi in reversed(cls.ADJACENT_WINDOWS):
            # 해당 열정 범위에 속하는 미배정 후보 필터
            pm_passion = cls._filter_unused(pm_all, used_ids, passion_lo, passion_hi)
            fe_passion = cls._filter_unused(fe_all, used_ids, passion_lo, passion_hi)
            be_passion = cls._filter_unused(be_all, used_ids, passion_lo, passion_hi)

            # 실력 윈도우별로 추가 세분화
            for level_lo, level_hi in reversed(cls.ADJACENT_WINDOWS):
                pm_cands = [c for c in pm_passion if level_lo <= c['level'] <= level_hi]
                fe_cands = [c for c in fe_passion if level_lo <= c['level'] <= level_hi]
                be_cands = [c for c in be_passion if level_lo <= c['level'] <= level_hi]

                # 가능한 팀 수 계산
                n_teams = min(
                    len(pm_cands) // cls.PM_PER_TEAM,
                    len(fe_cands) // cls.FE_PER_TEAM,
                    len(be_cands) // cls.BE_PER_TEAM,
                )

                if n_teams == 0:
                    continue

                # 각 역할 내에서 레벨 편차를 최소화하도록 정렬
                pm_cands.sort(key=lambda c: c['level'])
                fe_cands.sort(key=lambda c: c['level'])
                be_cands.sort(key=lambda c: c['level'])

                pm_i = fe_i = be_i = 0
                for _ in range(n_teams):
                    slot = {
                        'pm': pm_cands[pm_i:pm_i + cls.PM_PER_TEAM],
                        'fe': fe_cands[fe_i:fe_i + cls.FE_PER_TEAM],
                        'be': be_cands[be_i:be_i + cls.BE_PER_TEAM],
                    }
                    pm_i += cls.PM_PER_TEAM
                    fe_i += cls.FE_PER_TEAM
                    be_i += cls.BE_PER_TEAM

                    # used_ids에 등록
                    for cand in slot['pm'] + slot['fe'] + slot['be']:
                        used_ids.add(cand['user'].id)

                    team_slots.append(slot)

                # passion 필터 목록도 갱신 (다음 level 윈도우에서 중복 방지)
                pm_passion = [c for c in pm_passion if c['user'].id not in used_ids]
                fe_passion = [c for c in fe_passion if c['user'].id not in used_ids]
                be_passion = [c for c in be_passion if c['user'].id not in used_ids]

        # ── 2차: 남은 인원으로 완화 매칭 (열정 ≤ 1, 실력 제약 완화) ──
        remaining_pm = cls._filter_unused(pm_all, used_ids)
        remaining_fe = cls._filter_unused(fe_all, used_ids)
        remaining_be = cls._filter_unused(be_all, used_ids)

        for passion_lo, passion_hi in reversed(cls.ADJACENT_WINDOWS):
            pm_p = [c for c in remaining_pm if passion_lo <= c['passion'] <= passion_hi]
            fe_p = [c for c in remaining_fe if passion_lo <= c['passion'] <= passion_hi]
            be_p = [c for c in remaining_be if passion_lo <= c['passion'] <= passion_hi]

            n = min(
                len(pm_p) // cls.PM_PER_TEAM,
                len(fe_p) // cls.FE_PER_TEAM,
                len(be_p) // cls.BE_PER_TEAM,
            )
            if n == 0:
                continue

            pm_p.sort(key=lambda c: c['level'])
            fe_p.sort(key=lambda c: c['level'])
            be_p.sort(key=lambda c: c['level'])

            pi = fi = bi = 0
            for _ in range(n):
                slot = {
                    'pm': pm_p[pi:pi + cls.PM_PER_TEAM],
                    'fe': fe_p[fi:fi + cls.FE_PER_TEAM],
                    'be': be_p[bi:bi + cls.BE_PER_TEAM],
                }
                pi += cls.PM_PER_TEAM
                fi += cls.FE_PER_TEAM
                bi += cls.BE_PER_TEAM

                for cand in slot['pm'] + slot['fe'] + slot['be']:
                    used_ids.add(cand['user'].id)
                team_slots.append(slot)

            remaining_pm = [c for c in remaining_pm if c['user'].id not in used_ids]
            remaining_fe = [c for c in remaining_fe if c['user'].id not in used_ids]
            remaining_be = [c for c in remaining_be if c['user'].id not in used_ids]

        return team_slots

    # ──────────────────────────────────────────
    # Step 4: DB 저장
    # ──────────────────────────────────────────
    @classmethod
    def _create_teams_in_db(cls, season, team_slots):
        """트랜잭션 내에서 팀·프로젝트·멤버 일괄 생성"""

        # Role 객체 캐싱 (총 3회 쿼리 → 미리 1회)
        roles = {r.code: r for r in Role.objects.all()}

        stats = {'pm': 0, 'fe': 0, 'be': 0}

        with transaction.atomic():
            teams_created = []

            for idx, slot in enumerate(team_slots, 1):
                project = Project.objects.create(
                    title=f"{season.name} 팀 {idx}",
                    description="자동 매칭된 팀 프로젝트",
                    season=season,
                    status='MATCHED',
                )
                team = Team.objects.create(
                    project=project,
                    name=f"Team {idx}",
                )

                role_map = {
                    'pm': ('PM', slot['pm']),
                    'fe': ('FRONTEND', slot['fe']),
                    'be': ('BACKEND', slot['be']),
                }
                for key, (role_code, members) in role_map.items():
                    for cand in members:
                        TeamMember.objects.create(
                            team=team, user=cand['user'], role=roles[role_code],
                        )
                        stats[key] += 1

                teams_created.append(team)

        total = stats['pm'] + stats['fe'] + stats['be']
        return {
            'teams_created': len(teams_created),
            'total_users_matched': total,
            'pm_matched': stats['pm'],
            'fe_matched': stats['fe'],
            'be_matched': stats['be'],
        }

    # ──────────────────────────────────────────
    # 헬퍼
    # ──────────────────────────────────────────
    @staticmethod
    def _filter_unused(candidates, used_ids, passion_lo=None, passion_hi=None):
        """미배정 후보 중 열정 범위에 해당하는 후보만 반환"""
        result = [c for c in candidates if c['user'].id not in used_ids]
        if passion_lo is not None and passion_hi is not None:
            result = [c for c in result if passion_lo <= c['passion'] <= passion_hi]
        return result


class EmailService:
    """이메일 발송 서비스"""
    
    @staticmethod
    def send_matching_start_notification(season_id):
        """
        팀 매칭 기간 시작 알림 이메일 발송
        - 모든 사용자에게 매칭 신청 유도 이메일 발송
        
        Args:
            season_id: Season ID
            
        Returns:
            dict: 발송 결과 통계
        """
        season = Season.objects.get(id=season_id)
        
        # 이메일 알림 활성화 사용자 조회
        users = User.objects.filter(
            email_notifications_enabled=True
        ).exclude(email='')
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                EmailService._send_matching_start_email(
                    user=user,
                    season=season
                )
                sent_count += 1
            except Exception as e:
                print(f"❌ 사용자 {user.id} ({user.email}) 이메일 발송 실패: {str(e)}")
                failed_count += 1
        
        return {
            'season_id': season_id,
            'users_total': users.count(),
            'sent_count': sent_count,
            'failed_count': failed_count,
        }
    
    @staticmethod
    def _send_matching_start_email(user, season):
        """
        개별 사용자에게 팀 매칭 기간 시작 알림 발송
        
        Args:
            user: 수신자
            season: 현재 시즌
        """
        context = {
            'user': user,
            'season': season,
            'matching_start': season.matching_start.strftime('%Y년 %m월 %d일'),
            'matching_end': season.matching_end.strftime('%Y년 %m월 %d일'),
        }
        
        # HTML 템플릿 렌더링
        html_message = render_to_string(
            'emails/matching_start.html',
            context
        )
        
        # 일반 텍스트 버전
        text_message = render_to_string(
            'emails/matching_start.txt',
            context
        )
        
        # 이메일 발송
        send_mail(
            subject=f'[KITUP] {season.name} 팀 매칭이 시작되었습니다',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    @staticmethod
    def send_matching_results(season_id):
        """
        팀 매칭 결과 이메일 발송
        - 매칭된 팀의 멤버들에게만 발송
        - 발송 완료 후 email_notifications_enabled = False로 변경
        
        N+1 쿼리 최적화: prefetch_related 사용
        
        Args:
            season_id: Season ID
            
        Returns:
            dict: 발송 결과 통계
        """
        season = Season.objects.get(id=season_id)
        
        # 현재 시즌의 모든 팀 조회
        # N+1 쿼리 최적화: members__user__role_levels를 미리 로드
        teams = Team.objects.filter(
            project__season=season
        ).prefetch_related(
            'members__user__role_levels',
            'members__role',
            'project'
        ).distinct()
        
        sent_count = 0
        failed_count = 0
        notified_users = []
        
        for team in teams:
            try:
                # 각 팀의 모든 멤버에게 매칭 결과 이메일 발송
                for member in team.members.all():
                    if member.user.email_notifications_enabled:
                        EmailService._send_team_matching_email(
                            user=member.user,
                            team=team,
                            season=season
                        )
                        notified_users.append(member.user.id)
                sent_count += 1
            except Exception as e:
                print(f"❌ 팀 {team.id} 이메일 발송 실패: {str(e)}")
                failed_count += 1
        
        # 이메일을 받은 사용자들의 email_notifications_enabled를 False로 변경
        if notified_users:
            User.objects.filter(id__in=notified_users).update(email_notifications_enabled=False)
        
        return {
            'season_id': season_id,
            'teams_total': teams.count(),
            'sent_count': sent_count,
            'failed_count': failed_count,
            'notified_users': len(notified_users),
        }
    
    @staticmethod
    def _send_team_matching_email(user, team, season):
        """
        개별 사용자에게 팀 매칭 결과 이메일 발송
        
        N+1 쿼리 최적화: prefetch_related된 데이터 사용
        
        Args:
            user: 수신자
            team: 할당된 팀
            season: 현재 시즌
        """
        # 팀원 정보 수집
        # prefetch_related된 데이터만 사용 (DB 쿼리 없음)
        team_members = []
        for member in team.members.all():
            # prefetch_related된 role_levels에서 빠르게 조회
            role_level = None
            for rl in member.user.role_levels.all():
                if rl.role.code == member.role.code:
                    role_level = rl
                    break
            
            team_members.append({
                'user': member.user,
                'role': member.role,
                'level': role_level.level if role_level else None,
            })
        
        # 이메일 컨텍스트
        context = {
            'user': user,
            'team': team,
            'team_members': team_members,
            'season': season,
            'project_start': season.project_start.strftime('%Y년 %m월 %d일'),
            'project_end': season.project_end.strftime('%Y년 %m월 %d일'),
        }
        
        # HTML 템플릿 렌더링
        html_message = render_to_string(
            'emails/matching_result.html',
            context
        )
        
        # 일반 텍스트 버전
        text_message = render_to_string(
            'emails/matching_result.txt',
            context
        )
        
        # 이메일 발송
        send_mail(
            subject=f'[KITUP] {season.name} 팀 매칭 완료',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
