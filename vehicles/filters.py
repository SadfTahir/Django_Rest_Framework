import django_filters

from .models import Make, Vehicle


class MakeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    founded_after = django_filters.DateFilter(field_name='founded_at', lookup_expr='gte')
    founded_before = django_filters.DateFilter(field_name='founded_at', lookup_expr='lte')

    class Meta:
        model = Make
        fields = ['name', 'founded_after', 'founded_before', 'created_by']


class VehicleFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    model = django_filters.CharFilter(lookup_expr='icontains')
    color = django_filters.CharFilter(lookup_expr='iexact')
    make_name = django_filters.CharFilter(field_name='make__name', lookup_expr='icontains')
    engine_min = django_filters.NumberFilter(field_name='engine', lookup_expr='gte')
    engine_max = django_filters.NumberFilter(field_name='engine', lookup_expr='lte')

    class Meta:
        model = Vehicle
        fields = [
            'make', 'make_name', 'name', 'model', 'color', 'engine', 'engine_min', 'engine_max',
            'created_by',
        ]
