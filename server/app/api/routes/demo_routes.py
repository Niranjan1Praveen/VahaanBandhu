"""Frozen demo routes — one real TomTom corridor per role.

The demo must show genuine road geometry every time: offline, on a rate-limited
key, or long after the key expires. Fetching live at page load makes the demo
hostage to a third party, and the straight-line fallback makes the product look
like it cannot route at all.

So the geometry here was fetched **once** from the live TomTom Routing API and
committed (`tools/freeze_demo_routes.py`). It is measured geometry, not
synthesised, and the response labels it `frozen_snapshot` so the UI can say what
it is rather than implying a live call.

The live endpoint (`POST /routes/live`) is unchanged and still used for real
requests. This is additive.
"""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from server.app.core.security import Identity, get_identity
from server.app.schemas.common import UserRole

router = APIRouter()
log = logging.getLogger(__name__)

FIXTURE = Path(__file__).resolve().parents[4] / "Data" / "demo" / "demo_routes.json"


@functools.lru_cache(maxsize=1)
def _fixture() -> dict | None:
    """Load and cache the frozen routes. None when the fixture is absent."""
    try:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("demo route fixture unavailable at %s: %s", FIXTURE, e)
        return None


@router.get("/demo")
async def demo_route(
    role: UserRole | None = None,
    identity: Identity = Depends(get_identity),
) -> dict:
    """The frozen demo corridor for a role.

    Defaults to the caller's own role, so the demo dashboards need not know
    which corridor belongs to them.
    """
    data = _fixture()
    if data is None:
        raise HTTPException(
            status_code=503,
            detail=("Demo routes are not available. Regenerate them with "
                    "tools/freeze_demo_routes.py."))

    wanted = (role or identity.role or UserRole.FARMER).value
    entry = data["roles"].get(wanted)
    if entry is None:
        raise HTTPException(status_code=404,
                            detail=f"No frozen demo route for role {wanted}.")

    # Flatten into the same shape the map already consumes, so the frontend
    # needs no second rendering path.
    return {
        "role": wanted,
        "title_hi": entry["title_hi"],
        "markers": [
            {"lat": m["lat"], "lon": m["lon"], "kind": m["kind"], "label": m["label"]}
            for m in entry["markers"]
        ],
        "legs": [
            {
                "kind": l["kind"], "label": l["label"],
                "distance_km": l["distance_km"],
                "travel_time_min": l["travel_time_min"],
                "traffic_delay_min": l["traffic_delay_min"],
                "polyline": l["polyline"],
                "n_geometry_points": l["n_geometry_points"],
                "traffic_sections": l.get("traffic_sections", []),
                "provider": l["provider"],
            }
            for l in entry["legs"]
        ],
        "total_distance_km": entry["total_distance_km"],
        "total_time_min": entry["total_time_min"],
        "total_traffic_delay_min": round(
            sum(l["traffic_delay_min"] for l in entry["legs"]), 1),
        "total_geometry_points": entry["total_geometry_points"],
        # Honest provenance: real TomTom geometry, but a snapshot, not a live call.
        "provider": "tomtom",
        "mode": "frozen_snapshot",
        "generated_at": data["generated_at"],
        "warnings": [],
    }
