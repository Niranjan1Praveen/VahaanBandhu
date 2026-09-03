"""Location, mandi and crop reference data. Public read-only lookups."""

from __future__ import annotations

from fastapi import APIRouter, Query

from server.app.db.mongodb import CROPS, mongo
from server.app.repositories.transport_repo import location_repo

router = APIRouter()


@router.get("/locations/search")
async def search_locations(
    q: str = Query(default="", description="Name prefix, Hindi or English"),
    location_type: str | None = Query(default=None),
    limit: int = Query(default=15, le=50),
) -> dict:
    results = await location_repo.search(q, location_type, limit)
    return {"query": q, "count": len(results), "results": results}


@router.get("/locations/near")
async def locations_near(
    latitude: float, longitude: float,
    max_km: float = Query(default=50, le=300),
    location_type: str | None = Query(default=None),
    limit: int = Query(default=10, le=50),
) -> dict:
    results = await location_repo.near(latitude, longitude, max_km,
                                       location_type, limit)
    return {"count": len(results), "results": results}


@router.get("/mandis")
async def list_mandis(
    district: str | None = Query(default=None),
    limit: int = Query(default=100, le=300),
) -> dict:
    results = await location_repo.list_mandis(district, limit)
    return {"count": len(results), "results": results}


@router.get("/crops")
async def list_crops() -> dict:
    """Crop ontology with Hindi names, for the farmer request form."""
    try:
        cur = mongo.collection(CROPS).find({}, {"_id": 0}).limit(100)
        results = await cur.to_list(length=100)
    except Exception:
        results = []
    return {"count": len(results), "results": results}
