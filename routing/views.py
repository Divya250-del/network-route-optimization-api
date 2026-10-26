from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from routing.filters import RouteQueryFilter
from routing.models import Edge, Node, RouteQuery
from routing.serializers import (
    EdgeSerializer,
    NodeSerializer,
    RouteQuerySerializer,
    ShortestRouteRequestSerializer,
)
from routing.services import build_graph, shortest_path

DEFAULT_HISTORY_LIMIT = 100
MAX_HISTORY_LIMIT = 500


class CreateListDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """POST, GET (list) and DELETE only; no retrieve or update (not in the spec)."""

    def perform_create(self, serializer):
        # The DB constraints are the last line of defence against races where
        # two identical requests both pass serializer validation.
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError("This record conflicts with an existing one.")


class NodeViewSet(CreateListDestroyViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer


class EdgeViewSet(CreateListDestroyViewSet):
    queryset = Edge.objects.select_related("source", "destination")
    serializer_class = EdgeSerializer


class ShortestRouteView(APIView):
    def post(self, request):
        serializer = ShortestRouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 400 for bad/unknown nodes

        source = serializer.validated_data["source"]
        destination = serializer.validated_data["destination"]

        result = shortest_path(build_graph(), source, destination)
        if result is None:
            return Response(
                {"error": f"No path exists between {source} and {destination}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        total_latency, path = result
        RouteQuery.objects.create(
            source=source,
            destination=destination,
            total_latency=total_latency,
            path=path,
        )
        return Response({"total_latency": float(total_latency), "path": path})


class RouteHistoryView(generics.ListAPIView):
    queryset = RouteQuery.objects.all()  # Meta.ordering gives newest first
    serializer_class = RouteQuerySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RouteQueryFilter

    def _get_limit(self):
        raw = self.request.query_params.get("limit")
        if raw is None:
            return DEFAULT_HISTORY_LIMIT
        try:
            limit = int(raw)
        except ValueError:
            raise ValidationError({"limit": "Must be an integer."})
        if limit < 1:
            raise ValidationError({"limit": "Must be at least 1."})
        return min(limit, MAX_HISTORY_LIMIT)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset[: self._get_limit()]  # slice last, after all filters