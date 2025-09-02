from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()

@register.filter
def get_field_label(form, field_name):
    """
    Get the label for a form field, falling back to the field name if not found.
    """
    field = form.fields.get(field_name)
    if field and hasattr(field, 'label'):
        return field.label
    return field_name.replace('_', ' ').title()
