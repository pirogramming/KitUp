#!/usr/bin/env python
"""
테스트 데이터 생성 스크립트
팀매칭 알고리즘 테스트용 데이터 자동 생성
"""
import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User, Role, UserRoleLevel
from apps.projects.models import Season

def create_test_data():
    print("=" * 50)
    print("🚀 테스트 데이터 생성 시작")
    print("=" * 50)
    
    # 1. Role 확인/생성
    print("\n1️⃣ Role 생성 중...")
    roles = {}
    role_data = [
        ('PM', 'PM(기획)'),
        ('FRONTEND', '프론트엔드'),
        ('BACKEND', '백엔드'),
    ]
    
    for code, name in role_data:
        role, created = Role.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )
        roles[code] = role
        status = "생성" if created else "기존"
        print(f"   ✅ {status}: {name}")
    
    # 2. 시즌 생성
    print("\n2️⃣ 시즌 생성 중...")
    now = timezone.now()
    season, created = Season.objects.get_or_create(
        name='2026년 2월 시즌',
        defaults={
            'status': 'MATCHING',
            'matching_start': now - timedelta(hours=1),
            'matching_end': now + timedelta(days=7),
            'project_start': now + timedelta(days=8),
            'project_end': now + timedelta(days=30),
            'is_active': True
        }
    )
    status = "생성" if created else "기존"
    print(f"   ✅ {status}: {season.name}")
    
    # 3. 테스트 유저 생성 (30명: PM 6, FE 12, BE 12)
    print("\n3️⃣ 테스트 유저 생성 중...")
    test_users = [
        # PM (6명)
        ('testpm1', '기획1', 'testpm1@example.com', 'PM', 1, 1),
        ('testpm2', '기획2', 'testpm2@example.com', 'PM', 2, 2),
        ('testpm3', '기획3', 'testpm3@example.com', 'PM', 2, 4),
        ('testpm4', '기획4', 'testpm4@example.com', 'PM', 3, 3),
        ('testpm5', '기획5', 'testpm5@example.com', 'PM', 3, 1),
        ('testpm6', '기획6', 'testpm6@example.com', 'PM', 4, 2),
        
        # FE (12명)
        ('testfe1', '프론트1', 'testfe1@example.com', 'FRONTEND', 1, 2),
        ('testfe2', '프론트2', 'testfe2@example.com', 'FRONTEND', 1, 3),
        ('testfe3', '프론트3', 'testfe3@example.com', 'FRONTEND', 1, 4),
        ('testfe4', '프론트4', 'testfe4@example.com', 'FRONTEND', 2, 1),
        ('testfe5', '프론트5', 'testfe5@example.com', 'FRONTEND', 2, 3),
        ('testfe6', '프론트6', 'testfe6@example.com', 'FRONTEND', 2, 4),
        ('testfe7', '프론트7', 'testfe7@example.com', 'FRONTEND', 3, 2),
        ('testfe8', '프론트8', 'testfe8@example.com', 'FRONTEND', 3, 3),
        ('testfe9', '프론트9', 'testfe9@example.com', 'FRONTEND', 3, 1),
        ('testfe10', '프론트10', 'testfe10@example.com', 'FRONTEND', 4, 4),
        ('testfe11', '프론트11', 'testfe11@example.com', 'FRONTEND', 4, 2),
        ('testfe12', '프론트12', 'testfe12@example.com', 'FRONTEND', 4, 1),
        
        # BE (12명)
        ('testbe1', '백엔드1', 'testbe1@example.com', 'BACKEND', 1, 1),
        ('testbe2', '백엔드2', 'testbe2@example.com', 'BACKEND', 1, 3),
        ('testbe3', '백엔드3', 'testbe3@example.com', 'BACKEND', 1, 4),
        ('testbe4', '백엔드4', 'testbe4@example.com', 'BACKEND', 2, 2),
        ('testbe5', '백엔드5', 'testbe5@example.com', 'BACKEND', 2, 1),
        ('testbe6', '백엔드6', 'testbe6@example.com', 'BACKEND', 2, 3),
        ('testbe7', '백엔드7', 'testbe7@example.com', 'BACKEND', 3, 4),
        ('testbe8', '백엔드8', 'testbe8@example.com', 'BACKEND', 3, 1),
        ('testbe9', '백엔드9', 'testbe9@example.com', 'BACKEND', 3, 2),
        ('testbe10', '백엔드10', 'testbe10@example.com', 'BACKEND', 4, 3),
        ('testbe11', '백엔드11', 'testbe11@example.com', 'BACKEND', 4, 4),
        ('testbe12', '백엔드12', 'testbe12@example.com', 'BACKEND', 4, 2),
    ]
    
    for username, nickname, email, role_code, level, passion_level in test_users:
        # 유저 생성
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'nickname': nickname,
                'passion_level': passion_level,
                'is_active': True,
            }
        )
        
        if created:
            user.set_password('test1234')
            user.save()
        else:
            # 기존 유저의 열정 레벨 업데이트
            user.passion_level = passion_level
            user.save()
        
        # UserRoleLevel 설정
        role = roles[role_code]
        level_obj, _ = UserRoleLevel.objects.update_or_create(
            user=user,
            role=role,
            defaults={'level': level}
        )
        
        status = "생성" if created else "기존"
        print(f"   ✅ {status}: {username:10s} ({nickname:6s}) - {role.name:8s} Lv{level} | 열정 {passion_level}⭐")
    
    print("\n" + "=" * 50)
    print("🎉 테스트 데이터 준비 완료!")
    print("=" * 50)
    print(f"\n📊 생성 통계:")
    print(f"   • Role: 3개")
    print(f"   • Season: 1개 (2026년 2월 시즌)")
    print(f"   • Users: {len(test_users)}명")
    print(f"     - PM: 6명")
    print(f"     - FE: 12명")
    print(f"     - BE: 12명")
    print(f"\n💡 로그인 정보:")
    print(f"   • Username: testpm1, testfe1, testbe1 등")
    print(f"   • Password: test1234")
    print(f"\n🎯 다음 단계:")
    print(f"   1. 로그인하여 마이페이지에서 레벨 확인")
    print(f"   2. 관리자 페이지에서 팀매칭 실행")
    print(f"   3. 결과 확인")

if __name__ == '__main__':
    create_test_data()
