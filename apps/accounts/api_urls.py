from django.urls import path
from . import views

urlpatterns = [
    path("check-username/", views.check_username, name="check_username"),
    path("check-email/", views.check_email, name="check_email"),
    path("check-nickname/", views.check_nickname, name="check_nickname"),
    path("level-test/submit/", views.level_submit, name="level_submit"),
    path("report/create", views.create_report, name="create_report"),
]
