from django.contrib import admin
from .models import Node, Edge, RouteQuery

admin.site.register(Node)
admin.site.register(Edge)
admin.site.register(RouteQuery)
