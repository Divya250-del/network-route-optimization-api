from django.db import models


class RouteQuery(models.Model):
    """History of shortest-route lookups"""

    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    total_latency = models.DecimalField(max_digits=12, decimal_places=3)
    path = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "destination"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.source} -> {self.destination} ({self.total_latency})"