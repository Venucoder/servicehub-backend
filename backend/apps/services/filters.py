import django_filters
from django.db.models import Q
from .models import Service, ServiceCategory


class ServiceFilter(django_filters.FilterSet):
    """
    Filter for services
    """
    category = django_filters.ModelChoiceFilter(
        queryset=ServiceCategory.objects.filter(is_active=True),
        field_name='category'
    )
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact'
    )
    min_price = django_filters.NumberFilter(
        field_name='base_price',
        lookup_expr='gte'
    )
    max_price = django_filters.NumberFilter(
        field_name='base_price',
        lookup_expr='lte'
    )
    min_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte'
    )
    delivery_time = django_filters.NumberFilter(
        field_name='delivery_time',
        lookup_expr='lte'
    )
    provider = django_filters.CharFilter(
        field_name='provider__username',
        lookup_expr='iexact'
    )
    has_packages = django_filters.BooleanFilter(
        method='filter_has_packages'
    )
    featured = django_filters.BooleanFilter(
        method='filter_featured'
    )
    
    class Meta:
        model = Service
        fields = [
            'category', 'category_slug', 'min_price', 'max_price',
            'min_rating', 'delivery_time', 'provider', 'has_packages', 'featured'
        ]
    
    def filter_has_packages(self, queryset, name, value):
        if value:
            return queryset.filter(packages__isnull=False).distinct()
        return queryset.filter(packages__isnull=True)
    
    def filter_featured(self, queryset, name, value):
        if value:
            return queryset.filter(
                rating__gte=4.0,
                orders_count__gte=5
            )
        return queryset