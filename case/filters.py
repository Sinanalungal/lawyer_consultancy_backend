from django_filters import rest_framework as filters
from .models import Case


class CaseFilter(filters.FilterSet):
    case_type = filters.CharFilter(lookup_expr='icontains')
    state = filters.NumberFilter(field_name='state__id')
    status = filters.ChoiceFilter(choices=Case.STATUS_CHOICES)

    class Meta:
        model = Case
        fields = ['case_type', 'state', 'status']
