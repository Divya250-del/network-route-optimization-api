from django.urls import path
from rest_framework.routers import SimpleRouter

from routing.views import (
    EdgeViewSet,
    NodeViewSet,
    RouteHistoryView,
    ShortestRouteView,
)

router = SimpleRouter(trailing_slash=False)
router.register("nodes", NodeViewSet, basename="node")
router.register("edges", EdgeViewSet, basename="edge")

urlpatterns = [
    path("routes/shortest", ShortestRouteView.as_view()),
    path("routes/history", RouteHistoryView.as_view()),
    *router.urls,
]