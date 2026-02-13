from django import template
from django.utils.safestring import mark_safe

import markdown
import bleach
import re

register = template.Library()

def _ensure_class(html: str, tag: str, cls: str) -> str:
    # 1) class가 이미 있는 경우: 기존 class 뒤에 추가(중복 방지)
    def repl_with_class(m):
        before, classes, after = m.group(1), m.group(2), m.group(3)
        class_list = classes.split()
        if cls not in class_list:
            class_list.append(cls)
        return f'<{tag}{before}class="{" ".join(class_list)}"{after}'

    html = re.sub(
        rf"<{tag}([^>]*?)class=\"([^\"]*)\"([^>]*?)>",
        repl_with_class,
        html,
        flags=re.IGNORECASE,
    )

    # 2) class가 없는 경우: 새로 추가
    html = re.sub(
        rf"<{tag}(\s|>)",
        rf'<{tag} class="{cls}"\1',
        html,
        flags=re.IGNORECASE,
    )
    return html

def _add_classes(html: str) -> str:
    # table
    html = _ensure_class(html, "table", "md-table")
    html = _ensure_class(html, "thead", "md-thead")
    html = _ensure_class(html, "tbody", "md-tbody")
    html = _ensure_class(html, "tr", "md-tr")
    html = _ensure_class(html, "th", "md-th")
    html = _ensure_class(html, "td", "md-td")

    # images
    html = _ensure_class(html, "img", "md-img")

    # code blocks
    html = _ensure_class(html, "pre", "md-pre")
    html = _ensure_class(html, "code", "md-code")

    # blockquote / lists
    html = _ensure_class(html, "blockquote", "md-quote")
    html = _ensure_class(html, "ul", "md-ul")
    html = _ensure_class(html, "ol", "md-ol")
    html = _ensure_class(html, "li", "md-li")

    # headings
    html = _ensure_class(html, "h1", "md-h1")
    html = _ensure_class(html, "h2", "md-h2")
    html = _ensure_class(html, "h3", "md-h3")

    # paragraphs
    html = _ensure_class(html, "p", "md-p")

    return html

def _wrap_tables(html: str) -> str:
    # table을 md-table-wrap로 감쌈 (이미 감싸져 있으면 중복 방지 정도는 추가 가능)
    return re.sub(
        r'(<table\b[^>]*>.*?</table>)',
        r'<div class="md-table-wrap">\1</div>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

@register.filter(name="get_item")
def get_item(d, key):
    if not d:
        return ""
    return d.get(key, "")

@register.filter(name="md")
def md(value):
    if not value:
        return ""

    raw_html = markdown.markdown(
        value,
        extensions=[
            "fenced_code",   # ``` 코드블록
            "tables",
            "nl2br",         # 줄바꿈
        ],
    )

    allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
        "p","br","hr",
        "h1","h2","h3","h4","h5","h6",
        "pre","code","blockquote",
        "ul","ol","li",
        "strong","em",
        "a","img",
        # 테이블 관련 태그 허용
        "table","thead","tbody","tr","th","td",
    })
    allowed_attrs = {
        "a": ["href", "title", "rel", "target"],
        "img": ["src", "alt", "title"],
        "*": ["class"],
    }

    cleaned = bleach.clean(
        raw_html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        protocols=["http", "https", "data"],
        strip=True,
    )
    cleaned = bleach.linkify(cleaned)
    cleaned = _add_classes(cleaned)
    cleaned = _wrap_tables(cleaned)
    return mark_safe(cleaned)
