from rest_framework import serializers

from routing.models import Edge, Node


class EdgeSerializer(serializers.ModelSerializer):
    source = serializers.SlugRelatedField(
        slug_field="name", queryset=Node.objects.all()
    )
    destination = serializers.SlugRelatedField(
        slug_field="name", queryset=Node.objects.all()
    )
    latency = serializers.DecimalField(
        max_digits=10, decimal_places=3, coerce_to_string=False
    )

    class Meta:
        model = Edge
        fields = ["id", "source", "destination", "latency"]
        validators = []  # we do the duplicate check ourselves, with a clearer message

    def validate_latency(self, value):
        if value <= 0:
            raise serializers.ValidationError("Latency must be greater than 0.")
        return value

    def validate(self, attrs):
        source, destination = attrs["source"], attrs["destination"]

        if source == destination:
            raise serializers.ValidationError(
                "Source and destination must be different nodes."
            )

        duplicates = Edge.objects.filter(source=source, destination=destination)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                f"An edge from {source.name} to {destination.name} already exists."
            )
        return attrs