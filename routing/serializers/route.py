from rest_framework import serializers

from routing.models import Node, RouteQuery


class ShortestRouteRequestSerializer(serializers.Serializer):
    source = serializers.CharField()
    destination = serializers.CharField()

    def _validate_node_exists(self, name):
        if not Node.objects.filter(name=name).exists():
            raise serializers.ValidationError(f"Node '{name}' does not exist.")
        return name

    def validate_source(self, value):
        return self._validate_node_exists(value)

    def validate_destination(self, value):
        return self._validate_node_exists(value)

    def validate(self, attrs):
        if attrs["source"] == attrs["destination"]:
            raise serializers.ValidationError(
                "Source and destination must be different nodes."
            )
        return attrs


class RouteQuerySerializer(serializers.ModelSerializer):
    total_latency = serializers.DecimalField(
        max_digits=12, decimal_places=3, coerce_to_string=False
    )

    class Meta:
        model = RouteQuery
        fields = [
            "id", "source", "destination",
            "total_latency", "path", "created_at",
        ]
        read_only_fields = fields