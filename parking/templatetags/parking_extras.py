from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter để lookup key trong dictionary"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''