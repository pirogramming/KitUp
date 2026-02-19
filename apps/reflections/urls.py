from django.urls import path
from . import views

app_name = "reflections"

urlpatterns = [
    # 회고 목록
    path("", views.note_list, name="note_list"),  # note_list.html
    
    # 회고 작성
    path("create/", views.note_create, name="note_create"),  # note_create.html
    
    # 회고 상세
    path("<int:note_id>/", views.note_detail, name="note_detail"),  # note_detail.html
    
    # 회고 수정
    path("<int:note_id>/edit/", views.note_update, name="note_update"),  # note_update.html
    
    # 회고 삭제
    path("<int:note_id>/delete/", views.note_delete, name="note_delete"),
]
