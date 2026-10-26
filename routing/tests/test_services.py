from decimal import Decimal as D

from django.test import SimpleTestCase

from routing.services import shortest_path


class ShortestPathTests(SimpleTestCase):
    def test_direct_edge(self):
        graph = {"A": [("B", D("12.5"))]}
        self.assertEqual(shortest_path(graph, "A", "B"), (D("12.5"), ["A", "B"]))

    def test_prefers_lower_latency_over_fewer_hops(self):
        graph = {
            "A": [("D", D("100")), ("B", D("1"))],
            "B": [("C", D("1"))],
            "C": [("D", D("1"))],
        }
        total, path = shortest_path(graph, "A", "D")
        self.assertEqual(total, D("3"))
        self.assertEqual(path, ["A", "B", "C", "D"])

    def test_unreachable_returns_none(self):
        graph = {"A": [("B", D("1"))], "C": [("D", D("1"))]}
        self.assertIsNone(shortest_path(graph, "A", "D"))

    def test_edges_are_directed(self):
        graph = {"A": [("B", D("1"))]}
        self.assertIsNone(shortest_path(graph, "B", "A"))

    def test_decimal_arithmetic_is_exact(self):
        graph = {"A": [("B", D("12.5"))], "B": [("D", D("10.9"))]}
        total, path = shortest_path(graph, "A", "D")
        self.assertEqual(total, D("23.4"))
        self.assertEqual(path, ["A", "B", "D"])

    def test_cycle_does_not_loop_forever(self):
        graph = {
            "A": [("B", D("1"))],
            "B": [("A", D("1")), ("C", D("2"))],
        }
        total, path = shortest_path(graph, "A", "C")
        self.assertEqual(total, D("3"))
        self.assertEqual(path, ["A", "B", "C"])