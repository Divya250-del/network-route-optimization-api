import django_filters as filters

from routing.models import RouteQuery


class RouteQueryFilter(filters.FilterSet):
    source = filters.CharFilter(field_name="source", lookup_expr="exact")
    destination = filters.CharFilter(field_name="destination", lookup_expr="exact")
    date_from = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = RouteQuery
        fields = ["source", "destination", "date_from", "date_to"]