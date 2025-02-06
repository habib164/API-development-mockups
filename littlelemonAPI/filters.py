import django_filters
from .models import MenuItem

class MenuItemFilter(django_filters.FilterSet):
    class Meta:
        model = MenuItem
        fields = {
            'price': ['lte'],
            'category__title': ['exact'],
            'title': ['icontains'],
    }
