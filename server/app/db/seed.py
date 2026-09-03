"""Load Phase-A artifacts into MongoDB and create development seed data.

**Direction is one-way.** Phase-A CSVs remain the reproducible research source of
truth; MongoDB is a rebuildable serving layer. Nothing here writes back to
`Data/`, and the compose file mounts those directories read-only.

Only a manageable subset is loaded, so local development has realistic content
without importing 376k route edges into the application database.

    python -m server.app.db.seed --reset
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from server.app.db.mongodb import (
    CROPS, DEALER_REQUIREMENTS, LOCATIONS, MANDIS, TRANSPORT_REQUESTS, USERS,
    VEHICLES, ensure_indexes, mongo, to_geojson,
)
from server.app.schemas.common import (
    RequirementStatus, TransportStatus, UserRole,
)

log = logging.getLogger("vb.seed")

# Development users. Clearly prefixed so they can never be mistaken for real
# accounts, and so a cleanup can target them precisely.
DEV_USERS = [
    {"clerk_user_id": "dev_farmer_01", "email": "farmer@dev.local",
     "role": UserRole.FARMER.value,
     "profile": {"display_name": "रमेश कुमार", "phone": "+91-90000-00001",
                 "district": "Sonipat", "village": "रामपुर कलां",
                 "primary_crop": "wheat"}},
    {"clerk_user_id": "dev_trucker_01", "email": "trucker@dev.local",
     "role": UserRole.TRUCKER.value,
     "profile": {"display_name": "सुखबीर सिंह", "phone": "+91-90000-00002",
                 "district": "Rohtak", "vehicle_number": "HR-10-AB-1234",
                 "vehicle_class": "2axle", "capacity_kg": 9000}},
    {"clerk_user_id": "dev_dealer_01", "email": "dealer@dev.local",
     "role": UserRole.INPUT_DEALER.value,
     "profile": {"display_name": "श्री बालाजी ट्रेडर्स", "phone": "+91-90000-00003",
                 "district": "Sonipat", "business_name": "श्री बालाजी बिल्डिंग मटेरियल",
                 "shop_category": "multi"}},
]

MAX_LOCATIONS = 1200


async def load_phase_a(limit_locations: int = MAX_LOCATIONS) -> dict:
    """Load locations, mandis and crops from the Phase-A masters."""
    import pandas as pd

    from vb import config as C

    counts: dict[str, int] = {}

    # --- locations: mandis, depots and a village sample.
    path = C.MASTER / "locations_master.csv"
    if not path.exists():
        log.warning("Phase-A locations not found at %s", path)
        return counts

    df = pd.read_csv(path)
    keep = df[df["location_type"].isin(["mandi", "depot"])]
    villages = df[df["location_type"] == "village"].head(
        max(0, limit_locations - len(keep)))
    shops = df[df["location_type"] == "shop"].head(120)
    subset = pd.concat([keep, villages, shops], ignore_index=True)

    docs = []
    for _, r in subset.iterrows():
        docs.append({
            "location_id": r["location_id"],
            "location_type": r["location_type"],
            "name_en": r.get("name_en"),
            "name_hi": r.get("name_hi") if pd.notna(r.get("name_hi")) else None,
            "state": r.get("state"), "state_code": r.get("state_code"),
            "district": r.get("district"),
            "latitude": float(r["latitude"]), "longitude": float(r["longitude"]),
            # GeoJSON is [longitude, latitude] -- the reverse of the fields above.
            "geo": to_geojson(float(r["latitude"]), float(r["longitude"])),
            "is_synthetic": bool(r.get("is_synthetic", True)),
            "geocode_precision": r.get("geocode_precision"),
            "in_ncr": bool(r.get("in_ncr", False)),
            "source": "phase_a_v0.1",
        })
    if docs:
        await mongo.collection(LOCATIONS).delete_many({"source": "phase_a_v0.1"})
        await mongo.collection(LOCATIONS).insert_many(docs, ordered=False)
    counts["locations"] = len(docs)

    # --- mandis, joined to their location coordinates.
    mpath = C.MASTER / "mandis.csv"
    if mpath.exists():
        mdf = pd.read_csv(mpath)
        loc_by_id = {d["location_id"]: d for d in docs}
        mandi_docs = []
        for _, r in mdf.iterrows():
            loc = loc_by_id.get(r["location_id"])
            if loc is None:
                continue
            mandi_docs.append({
                "mandi_id": r["mandi_id"], "location_id": r["location_id"],
                "apmc_name": r.get("apmc_name"),
                "name_hi": loc.get("name_hi"), "name_en": loc.get("name_en"),
                "district": loc.get("district"), "state_code": loc.get("state_code"),
                "latitude": loc["latitude"], "longitude": loc["longitude"],
                "geo": loc["geo"],
                "market_yard_type": r.get("market_yard_type"),
                "enam_enabled": bool(r.get("enam_enabled", False)),
                # Phase-A honesty flag: real market name, approximate coordinate.
                "coordinate_verified": bool(r.get("coordinate_verified", False)),
                "avg_queue_min": int(r.get("avg_queue_min", 45)),
                "source": "phase_a_v0.1",
            })
        if mandi_docs:
            await mongo.collection(MANDIS).delete_many({"source": "phase_a_v0.1"})
            await mongo.collection(MANDIS).insert_many(mandi_docs, ordered=False)
        counts["mandis"] = len(mandi_docs)

    # --- crops
    cpath = C.MASTER / "crops.csv"
    if cpath.exists():
        cdf = pd.read_csv(cpath)
        crop_docs = [{
            "crop_id": r["crop_id"], "crop_key": r["crop_key"],
            "name_en": r["name_en"], "name_hi": r["name_hi"],
            "default_unit": r["default_unit"],
            "default_bag_weight_kg": (float(r["default_bag_weight_kg"])
                                      if pd.notna(r["default_bag_weight_kg"]) else None),
            "season": r.get("season_kharif_rabi_zaid"),
            "source": "phase_a_v0.1",
        } for _, r in cdf.iterrows()]
        await mongo.collection(CROPS).delete_many({"source": "phase_a_v0.1"})
        await mongo.collection(CROPS).insert_many(crop_docs, ordered=False)
        counts["crops"] = len(crop_docs)

    return counts


async def seed_dev_data() -> dict:
    """Development users and sample workflow content."""
    counts: dict[str, int] = {}
    now = datetime.now(timezone.utc)

    for u in DEV_USERS:
        await mongo.collection(USERS).update_one(
            {"clerk_user_id": u["clerk_user_id"]},
            {"$set": {**u, "is_dev_seed": True, "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True)
    counts["users"] = len(DEV_USERS)

    # A vehicle for the dev trucker.
    await mongo.collection(VEHICLES).update_one(
        {"vehicle_id": "VEH_DEV0000001"},
        {"$set": {
            "vehicle_id": "VEH_DEV0000001",
            "owner_user_id": "dev_trucker_01",
            "vehicle_number": "HR-10-AB-1234", "vehicle_class": "2axle",
            "capacity_kg": 9000.0, "body_type": "open", "fuel_type": "diesel",
            "available": True, "district": "Rohtak",
            # Based near Rohtak, ~40 km from Sonipat mandi, so the return leg is real.
            "latitude": 28.8955, "longitude": 76.6066,
            "geo": to_geojson(28.8955, 76.6066),
            "is_dev_seed": True, "updated_at": now,
        }, "$setOnInsert": {"created_at": now}},
        upsert=True)
    counts["vehicles"] = 1

    # A farmer request already in flight.
    mandi = await mongo.collection(MANDIS).find_one({}, {"_id": 0})
    await mongo.collection(TRANSPORT_REQUESTS).update_one(
        {"request_id": "REQ_DEV000000001"},
        {"$set": {
            "request_id": "REQ_DEV000000001",
            "requester_user_id": "dev_farmer_01",
            "requester_role": UserRole.FARMER.value,
            "crop_key": "wheat", "crop_label": "गेहूँ",
            "mandi_id": (mandi or {}).get("mandi_id"),
            "mandi_label": (mandi or {}).get("name_hi") or (mandi or {}).get("apmc_name"),
            "quantity_value": 20.0, "quantity_unit": "quintal",
            "quantity_kg": 2000.0,
            "conversion_confidence": "exact",
            "conversion_source": "definitional",
            "needs_clarification": False,
            "origin_label": "रामपुर कलां",
            "origin": {"geo": to_geojson(28.99, 77.01),
                       "latitude": 28.99, "longitude": 77.01},
            "status": TransportStatus.REQUESTED.value,
            "status_history": [{"status": TransportStatus.REQUESTED.value, "at": now}],
            "language": "hi", "input_mode": "text",
            "is_dev_seed": True, "updated_at": now,
        }, "$setOnInsert": {"created_at": now}},
        upsert=True)

    # A deliberately UNRESOLVED bori request -- exercises the clarification path
    # that exists so the system never guesses a conversion.
    await mongo.collection(TRANSPORT_REQUESTS).update_one(
        {"request_id": "REQ_DEV000000002"},
        {"$set": {
            "request_id": "REQ_DEV000000002",
            "requester_user_id": "dev_farmer_01",
            "requester_role": UserRole.FARMER.value,
            "crop_key": "sugarcane", "crop_label": "गन्ना",
            "mandi_id": (mandi or {}).get("mandi_id"),
            "mandi_label": (mandi or {}).get("name_hi"),
            "quantity_value": 15.0, "quantity_unit": "bori",
            "quantity_kg": None,
            "conversion_confidence": "unresolved",
            "conversion_source": "no_bag_weight_available",
            "needs_clarification": True,
            "clarification_prompt": ("एक बोरी का वज़न फसल के अनुसार बदलता है। "
                                     "कृपया बताएं कि एक बोरी में कितने किलो हैं?"),
            "origin_label": "रामपुर कलां",
            "status": TransportStatus.DRAFT.value,
            "status_history": [{"status": TransportStatus.DRAFT.value, "at": now}],
            "language": "hi", "input_mode": "text",
            "is_dev_seed": True, "updated_at": now,
        }, "$setOnInsert": {"created_at": now}},
        upsert=True)
    counts["transport_requests"] = 2

    # Dealer requirements placed along a realistic RETURN CORRIDOR.
    #
    # Geometry matters here. The trucker is based near Rohtak (28.90, 76.61) and
    # delivers to Sonipat mandi (28.99, 77.02) -- roughly 40 km apart. Driving
    # home empty therefore costs ~40 km, and a dealer positioned *between* the
    # two converts that empty leg into a paid one.
    #
    # An earlier seed put the depot essentially at the mandi, which made every
    # empty_km_avoided legitimately 0: with no empty return leg there is nothing
    # to avoid. The formula was right; the scenario was degenerate.
    MANDI_LAT, MANDI_LON = 28.9931, 77.0151
    reqs = [
        # On the homeward corridor -- should show a large empty-km saving.
        ("DRQ_DEV000000001", "cement", "सीमेंट", 8000.0, 28.96, 76.85),
        ("DRQ_DEV000000002", "tmt", "स्टील / टीएमटी", 5000.0, 28.93, 76.72),
        # Deliberately in the WRONG direction -- should show little or no saving,
        # so the UI can be seen to distinguish a real opportunity from a detour.
        ("DRQ_DEV000000003", "brick", "ईंट", 12000.0, 29.10, 77.35),
    ]
    for rid, material, label, kg, lat, lon in reqs:
        await mongo.collection(DEALER_REQUIREMENTS).update_one(
            {"requirement_id": rid},
            {"$set": {
                "requirement_id": rid, "dealer_user_id": "dev_dealer_01",
                "business_name": "श्री बालाजी बिल्डिंग मटेरियल",
                "material": material, "material_label": label,
                "quantity_value": kg, "quantity_unit": "kg", "quantity_kg": kg,
                "conversion_confidence": "exact",
                "needs_clarification": False,
                "delivery_label": f"{label} — सोनीपत",
                "delivery_location": {"geo": to_geojson(lat, lon),
                                      "latitude": lat, "longitude": lon},
                "needed_by": (now + timedelta(days=3)).date().isoformat(),
                "status": RequirementStatus.OPEN.value,
                "is_dev_seed": True, "updated_at": now,
            }, "$setOnInsert": {"created_at": now}},
            upsert=True)
    counts["dealer_requirements"] = len(reqs)
    return counts


async def run(reset: bool = False) -> dict:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    await mongo.connect()
    idx = await ensure_indexes()
    log.info("indexes ensured on %d collections", len(idx))

    if reset:
        for coll in (LOCATIONS, MANDIS, CROPS, USERS, VEHICLES,
                     TRANSPORT_REQUESTS, DEALER_REQUIREMENTS):
            await mongo.collection(coll).delete_many({})
        log.info("collections reset")

    counts = await load_phase_a()
    log.info("Phase-A loaded: %s", counts)
    dev = await seed_dev_data()
    log.info("dev seed: %s", dev)
    await mongo.disconnect()
    return {"phase_a": counts, "dev": dev, "indexes": {k: len(v) for k, v in idx.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true",
                    help="drop the application collections before loading")
    a = ap.parse_args()
    out = asyncio.run(run(reset=a.reset))
    print(out)


if __name__ == "__main__":
    main()
