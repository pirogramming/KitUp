from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import Role, UserRoleLevel

User = get_user_model()

class LevelFlowTests(TestCase):
    def setUp(self):
        self.password = "testpass1234"
        self.user = User.objects.create_user(username="testuser", password=self.password)

        # ✅ 온보딩/프로필 완료 가드가 있으면 이게 필요
        self.user.nickname = "tester"
        self.user.save(update_fields=["nickname"])

        ok = self.client.login(username="testuser", password=self.password)
        self.assertTrue(ok)

        self.backend = Role.objects.create(code="BACKEND", name="백엔드")
        Role.objects.create(code="FRONTEND", name="프론트엔드")
        Role.objects.create(code="PM", name="PM(기획)")

    def test_get_level_test_ok(self):
        url = reverse("accounts:level_test") + "?role=BACKEND"
        res = self.client.get(url)
        # 디버깅 필요하면 아래 1줄 잠깐 켜봐
        # print(res.status_code, res.headers.get("Location"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context.get("role_code"), "BACKEND")

    def test_submit_creates_user_role_level(self):
        url = reverse("accounts:level_submit")

        # ✅ view는 role로 받는다
        res = self.client.post(url, data={"role": "BACKEND", "level": "3"})
        self.assertEqual(res.status_code, 302)

        obj = UserRoleLevel.objects.get(user=self.user, role=self.backend)
        self.assertEqual(obj.level, 3)

    def test_result_shows_level(self):
        UserRoleLevel.objects.create(
            user=self.user,
            role=self.backend,
            level=2,
            last_diagnosed_at=timezone.now(),
        )

        url = reverse("accounts:test_result") + "?role=BACKEND"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context.get("level"), 2)
