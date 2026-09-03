"""Load the canonical CSV datasets into MongoDB for the application layer.

Architecture note, recorded here because it is a deliberate decision:

**The CSVs under `Data/` remain the canonical research source of truth.** MongoDB is a
*serving* layer — it exists so the application can do fast geospatial and key lookups.
It is rebuilt from the CSVs, never edited in place as a primary store. If the two ever
disagree, the CSVs win and Mongo is reloaded.

This keeps the research pipeline reproducible (a dataset version is a set of files with
hashes) while giving the app the query patterns it needs.

    python -m vb.load_mongo --drop

Requires `MONGODB_URI` in the environment.
"""

from __future__ import annotations

import argparse
import logging
import os

import pandas as pd
from dotenv import load_dotenv

from vb import config as C

log = logging.getLogger("vb.mongo")

DB_NAME = "vahaanbandhu"

# table -> (csv path, collection, unique key, GeoJSON source columns or None)
COLLECTIONS = {
    "locations_master": (C.MASTER / "locations_master.csv", "locations", "location_id",
                         ("longitude", "latitude")),
    "mandis": (C.MASTER / "mandis.csv", "mandis", "mandi_id", None),
    "crops": (C.MASTER / "crops.csv", "crops", "crop_id", None),
    "mandi_commodities": (C.MASTER / "mandi_commodities.csv", "mandi_commodities", None, None),
    "scenarios": (C.MASTER / "scenarios.csv", "scenarios", "scenario_id", None),
    "shops": (C.SYNTHETIC / "shops.csv", "shops", "shop_id", None),
    "farmer_nodes": (C.SYNTHETIC / "farmer_nodes.csv", "farmer_nodes", "farmer_node_id",
                     ("longitude", "latitude")),
    "trucks": (C.SYNTHETIC / "trucks.csv", "trucks", "truck_id", None),
    "truck_availability": (C.SYNTHETIC / "truck_availability.csv", "truck_availability",
                           "availability_id", None),
    "transport_requests": (C.SYNTHETIC / "transport_requests.csv", "transport_requests",
                           "request_id", None),
    "route_instances": (C.SYNTHETIC / "route_instances.csv", "route_instances",
                        "instance_id", None),
    "instance_requests": (C.SYNTHETIC / "instance_requests.csv", "instance_requests",
                          None, None),
}

# route_edges is loaded separately: it is by far the largest table and only the
# baseline scenario is needed for live serving.
EDGES_PATH = C.SYNTHETIC / "route_edges.csv"


def _records(df: pd.DataFrame, geo: tuple[str, str] | None) -> list[dict]:
    """Convert rows to Mongo documents, adding a GeoJSON point where applicable."""
    df = df.where(pd.notna(df), None)
    docs = df.to_dict("records")
    if geo:
        lon_col, lat_col = geo
        for d in docs:
            lon, lat = d.get(lon_col), d.get(lat_col)
            if lon is not None and lat is not None:
                # GeoJSON is [longitude, latitude] -- the reverse of how the rest
                # of the codebase writes coordinates. Getting this backwards puts
                # every point in the Indian Ocean.
                d["geo"] = {"type": "Point", "coordinates": [float(lon), float(lat)]}
    return docs


def load(uri: str, *, drop: bool = False, edge_scenario: str = "SCN_BASELINE") -> dict:
    from pymongo import ASCENDING, GEOSPHERE, MongoClient

    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    db = client[DB_NAME]
    counts: dict[str, int] = {}

    for name, (path, coll_name, key, geo) in COLLECTIONS.items():
        if not path.exists():
            log.warning("skipping %s: %s not found", name, path)
            continue
        coll = db[coll_name]
        if drop:
            coll.drop()
        df = pd.read_csv(path, low_memory=False)
        docs = _records(df, geo)
        if docs:
            coll.insert_many(docs, ordered=False)
        if key:
            coll.create_index([(key, ASCENDING)], unique=True, name=f"{key}_unique")
        if geo:
            coll.create_index([("geo", GEOSPHERE)], name="geo_2dsphere")
        counts[coll_name] = len(docs)
        log.info("%-22s %7d docs -> %s", name, len(docs), coll_name)

    # Route edges: baseline scenario only, indexed for adjacency lookups.
    if EDGES_PATH.exists():
        coll = db["route_edges"]
        if drop:
            coll.drop()
        edges = pd.read_csv(EDGES_PATH)
        edges = edges[edges["scenario_id"] == edge_scenario]
        docs = _records(edges, None)
        if docs:
            coll.insert_many(docs, ordered=False)
        coll.create_index([("origin_location_id", ASCENDING),
                           ("destination_location_id", ASCENDING),
                           ("scenario_id", ASCENDING)], name="edge_lookup")
        counts["route_edges"] = len(docs)
        log.info("%-22s %7d docs -> route_edges (%s only)",
                 "route_edges", len(docs), edge_scenario)

    # Useful compound indexes for the three user interfaces.
    db["locations"].create_index([("location_type", ASCENDING), ("district", ASCENDING)],
                                 name="type_district")
    db["transport_requests"].create_index([("requester_type", ASCENDING),
                                           ("feasibility_label", ASCENDING)],
                                          name="requester_feasibility")
    db["trucks"].create_index([("district", ASCENDING), ("capacity_kg", ASCENDING)],
                              name="district_capacity")
    db["shops"].create_index([("shop_category", ASCENDING)], name="category")

    return counts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()
    p = argparse.ArgumentParser(description="Load VahaanBandhu datasets into MongoDB")
    p.add_argument("--drop", action="store_true", help="drop collections before loading")
    p.add_argument("--uri", default=os.environ.get("MONGODB_URI", ""))
    p.add_argument("--edge-scenario", default="SCN_BASELINE")
    a = p.parse_args()

    if not a.uri:
        raise SystemExit(
            "MONGODB_URI is not set. Start the local instance with "
            "`docker compose up -d mongo` and set "
            "MONGODB_URI=mongodb://localhost:27017 in .env"
        )
    counts = load(a.uri, drop=a.drop, edge_scenario=a.edge_scenario)
    print(f"\nloaded {sum(counts.values()):,} documents into `{DB_NAME}`")


if __name__ == "__main__":
    main()
