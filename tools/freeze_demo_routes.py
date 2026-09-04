"""Freeze one real TomTom route per role for the demo.

Why freeze at all. The demo must show *real road geometry* every time it is
opened — on a laptop with no network, on a rate-limited key, or a year from now.
Fetching live at page load makes the demo hostage to a third party, and falling
back to a straight line makes the product look like it cannot route.

So: fetch the real carriageway geometry **once**, from the live TomTom API, and
commit it. The fixture is genuine measured geometry, not synthesised, and it is
labelled as a frozen snapshot rather than passed off as live.

One canonical corridor per role:

  farmer  village -> Sonipat mandi          (a real ~18 km haul, not 800 m)
  trucker Rohtak depot -> farm -> mandi, then the return leg through a dealer
  dealer  mandi/supplier -> shop

    python tools/freeze_demo_routes.py            # fetch and write the fixture
    python tools/freeze_demo_routes.py --verify   # check the committed fixture
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "Data" / "demo" / "demo_routes.json"

# Named points on the Rohtak <-> Sonipat corridor.
P = {
    "depot":  {"lat": 28.8955, "lon": 76.6066, "kind": "depot",  "label": "रोहतक डिपो"},
    "village": {"lat": 28.8752, "lon": 76.8410, "kind": "farm",  "label": "रामपुर कलां (खेत)"},
    "farm":   {"lat": 28.9420, "lon": 76.9310, "kind": "farm",   "label": "खेत"},
    "mandi":  {"lat": 28.9931, "lon": 77.0151, "kind": "mandi",  "label": "सोनीपत मंडी"},
    "dealer": {"lat": 28.9600, "lon": 76.8500, "kind": "dealer", "label": "सीमेंट डीलर"},
}

DEMOS = {
    "FARMER": {
        "title_hi": "किसान — खेत से मंडी",
        "markers": ["village", "mandi"],
        # A real haul. The old farm->mandi pair were 800 m apart, which renders
        # as a dot and made the farmer map look broken.
        "legs": [("village", "mandi", "outbound", "खेत → मंडी")],
    },
    "TRUCKER": {
        "title_hi": "ट्रक चालक — पूरा चक्र",
        "markers": ["depot", "farm", "mandi", "dealer"],
        "legs": [
            ("depot", "farm", "outbound", "डिपो → खेत"),
            ("farm", "mandi", "outbound", "खेत → मंडी"),
            ("mandi", "dealer", "return", "मंडी → डीलर"),
            ("dealer", "depot", "return", "डीलर → डिपो"),
        ],
    },
    "INPUT_DEALER": {
        "title_hi": "इनपुट डीलर — आने वाला सामान",
        "markers": ["mandi", "dealer"],
        "legs": [("mandi", "dealer", "outbound", "आपूर्ति → दुकान")],
    },
}


def fetch() -> dict:
    from routing.models import LatLon
    from routing.providers.tomtom import TomTomRoutingProvider

    provider = TomTomRoutingProvider(timeout=30.0)
    if not provider.available:
        raise SystemExit("No usable TomTom key; refusing to write a fixture of "
                         "straight lines. Set TOMTOM_API_KEYS and retry.")

    out = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "tomtom",
        "note": ("Real road geometry fetched once from the TomTom Routing API "
                 "and frozen so the demo is deterministic and works offline. "
                 "This is measured geometry, not synthesised. It is a snapshot: "
                 "distances and the carriageway are stable, but the traffic "
                 "delay recorded here is from the fetch time and the live "
                 "overlay is fetched separately."),
        "points": P,
        "roles": {},
    }

    for role, spec in DEMOS.items():
        legs_out = []
        for a, b, kind, label in spec["legs"]:
            pa, pb = P[a], P[b]
            print(f"  {role:12s} {label} ...", end=" ", flush=True)
            routes = provider.get_alternative_routes(
                LatLon(pa["lat"], pa["lon"]), LatLon(pb["lat"], pb["lon"]),
                max_alternatives=0, travel_mode="truck",
            )
            if not routes or len(routes[0].geometry) < 3:
                raise SystemExit(
                    f"TomTom returned no usable geometry for {role} {label}. "
                    "Not writing a fixture with a straight-line placeholder.")
            r = routes[0]
            legs_out.append({
                "from": a, "to": b, "kind": kind, "label": label,
                "distance_km": round(r.distance_km, 2),
                "travel_time_min": round(r.travel_time_min, 1),
                "traffic_delay_min": round(r.traffic_delay_min, 1),
                "estimated_fuel_cost_inr": round(r.estimated_fuel_cost_inr, 2),
                "toll_inr": round(r.toll_cost_inr, 2),
                "polyline": [[round(lat, 6), round(lon, 6)] for lat, lon in r.geometry],
                "n_geometry_points": len(r.geometry),
                "traffic_sections": r.traffic_sections,
                "provider": "tomtom",
            })
            print(f"{r.distance_km:.1f} km, {len(r.geometry)} pts, "
                  f"{len(r.traffic_sections)} traffic sections")

        out["roles"][role] = {
            "title_hi": spec["title_hi"],
            "markers": [P[m] | {"key": m} for m in spec["markers"]],
            "legs": legs_out,
            "total_distance_km": round(sum(l["distance_km"] for l in legs_out), 2),
            "total_time_min": round(sum(l["travel_time_min"] for l in legs_out), 1),
            "total_geometry_points": sum(l["n_geometry_points"] for l in legs_out),
        }
    return out


def verify() -> int:
    if not FIXTURE.exists():
        print(f"MISSING: {FIXTURE}")
        return 1
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    print(f"generated_at: {d['generated_at']}  source: {d['source']}")
    ok = True
    for role, r in d["roles"].items():
        pts = r["total_geometry_points"]
        # A frozen route with two points per leg would be a straight line, which
        # is exactly what this fixture exists to avoid.
        straight = [l["label"] for l in r["legs"] if l["n_geometry_points"] < 3]
        status = "OK" if not straight else f"STRAIGHT-LINE LEGS: {straight}"
        ok = ok and not straight
        print(f"  {role:12s} {len(r['legs'])} legs  {r['total_distance_km']:6.1f} km  "
              f"{pts:5d} pts  markers={len(r['markers'])}  {status}")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        raise SystemExit(verify())

    print("Fetching real TomTom geometry for the demo corridors ...")
    data = fetch()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(data, indent=1), encoding="utf-8")
    size_kb = FIXTURE.stat().st_size / 1024
    print(f"\nwrote {FIXTURE} ({size_kb:.0f} KB)")
    verify()


if __name__ == "__main__":
    main()
