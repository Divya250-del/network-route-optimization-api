from datetime import datetime, timezone
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from routing.models import Edge, Node, RouteQuery


def make_nodes(*names):
    return {name: Node.objects.create(name=name) for name in names}


def make_edge(nodes, source, destination, latency):
    return Edge.objects.create(
        source=nodes[source],
        destination=nodes[destination],
        latency=Decimal(str(latency)),
    )


class NodeApiTests(APITestCase):
    def test_create_node(self):
        res = self.client.post("/nodes", {"name": "ServerA"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.json()["name"], "ServerA")
        self.assertIn("id", res.json())

    def test_duplicate_name_returns_400(self):
        make_nodes("ServerA")
        res = self.client.post("/nodes", {"name": "ServerA"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_name_returns_400(self):
        res = self.client.post("/nodes", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_name_returns_400(self):
        res = self.client.post("/nodes", {"name": "   "}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_nodes(self):
        make_nodes("ServerA", "ServerB")
        res = self.client.get("/nodes")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([n["name"] for n in res.json()], ["ServerA", "ServerB"])

    def test_delete_node_cascades_to_edges(self):
        nodes = make_nodes("ServerA", "ServerB")
        make_edge(nodes, "ServerA", "ServerB", 5)
        res = self.client.delete(f"/nodes/{nodes['ServerA'].id}")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Edge.objects.count(), 0)


class EdgeApiTests(APITestCase):
    def setUp(self):
        self.nodes = make_nodes("ServerA", "ServerB")

    def payload(self, **overrides):
        data = {"source": "ServerA", "destination": "ServerB", "latency": 12.5}
        data.update(overrides)
        return data

    def test_create_edge(self):
        res = self.client.post("/edges", self.payload(), format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        body = res.json()
        self.assertEqual(body["source"], "ServerA")
        self.assertEqual(body["destination"], "ServerB")
        self.assertEqual(body["latency"], 12.5)

    def test_duplicate_edge_returns_400(self):
        make_edge(self.nodes, "ServerA", "ServerB", 5)
        res = self.client.post("/edges", self.payload(), format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reverse_edge_is_not_a_duplicate(self):
        make_edge(self.nodes, "ServerA", "ServerB", 5)
        res = self.client.post(
            "/edges",
            self.payload(source="ServerB", destination="ServerA"),
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_zero_or_negative_latency_returns_400(self):
        for bad in (0, -1, -0.5):
            with self.subTest(latency=bad):
                res = self.client.post(
                    "/edges", self.payload(latency=bad), format="json"
                )
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_fields_return_400(self):
        for field in ("source", "destination", "latency"):
            with self.subTest(missing=field):
                data = self.payload()
                del data[field]
                res = self.client.post("/edges", data, format="json")
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_node_returns_400(self):
        res = self.client.post(
            "/edges", self.payload(destination="Nope"), format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_self_loop_returns_400(self):
        res = self.client.post(
            "/edges", self.payload(destination="ServerA"), format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_and_delete_edge(self):
        edge = make_edge(self.nodes, "ServerA", "ServerB", 5)
        self.assertEqual(len(self.client.get("/edges").json()), 1)
        res = self.client.delete(f"/edges/{edge.id}")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Edge.objects.count(), 0)


class ShortestRouteApiTests(APITestCase):
    URL = "/routes/shortest"

    def setUp(self):
        self.nodes = make_nodes("ServerA", "ServerB", "ServerC", "ServerD")
        make_edge(self.nodes, "ServerA", "ServerB", 12.5)
        make_edge(self.nodes, "ServerB", "ServerD", 10.9)

    def post(self, source, destination):
        return self.client.post(
            self.URL, {"source": source, "destination": destination}, format="json"
        )

    def test_path_exists(self):
        res = self.post("ServerA", "ServerD")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.json(),
            {"total_latency": 23.4, "path": ["ServerA", "ServerB", "ServerD"]},
        )

    def test_picks_lower_latency_route_over_fewer_hops(self):
        make_edge(self.nodes, "ServerA", "ServerD", 100)
        res = self.post("ServerA", "ServerD")
        self.assertEqual(res.json()["path"], ["ServerA", "ServerB", "ServerD"])

    def test_no_path_returns_404_with_exact_body(self):
        res = self.post("ServerA", "ServerC")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            res.json(), {"error": "No path exists between ServerA and ServerC"}
        )

    def test_direction_matters(self):
        res = self.post("ServerD", "ServerA")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_node_returns_400(self):
        self.assertEqual(
            self.post("ServerA", "Nope").status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            self.post("Nope", "ServerA").status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_missing_fields_return_400(self):
        res = self.client.post(self.URL, {"source": "ServerA"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_source_and_destination_returns_400(self):
        self.assertEqual(
            self.post("ServerA", "ServerA").status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_successful_query_is_saved_to_history(self):
        self.post("ServerA", "ServerD")
        self.assertEqual(RouteQuery.objects.count(), 1)
        saved = RouteQuery.objects.get()
        self.assertEqual(saved.path, ["ServerA", "ServerB", "ServerD"])
        self.assertEqual(saved.total_latency, Decimal("23.4"))

    def test_failed_query_is_not_saved(self):
        self.post("ServerA", "ServerC")  # 404
        self.post("ServerA", "Nope")  # 400
        self.assertEqual(RouteQuery.objects.count(), 0)


class RouteHistoryApiTests(APITestCase):
    URL = "/routes/history"

    def make_query(self, source, destination, latency, created_at):
        query = RouteQuery.objects.create(
            source=source,
            destination=destination,
            total_latency=Decimal(str(latency)),
            path=[source, destination],
        )
        # created_at is auto_now_add, so override it after creation
        RouteQuery.objects.filter(pk=query.pk).update(created_at=created_at)
        return query

    def setUp(self):
        utc = timezone.utc
        self.make_query("ServerA", "ServerD", 23.4, datetime(2026, 2, 20, 14, 0, tzinfo=utc))
        self.make_query("ServerB", "ServerC", 10.1, datetime(2026, 2, 20, 15, 0, tzinfo=utc))
        self.make_query("ServerA", "ServerC", 5.0, datetime(2026, 2, 21, 9, 0, tzinfo=utc))

    def test_returns_newest_first(self):
        res = self.client.get(self.URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [r["total_latency"] for r in res.json()], [5.0, 10.1, 23.4]
        )

    def test_response_shape(self):
        record = self.client.get(self.URL).json()[0]
        self.assertEqual(
            set(record),
            {"id", "source", "destination", "total_latency", "path", "created_at"},
        )

    def test_filter_by_source(self):
        res = self.client.get(self.URL, {"source": "ServerA"})
        self.assertEqual(len(res.json()), 2)

    def test_filter_by_source_and_destination(self):
        res = self.client.get(self.URL, {"source": "ServerA", "destination": "ServerC"})
        self.assertEqual(len(res.json()), 1)

    def test_filter_by_date_range(self):
        res = self.client.get(
            self.URL,
            {"date_from": "2026-02-20T14:30:00Z", "date_to": "2026-02-20T23:59:59Z"},
        )
        self.assertEqual([r["source"] for r in res.json()], ["ServerB"])

    def test_limit(self):
        self.assertEqual(len(self.client.get(self.URL, {"limit": 2}).json()), 2)

    def test_limit_applies_after_filters(self):
        res = self.client.get(self.URL, {"source": "ServerA", "limit": 1})
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["destination"], "ServerC")  # newest A-query

    def test_invalid_limit_returns_400(self):
        for bad in ("abc", "0", "-3"):
            with self.subTest(limit=bad):
                res = self.client.get(self.URL, {"limit": bad})
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_returns_400(self):
        res = self.client.get(self.URL, {"date_from": "not-a-date"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)