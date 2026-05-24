from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter để lấy item từ dictionary theo key
    Sử dụng: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
