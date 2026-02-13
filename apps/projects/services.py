"""
팀 매칭 알고리즘 및 관련 서비스
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from apps.accounts.models import User, Role, UserRoleLevel
from apps.projects.models import Season, Project
from apps.teams.models import Team, TeamMember


class TeamMatchingService:
    """팀 매칭 알고리즘 서비스"""
    
    TEAM_SIZE = 5
    PM_COUNT_PER_TEAM = 1
    FE_COUNT_PER_TEAM = 2
    BE_COUNT_PER_TEAM = 2
    
    @staticmethod
    def run_matching(season_id):
        """
        팀 매칭 실행
        
        Args:
            season_id: Season ID
            
        Returns:
            dict: 매칭 결과 통계
            
        Raises:
            ValidationError: 지원자 부족 등 조건 미충족
        """
        season = Season.objects.get(id=season_id)
        
        # 1️⃣ passion_level이 설정된 지원자만 필터링
        # N+1 쿼리 최적화: UserRoleLevel을 미리 로드
        applicants = User.objects.filter(
            passion_level__isnull=False
        ).prefetch_related('role_levels')
        
        if not applicants.exists():
            raise ValidationError("팀매칭 지원자가 없습니다.")
        
        # 2️⃣ 역할별로 그룹화
        pm_candidates = TeamMatchingService._get_role_candidates(
            applicants, 'PM'
        )
        fe_candidates = TeamMatchingService._get_role_candidates(
            applicants, 'FRONTEND'
        )
        be_candidates = TeamMatchingService._get_role_candidates(
            applicants, 'BACKEND'
        )
        
        # 3️⃣ 가능한 최대 팀 개수 계산
        # PM 기준, FE 기준, BE 기준 중 최소값
        max_teams_by_pm = len(pm_candidates) // TeamMatchingService.PM_COUNT_PER_TEAM
        max_teams_by_fe = len(fe_candidates) // TeamMatchingService.FE_COUNT_PER_TEAM
        max_teams_by_be = len(be_candidates) // TeamMatchingService.BE_COUNT_PER_TEAM
        
        num_teams = min(max_teams_by_pm, max_teams_by_fe, max_teams_by_be)
        
        if num_teams == 0:
            raise ValidationError(
                f"팀을 만들 수 없습니다. (최소 조건: PM {TeamMatchingService.PM_COUNT_PER_TEAM}명, "
                f"FE {TeamMatchingService.FE_COUNT_PER_TEAM}명, BE {TeamMatchingService.BE_COUNT_PER_TEAM}명) "
                f"현재: PM {len(pm_candidates)}명, FE {len(fe_candidates)}명, BE {len(be_candidates)}명"
            )
        
        # 4️⃣ 더 나은 분배 알고리즘
        # 각 역할별로 열정 그룹을 만들되, 팀별로 라운드로빈 방식 적용
        def distribute_round_robin(candidates, num_teams, role_code):
            """
            각 역할별 지원자를 팀별로 라운드로빈으로 배정
            같은 팀 내에서 여러 직군의 사람이 들어가면서도,
            각 역할의 배정은 균등하게 이루어짐
            N+1 쿼리 최적화: prefetch_related된 role_levels 사용
            """
            # 헬퍼: 캐시된 user.role_levels에서 해당 role의 level을 빠르게 조회
            def get_role_level(user, role_code):
                """이미 prefetch된 role_levels에서 빠르게 조회 (DB 쿼리 없음)"""
                for role_level in user.role_levels.all():
                    if role_level.role.code == role_code:
                        return role_level.level
                return 0
            
            # 열정별로 그룹화한 후 레벨순 정렬
            passion_groups = {}
            for user in candidates:
                passion = user.passion_level or 0
                if passion not in passion_groups:
                    passion_groups[passion] = []
                passion_groups[passion].append(user)
            
            # 각 열정 그룹을 역할별 레벨로 정렬 (높은 순)
            # 이제 DB 쿼리 없이 메모리에서만 정렬함
            for passion in passion_groups:
                passion_groups[passion].sort(
                    key=lambda u: (-get_role_level(u, role_code))
                )
            
            # 열정별로 순회하면서 팀별로 라운드로빈 배정
            result = [[] for _ in range(num_teams)]
            team_member_counts = [0] * num_teams
            
            for passion_level in sorted(passion_groups.keys(), reverse=True):
                users_in_passion = passion_groups[passion_level]
                for idx, user in enumerate(users_in_passion):
                    # 가장 적은 멤버를 가진 팀부터 배정
                    min_team = min(range(num_teams), key=lambda i: team_member_counts[i])
                    result[min_team].append(user)
                    team_member_counts[min_team] += 1
            
            # 결과를 평탄화
            flattened = []
            for team_members in result:
                flattened.extend(team_members)
            return flattened
        
        # 4️⃣ 트랜잭션 내에서 팀 생성 및 멤버 배정
        with transaction.atomic():
            teams_created = []
            
            # 각 역할의 지원자를 라운드-로빈 분배 (열정 + 레벨 + 균형 고려)
            pm_distributed = distribute_round_robin(pm_candidates, num_teams, 'PM')
            fe_distributed = distribute_round_robin(fe_candidates, num_teams, 'FRONTEND')
            be_distributed = distribute_round_robin(be_candidates, num_teams, 'BACKEND')
            
            pm_idx = 0
            fe_idx = 0
            be_idx = 0
            
            for team_num in range(num_teams):
                # 프로젝트 생성
                project = Project.objects.create(
                    title=f"{season.name} 팀 {team_num + 1}",
                    description=f"자동 매칭된 팀 프로젝트",
                    status='MATCHED',
                )
                
                # 팀 생성
                team = Team.objects.create(
                    project=project,
                    name=f"Team {team_num + 1}",
                )
                
                # PM 배정
                for _ in range(TeamMatchingService.PM_COUNT_PER_TEAM):
                    if pm_idx < len(pm_distributed):
                        pm_user = pm_distributed[pm_idx]
                        TeamMember.objects.create(
                            team=team,
                            user=pm_user,
                            role=Role.objects.get(code='PM'),
                        )
                        pm_idx += 1
                
                # FE 배정
                for _ in range(TeamMatchingService.FE_COUNT_PER_TEAM):
                    if fe_idx < len(fe_distributed):
                        fe_user = fe_distributed[fe_idx]
                        TeamMember.objects.create(
                            team=team,
                            user=fe_user,
                            role=Role.objects.get(code='FRONTEND'),
                        )
                        fe_idx += 1
                
                # BE 배정
                for _ in range(TeamMatchingService.BE_COUNT_PER_TEAM):
                    if be_idx < len(be_distributed):
                        be_user = be_distributed[be_idx]
                        TeamMember.objects.create(
                            team=team,
                            user=be_user,
                            role=Role.objects.get(code='BACKEND'),
                        )
                        be_idx += 1
                
                teams_created.append(team)
        
        # 매칭되지 않은 인원 계산
        unmatched = {
            'pm': len(pm_candidates) - pm_idx,
            'fe': len(fe_candidates) - fe_idx,
            'be': len(be_candidates) - be_idx,
        }
        
        return {
            'teams_created': len(teams_created),
            'total_users_matched': (
                pm_idx +
                fe_idx +
                be_idx
            ),
            'pm_matched': pm_idx,
            'fe_matched': fe_idx,
            'be_matched': be_idx,
            'unmatched': unmatched,
            'total_unmatched': sum(unmatched.values()),
        }
    
    @staticmethod
    def _get_role_candidates(applicants, role_code):
        """
        특정 역할의 지원자를 역할 레벨 + 열정 레벨 기반으로 정렬
        
        정렬 기준:
        1. 열정 레벨 내림차순 (높은 열정부터)
        2. 같은 열정이면 역할 레벨 내림차순 (스킬 좋은 사람)
        
        N+1 쿼리 최적화: prefetch_related된 데이터만 사용
        
        Args:
            applicants: User QuerySet (prefetch_related='role_levels' 필수)
            role_code: 'PM' | 'FRONTEND' | 'BACKEND'
            
        Returns:
            list: 정렬된 User 객체 리스트 (열정 우선, 그 다음 역할 레벨)
        """
        candidates = []
        
        for user in applicants:
            # prefetch_related된 role_levels에서 해당 역할 조회 (DB 쿼리 없음)
            role_level = None
            for rl in user.role_levels.all():
                if rl.role.code == role_code:
                    role_level = rl
                    break
            
            if role_level:
                candidates.append({
                    'user': user,
                    'level': role_level.level,
                    'passion': user.passion_level or 0,
                })
        
        # 정렬: 열정 내림차순, 같으면 레벨 내림차순
        candidates.sort(key=lambda x: (-x['passion'], -x['level']))
        
        return [c['user'] for c in candidates]


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
