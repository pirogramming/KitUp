"""
팀 매칭 실행 management command
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from apps.projects.models import Season
from apps.projects.services import TeamMatchingService


class Command(BaseCommand):
    help = '팀 매칭 알고리즘 실행'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--season-id',
            type=int,
            required=True,
            help='Season ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 저장하지 않고 결과만 미리 확인',
        )
    
    def handle(self, *args, **options):
        season_id = options['season_id']
        
        # Season 존재 확인
        try:
            season = Season.objects.get(id=season_id)
        except Season.DoesNotExist:
            raise CommandError(f'Season ID {season_id}를 찾을 수 없습니다.')
        
        self.stdout.write(f'📌 시즌: {season.name}')
        self.stdout.write(f'📌 상태: {season.status}')
        
        # 매칭 시간 확인
        if not season.is_matching_period():
            raise CommandError('현재 팀매칭 기간이 아닙니다.')
        
        if options['dry_run']:
            self.stdout.write('⚠️  Dry-run 모드: 결과만 미리 확인합니다.')
        
        try:
            result = TeamMatchingService.run_matching(season_id)
            
            self.stdout.write(self.style.SUCCESS('✅ 팀 매칭 완료!'))
            self.stdout.write(f'  - 생성된 팀: {result["teams_created"]}개')
            self.stdout.write(f'  - 매칭된 사용자: {result["total_users_matched"]}명')
            self.stdout.write(f'    • PM: {result["pm_matched"]}명')
            self.stdout.write(f'    • FE: {result["fe_matched"]}명')
            self.stdout.write(f'    • BE: {result["be_matched"]}명')
            
            if result['total_unmatched'] > 0:
                self.stdout.write(self.style.WARNING(f'⚠️  매칭 안 된 사용자: {result["total_unmatched"]}명'))
                self.stdout.write(f'    • PM: {result["unmatched"]["pm"]}명')
                self.stdout.write(f'    • FE: {result["unmatched"]["fe"]}명')
                self.stdout.write(f'    • BE: {result["unmatched"]["be"]}명')
            
        except ValidationError as e:
            raise CommandError(f'❌ 매칭 실패: {e.message}')
        except Exception as e:
            raise CommandError(f'❌ 예상치 못한 오류: {str(e)}')
