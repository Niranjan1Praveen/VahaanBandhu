"""Pandera schemas for the canonical master and synthetic tables.

Schema validation is the cheapest place to catch a generator regression. The
checks that matter most here are the ones encoding project rules rather than
mere types:

* a synthetic row may never carry a non-zero real-world confidence score
* a coordinate must fall inside the coarse project region
* a resolved quantity must be positive; an unresolved one must be null, never 0
* a directed edge may not be a self-loop
"""

from __future__ import annotations

import pandera as pa
from pandera import Check, Column, DataFrameSchema

from vb.config import COARSE_BBOX
from vb.enums import (
    ConversionConfidence, FuelType, GeocodePrecision, InputLanguage, InputMode,
    LocationType, MarketYardType, RequesterType, ShopCategory, Unit,
    VehicleAccess, VehicleClass,
)

_lat = Check.in_range(COARSE_BBOX["lat_min"], COARSE_BBOX["lat_max"])
_lon = Check.in_range(COARSE_BBOX["lon_min"], COARSE_BBOX["lon_max"])


def _id(prefix: str) -> Check:
    return Check.str_matches(rf"^{prefix}_[0-9A-F]+$")


LOCATIONS_SCHEMA = DataFrameSchema(
    {
        "location_id": Column(str, [_id("LOC")], unique=True, nullable=False),
        "location_type": Column(str, Check.isin(LocationType.values())),
        "name_en": Column(str, nullable=False),
        "name_hi": Column(str, nullable=True),
        "state_code": Column(str, Check.isin(["DL", "HR", "PB", "UP"])),
        "district": Column(str, nullable=False),
        "latitude": Column(float, [_lat], nullable=False),
        "longitude": Column(float, [_lon], nullable=False),
        "geocode_precision": Column(str, Check.isin(GeocodePrecision.values())),
        "source_id": Column(str, nullable=False),
        "is_synthetic": Column(bool, nullable=False),
        "confidence_score": Column(float, Check.in_range(0.0, 1.0), nullable=False),
        "in_ncr": Column(bool, nullable=False),
        "dataset_version": Column(str, nullable=False),
    },
    checks=[
        # A synthetic entity has no real-world confidence to report. Allowing a
        # non-zero score here is how a fabricated point starts looking verified.
        Check(
            lambda df: ~(df["is_synthetic"] & (df["confidence_score"] > 0)),
            name="synthetic_rows_have_zero_confidence",
            error="synthetic location carries a non-zero confidence score",
        ),
        Check(
            lambda df: ~(df["is_synthetic"] & df["verified_at"].notna()),
            name="synthetic_rows_are_never_verified",
            error="synthetic location carries a verified_at timestamp",
        ),
    ],
    strict=False,
    coerce=True,
)

MANDIS_SCHEMA = DataFrameSchema(
    {
        "mandi_id": Column(str, [_id("MND")], unique=True),
        "location_id": Column(str, [_id("LOC")]),
        "apmc_name": Column(str, nullable=False),
        "market_yard_type": Column(str, Check.isin(MarketYardType.values())),
        "enam_enabled": Column(bool),
        "avg_queue_min": Column(int, Check.in_range(1, 300)),
        "coordinate_verified": Column(bool),
        "is_synthetic": Column(bool),
    },
    checks=[
        # Mandi coordinates in the routing research are town-level approximations. If this
        # ever flips to True, DATA_SOURCES.md must say where they came from.
        Check(
            lambda df: ~df["coordinate_verified"].any(),
            name="no_unsourced_verified_coordinate_claim",
            error="a mandi claims coordinate_verified without a cited source",
        ),
    ],
    strict=False, coerce=True,
)

SHOPS_SCHEMA = DataFrameSchema(
    {
        "shop_id": Column(str, [_id("SHP")], unique=True),
        "location_id": Column(str, [_id("LOC")]),
        "shop_category": Column(str, Check.isin(ShopCategory.values())),
        "capacity_tonnes": Column(float, Check.gt(0)),
        "daily_demand_kg": Column(float, Check.ge(0)),
        "loading_service_min": Column(int, Check.in_range(1, 240)),
        "vehicle_access": Column(str, Check.isin(VehicleAccess.values())),
        "road_access_quality": Column(float, Check.in_range(0.0, 1.0)),
        "is_synthetic": Column(bool, Check.eq(True)),
        "generation_method": Column(str, nullable=False),
    },
    strict=False, coerce=True,
)

FARMER_NODES_SCHEMA = DataFrameSchema(
    {
        "farmer_node_id": Column(str, [_id("FRM")], unique=True),
        "village_location_id": Column(str, [_id("LOC")]),
        "latitude": Column(float, [_lat]),
        "longitude": Column(float, [_lon]),
        "farm_size_ha": Column(float, Check.in_range(0.1, 100.0)),
        "primary_crop_id": Column(str, [_id("CRP")]),
        "is_synthetic": Column(bool, Check.eq(True)),
    },
    strict=False, coerce=True,
)

TRUCKS_SCHEMA = DataFrameSchema(
    {
        "truck_id": Column(str, [_id("TRK")], unique=True),
        "home_location_id": Column(str, [_id("LOC")]),
        "vehicle_class": Column(str, Check.isin(VehicleClass.values())),
        "capacity_kg": Column(float, Check.in_range(300, 40000)),
        "fuel_type": Column(str, Check.isin(FuelType.values())),
        "avg_kmpl": Column(float, Check.in_range(1.5, 20.0)),
        "max_route_km": Column(float, Check.in_range(30, 1500)),
        "is_synthetic": Column(bool, Check.eq(True)),
    },
    checks=[
        # A heavy rigid truck returning 14 km/l is a generator bug, not a
        # remarkable vehicle.
        Check(
            lambda df: ~((df["capacity_kg"] > 12000) & (df["avg_kmpl"] > 7.0)),
            name="heavy_trucks_have_plausible_economy",
            error="a heavy truck reports light-vehicle fuel economy",
        ),
        Check(
            lambda df: ~((df["fuel_type"] == "ev") & (df["capacity_kg"] > 5000)),
            name="no_heavy_evs",
            error="an EV is configured with heavy-truck capacity",
        ),
    ],
    strict=False, coerce=True,
)

REQUESTS_SCHEMA = DataFrameSchema(
    {
        "request_id": Column(str, [_id("REQ")], unique=True),
        "requester_type": Column(str, Check.isin(RequesterType.values())),
        "quantity_value": Column(float, nullable=True),
        "quantity_unit": Column(str, Check.isin(Unit.values())),
        "quantity_kg": Column(float, Check.gt(0), nullable=True),
        "conversion_confidence": Column(str, Check.isin(ConversionConfidence.values())),
        "input_language": Column(str, Check.isin(InputLanguage.values())),
        "input_mode": Column(str, Check.isin(InputMode.values())),
        "parsed_crop_conf": Column(float, Check.in_range(0.0, 1.0)),
        "parsed_mandi_conf": Column(float, Check.in_range(0.0, 1.0)),
        "parsed_quantity_conf": Column(float, Check.in_range(0.0, 1.0)),
        "split": Column(str, Check.isin(["train", "validation", "test"])),
    },
    checks=[
        # The central quantity rule: unresolved means null, never a fabricated
        # kilogram figure, and never a silent zero.
        Check(
            lambda df: ~(
                (df["conversion_confidence"] == ConversionConfidence.UNRESOLVED.value)
                & df["quantity_kg"].notna()
            ),
            name="unresolved_conversions_have_null_kg",
            error="an unresolved quantity was given a kilogram value anyway",
        ),
        Check(
            lambda df: ~(
                (df["conversion_confidence"] != ConversionConfidence.UNRESOLVED.value)
                & df["quantity_kg"].isna()
            ),
            name="resolved_conversions_have_kg",
            error="a conversion marked resolved has no kilogram value",
        ),
        Check(
            lambda df: (df["feasibility_label"] != "feasible") | (df["quantity_kg"] > 0),
            name="feasible_requests_have_positive_quantity",
            error="a request marked feasible has a non-positive quantity",
        ),
    ],
    strict=False, coerce=True,
)

ROUTE_EDGES_SCHEMA = DataFrameSchema(
    {
        "edge_id": Column(str, [_id("EDG")]),
        "origin_location_id": Column(str, [_id("LOC")]),
        "destination_location_id": Column(str, [_id("LOC")]),
        "distance_km": Column(float, Check.gt(0)),
        "haversine_km": Column(float, Check.ge(0)),
        "freeflow_time_min": Column(float, Check.gt(0)),
        "traffic_time_min": Column(float, Check.gt(0)),
        "toll_cost_inr": Column(float, Check.ge(0)),
        "fuel_cost_inr": Column(float, Check.gt(0)),
        "surface_risk_score": Column(float, Check.in_range(0.0, 2.0)),
        "scenario_id": Column(str, nullable=False),
    },
    checks=[
        Check(
            lambda df: df["origin_location_id"] != df["destination_location_id"],
            name="no_self_loops",
            error="an edge connects a location to itself",
        ),
        # Road distance is bounded below by the great-circle distance. A
        # violation means the detour model or a routing response is corrupt.
        Check(
            lambda df: df["distance_km"] >= df["haversine_km"] * 0.98,
            name="road_distance_at_least_geodesic",
            error="road distance is shorter than the straight-line distance",
        ),
    ],
    strict=False, coerce=True,
)

INSTANCES_SCHEMA = DataFrameSchema(
    {
        "instance_id": Column(str, [_id("INS")], unique=True),
        "instance_hash": Column(str, nullable=False),
        "problem_type": Column(str, Check.isin(
            ["TSP", "CVRP", "VRPTW", "PDP", "CIRCULAR_VRP"])),
        "depot_location_id": Column(str, [_id("LOC")]),
        "n_customers": Column(int, Check.ge(2)),
        "n_vehicles": Column(int, Check.ge(1)),
        "capacity_constraint": Column(float, Check.gt(0)),
        "cost_snapshot_id": Column(str, [_id("CST")]),
        "quantum_ready": Column(bool),
        "split": Column(str, Check.isin(["train", "validation", "test"])),
    },
    checks=[
        # The quantum track's whole premise is small encodable problems. If a
        # 40-node instance is flagged quantum_ready, the QUBO builder will
        # silently produce something no backend can run.
        Check(
            lambda df: ~(df["quantum_ready"] & (df["n_customers"] > 7)),
            name="quantum_ready_instances_are_small",
            error="an instance is flagged quantum_ready but is too large to encode",
        ),
    ],
    strict=False, coerce=True,
)

SCHEMAS = {
    "locations_master": LOCATIONS_SCHEMA,
    "mandis": MANDIS_SCHEMA,
    "shops": SHOPS_SCHEMA,
    "farmer_nodes": FARMER_NODES_SCHEMA,
    "trucks": TRUCKS_SCHEMA,
    "transport_requests": REQUESTS_SCHEMA,
    "route_edges": ROUTE_EDGES_SCHEMA,
    "route_instances": INSTANCES_SCHEMA,
}


def validate(name: str, df, *, lazy: bool = True):
    """Validate one table. Raises pandera.errors.SchemaErrors on failure."""
    return SCHEMAS[name].validate(df, lazy=lazy)
