# apps/reflections/management/commands/cleanup_temp_assets.py
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from apps.reflections.models import RetrospectiveAsset


class Command(BaseCommand):
    help = "Delete temporary retrospective assets (retrospective is NULL) older than TTL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="TTL in hours (default: 24). Assets older than this will be deleted.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be deleted without actually deleting.",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        dry_run = options["dry_run"]

        cutoff = timezone.now() - timedelta(hours=hours)

        qs = RetrospectiveAsset.objects.filter(
            retrospective__isnull=True,
            created_at__lt=cutoff,
        )

        count = qs.count()

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] would delete {count} temp assets (hours={hours})"))
            return

        # ✅ delete()는 post_delete 시그널이 있으면 파일도 삭제됩니다.
        deleted = qs.delete()
        # deleted는 (총 삭제 수, {모델: 수}) 형태
        self.stdout.write(self.style.SUCCESS(f"deleted {count} temp assets (hours={hours})"))
