from django import template
from django.utils.safestring import mark_safe

import markdown
import bleach

register = template.Library()

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
    return mark_safe(cleaned)
