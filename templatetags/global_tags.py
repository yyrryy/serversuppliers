from django import template
from main.models import Produit, Category
from django.db.models import Count, F



register = template.Library()



@register.simple_tag
def alertscount():
    return Produit.objects.filter(stocktotal__lte=F('minstock')).count()