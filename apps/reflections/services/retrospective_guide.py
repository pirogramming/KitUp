import json
from pathlib import Path
from django.apps import apps

APP_PATH = Path(apps.get_app_config("reflections").path) 
GUIDE_DIR = APP_PATH / "guide_templates"
ALLOWED_TPLS = {"default", "compact"}  # 지금은 default만 쓰면 {"default"}로

def load_guide(template_key: str) -> dict:
    """
    ### load_guide : {질문}.json 파일을 읽고 dict 형식으로 리턴
    :param tpl:str : retrospective_{tpl}.json 형식으로 읽을 질문 템플릿 지정
    :return -> dict: .json 파일을 변환한 dict
    """
    if template_key not in ALLOWED_TPLS:
        template_key = "default"
    path = GUIDE_DIR / f"retrospective_{template_key}.json"
    return json.loads(path.read_text(encoding="utf-8"))

def build_markdown(guide: dict, answers: dict, title: str | None = None) -> str:
    lines = []
    title_text = title.strip() if title else guide.get("title", "회고")
    lines.append(f"# 📝 {title_text}")
    lines.append("")

    intro = guide.get("intro") or []
    if intro:
        lines.append("> " + "\n> ".join(intro))
        lines.append("")
        lines.append("---")
        lines.append("")

    questions = sorted(guide.get("questions", []), key=lambda x: x.get("order", 0))
    for q in questions:
        order = q.get("order")
        qtitle = q.get("title", "")
        if order:
            lines.append(f"## {order} {qtitle}")
        else:
            lines.append(f"## {qtitle}")
        lines.append("")
        ans = (answers.get(q.get("id")) or "").strip()
        lines.append(ans if ans else "_(작성 내용 없음)_")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
