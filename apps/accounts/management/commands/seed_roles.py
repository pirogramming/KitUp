from django.core.management.base import BaseCommand
from apps.accounts.models import Role


class Command(BaseCommand):
    help = "Role 시드 데이터 생성 (PM, FRONTEND, BACKEND)"

    def handle(self, *args, **options):
        roles = [
            {"code": "PM", "name": "PM(기획)"},
            {"code": "FRONTEND", "name": "프론트엔드"},
            {"code": "BACKEND", "name": "백엔드"},
        ]

        created_count = 0
        for role_data in roles:
            role, created = Role.objects.get_or_create(
                code=role_data["code"],
                defaults={"name": role_data["name"]},
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Role '{role.code}' 생성됨")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  - Role '{role.code}' 이미 존재함")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n총 {created_count}개의 Role이 생성되었습니다.")
        )
