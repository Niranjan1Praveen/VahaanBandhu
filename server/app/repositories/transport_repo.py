"""Transport request, dealer requirement, route result and reference repositories.

Route results are **immutable**: a stored optimization is a record of what the
system decided at a point in time, with the model version that decided it. It is
appended, never updated in place.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from server.app.db.mongodb import (
    DEALER_REQUIREMENTS, LOCATIONS, MANDIS, ROUTE_RESULTS, TRANSPORT_REQUESTS,
    VEHICLES, mongo, to_geojson,
)
from server.app.schemas.common import (
    ALLOWED_TRANSITIONS, RequirementStatus, TransportStatus,
)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12].upper()}"


class TransportRequestRepository:
    @property
    def col(self):
        return mongo.collection(TRANSPORT_REQUESTS)

    async def create(self, doc: dict) -> dict:
        doc = dict(doc)
        doc.setdefault("request_id", _new_id("REQ"))
        doc.setdefault("status", TransportStatus.REQUESTED.value)
        doc["created_at"] = datetime.now(timezone.utc)
        doc["updated_at"] = doc["created_at"]
        doc.setdefault("status_history", [
            {"status": doc["status"], "at": doc["created_at"]}])
        await self.col.insert_one(doc)
        return await self.get(doc["request_id"])

    async def get(self, request_id: str) -> dict | None:
        return await self.col.find_one({"request_id": request_id}, {"_id": 0})

    async def list_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        cur = self.col.find({"requester_user_id": user_id}, {"_id": 0}) \
            .sort("created_at", -1).limit(limit)
        return await cur.to_list(length=limit)

    async def list_open(self, limit: int = 50) -> list[dict]:
        """Requests a trucker can pick up."""
        cur = self.col.find(
            {"status": {"$in": [TransportStatus.REQUESTED.value,
                                TransportStatus.MATCHING.value]}},
            {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cur.to_list(length=limit)

    async def transition(self, request_id: str, new_status: TransportStatus,
                         actor_user_id: str | None = None) -> dict:
        """Move to a new status, rejecting illegal transitions server-side."""
        doc = await self.get(request_id)
        if doc is None:
            raise KeyError(f"unknown request {request_id}")
        current = TransportStatus(doc["status"])
        if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
            raise ValueError(
                f"cannot move a request from {current.value} to {new_status.value}")
        now = datetime.now(timezone.utc)
        await self.col.update_one(
            {"request_id": request_id},
            {"$set": {"status": new_status.value, "updated_at": now},
             "$push": {"status_history": {
                 "status": new_status.value, "at": now, "by": actor_user_id}}},
        )
        return await self.get(request_id)

    async def assign_vehicle(self, request_id: str, vehicle_id: str,
                             trucker_user_id: str) -> dict:
        await self.col.update_one(
            {"request_id": request_id},
            {"$set": {"assigned_vehicle_id": vehicle_id,
                      "assigned_trucker_user_id": trucker_user_id,
                      "updated_at": datetime.now(timezone.utc)}},
        )
        return await self.get(request_id)


class DealerRequirementRepository:
    @property
    def col(self):
        return mongo.collection(DEALER_REQUIREMENTS)

    async def create(self, doc: dict) -> dict:
        doc = dict(doc)
        doc.setdefault("requirement_id", _new_id("DRQ"))
        doc.setdefault("status", RequirementStatus.OPEN.value)
        doc["created_at"] = datetime.now(timezone.utc)
        doc["updated_at"] = doc["created_at"]
        await self.col.insert_one(doc)
        return await self.get(doc["requirement_id"])

    async def get(self, requirement_id: str) -> dict | None:
        return await self.col.find_one({"requirement_id": requirement_id}, {"_id": 0})

    async def list_for_dealer(self, dealer_user_id: str, limit: int = 50) -> list[dict]:
        cur = self.col.find({"dealer_user_id": dealer_user_id}, {"_id": 0}) \
            .sort("created_at", -1).limit(limit)
        return await cur.to_list(length=limit)

    async def list_open(self, limit: int = 50) -> list[dict]:
        cur = self.col.find({"status": RequirementStatus.OPEN.value}, {"_id": 0}) \
            .sort("created_at", -1).limit(limit)
        return await cur.to_list(length=limit)

    async def near(self, latitude: float, longitude: float, max_km: float = 60.0,
                   limit: int = 10) -> list[dict]:
        """Open requirements near a point — the return-load candidate query."""
        cur = self.col.find({
            "status": RequirementStatus.OPEN.value,
            "delivery_location.geo": {
                "$near": {
                    "$geometry": to_geojson(latitude, longitude),
                    "$maxDistance": max_km * 1000,
                }},
        }, {"_id": 0}).limit(limit)
        return await cur.to_list(length=limit)

    async def set_status(self, requirement_id: str, status: RequirementStatus) -> dict:
        await self.col.update_one(
            {"requirement_id": requirement_id},
            {"$set": {"status": status.value,
                      "updated_at": datetime.now(timezone.utc)}})
        return await self.get(requirement_id)


class RouteResultRepository:
    """Immutable store of optimization outputs."""

    @property
    def col(self):
        return mongo.collection(ROUTE_RESULTS)

    async def save(self, solution: dict) -> dict:
        doc = dict(solution)
        doc["created_at"] = datetime.now(timezone.utc)
        await self.col.insert_one(doc)
        return await self.get(doc["route_id"])

    async def get(self, route_id: str) -> dict | None:
        return await self.col.find_one({"route_id": route_id}, {"_id": 0})

    async def list_for_request(self, request_id: str) -> list[dict]:
        cur = self.col.find({"request_id": request_id}, {"_id": 0}) \
            .sort("created_at", -1).limit(20)
        return await cur.to_list(length=20)


class VehicleRepository:
    @property
    def col(self):
        return mongo.collection(VEHICLES)

    async def create(self, doc: dict) -> dict:
        doc = dict(doc)
        doc.setdefault("vehicle_id", _new_id("VEH"))
        doc["created_at"] = datetime.now(timezone.utc)
        await self.col.insert_one(doc)
        return await self.get(doc["vehicle_id"])

    async def get(self, vehicle_id: str) -> dict | None:
        return await self.col.find_one({"vehicle_id": vehicle_id}, {"_id": 0})

    async def list_for_owner(self, owner_user_id: str) -> list[dict]:
        cur = self.col.find({"owner_user_id": owner_user_id}, {"_id": 0}).limit(50)
        return await cur.to_list(length=50)

    async def set_availability(self, vehicle_id: str, available: bool,
                               latitude: float | None = None,
                               longitude: float | None = None) -> dict:
        sets: dict = {"available": available,
                      "updated_at": datetime.now(timezone.utc)}
        if latitude is not None and longitude is not None:
            sets["geo"] = to_geojson(latitude, longitude)
            sets["latitude"] = latitude
            sets["longitude"] = longitude
        await self.col.update_one({"vehicle_id": vehicle_id}, {"$set": sets})
        return await self.get(vehicle_id)


class LocationRepository:
    @property
    def col(self):
        return mongo.collection(LOCATIONS)

    @property
    def mandi_col(self):
        return mongo.collection(MANDIS)

    async def search(self, q: str, location_type: str | None = None,
                     limit: int = 15) -> list[dict]:
        query: dict = {}
        if q:
            # Prefix match on either script. A text index exists, but prefix
            # regex gives better autocomplete behaviour for partial words.
            query["$or"] = [
                {"name_en": {"$regex": f"^{q}", "$options": "i"}},
                {"name_hi": {"$regex": f"^{q}"}},
                {"district": {"$regex": f"^{q}", "$options": "i"}},
            ]
        if location_type:
            query["location_type"] = location_type
        cur = self.col.find(query, {"_id": 0}).limit(limit)
        return await cur.to_list(length=limit)

    async def get(self, location_id: str) -> dict | None:
        return await self.col.find_one({"location_id": location_id}, {"_id": 0})

    async def near(self, latitude: float, longitude: float, max_km: float = 50,
                   location_type: str | None = None, limit: int = 10) -> list[dict]:
        query: dict = {"geo": {"$near": {
            "$geometry": to_geojson(latitude, longitude),
            "$maxDistance": max_km * 1000}}}
        if location_type:
            query["location_type"] = location_type
        cur = self.col.find(query, {"_id": 0}).limit(limit)
        return await cur.to_list(length=limit)

    async def list_mandis(self, district: str | None = None,
                          limit: int = 100) -> list[dict]:
        query = {"district": district} if district else {}
        cur = self.mandi_col.find(query, {"_id": 0}).limit(limit)
        return await cur.to_list(length=limit)


transport_repo = TransportRequestRepository()
requirement_repo = DealerRequirementRepository()
route_result_repo = RouteResultRepository()
vehicle_repo = VehicleRepository()
location_repo = LocationRepository()
