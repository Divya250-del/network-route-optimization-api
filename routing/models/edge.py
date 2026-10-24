from django.db import models
from django.db.models import F, Q


class Edge(models.Model):
    """Directed edge: source -> destination."""

    source = models.ForeignKey(
        "routing.Node", on_delete=models.CASCADE, related_name="outgoing_edges"
    )
    destination = models.ForeignKey(
        "routing.Node", on_delete=models.CASCADE, related_name="incoming_edges"
    )
    latency = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="unique_edge_source_destination",
            ),
            models.CheckConstraint(
                condition=Q(latency__gt=0), name="edge_latency_positive"
            ),
            models.CheckConstraint(
                condition=~Q(source=F("destination")), name="edge_no_self_loop"
            ),
        ]

    def __str__(self):
        return f"{self.source} -> {self.destination} ({self.latency})"