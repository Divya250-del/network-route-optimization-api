# Network Route Optimization API

Django + Django REST Framework API to manage nodes and latency edges, and find the lowest-latency route between two nodes using Dijkstra's algorithm.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Run tests: `python manage.py test`

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/nodes` | Add a node (`{"name": "ServerA"}`) |
| POST | `/edges` | Add an edge (`{"source", "destination", "latency"}`) |
| POST | `/routes/shortest` | Shortest route (`{"source", "destination"}`) |
| GET | `/routes/history` | Query history. Filters: `source`, `destination`, `date_from`, `date_to`, `limit` |
| GET | `/nodes`, `/edges` | List nodes / edges |
| DELETE | `/nodes/{id}`, `/edges/{id}` | Delete a node / edge |

Status codes: `201` created, `200` route found, `404` no path (`{"error": "No path exists between X and Y"}`), `400` validation errors.

## Design decisions

- Edges are **directed**; a duplicate is the same `(source, destination)` pair.
- Latency must be > 0; self-loops and unknown nodes are rejected (400).
- Node names are unique and case-sensitive.
- Only successful route lookups are saved to history (names stored as snapshots).
- History defaults to 100 records, max 500.
- Latency uses `Decimal` to avoid float rounding errors; responses return plain numbers.
- Constraints are enforced in both serializers and the database.
