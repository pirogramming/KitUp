from django import template
import markdown as md

register = template.Library()


@register.filter
def markdown(text):
    """마크다운을 HTML로 변환"""
    if not text:
        return ""
    return md.markdown(text)
