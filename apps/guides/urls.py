from django.urls import path
from . import views

app_name = "guides"

urlpatterns = [
    # 미션/체크리스트 페이지
    path("mission/", views.mission, name="mission"),
]
