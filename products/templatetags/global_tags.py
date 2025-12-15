from django import template
from main.models import Produit, Category
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.simple_tag
def allproducts():
    return 44

@register.simple_tag
def allcategories():
    return Category.objects.all().order_by('code')



@register.simple_tag
def firstctg():
    return Category.objects.order_by('code').first()

@register.filter(name='intspace')
@stringfilter
def intspace(value):
    # Split the value into integer and decimal parts

    if len(value)>1:
        parts = str(value).split('.')
    # Format the integer part with spaces as thousands separators
        integer_part = "{:,}".format(int(parts[0])).replace(',', ' ')

        # If there's a decimal part, join it back
        formatted_number = integer_part + ('.' + parts[1] if len(parts) > 1 else '')
    
        return formatted_number
    else:
        return value