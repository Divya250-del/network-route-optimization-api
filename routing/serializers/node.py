from rest_framework import serializers

from routing.models import Node


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ["id", "name"]