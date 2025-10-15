from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows accessing dictionary value by key in Django templates."""
    # This should be safe even if dictionary is a QuerySet or dict-like object
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None