"""MongoDB connection, collections and index management.

MongoDB is used intentionally rather than as "Postgres with JSON syntax":

* **Embed** profile data inside the user document -- it is always read with the
  user and never queried independently.
* **Reference** locations, mandis and vehicles -- they are shared across many
  documents and would duplicate badly.
* **GeoJSON + 2dsphere** for anything spatial, so `$near` queries work. Note the
  coordinate order is `[longitude, latitude]`, the reverse of how the rest of
  the codebase writes coordinates; getting it backwards silently places every
  point in the Indian Ocean.
* **TTL** on ephemeral route results so cached optimizations expire rather than
  accumulating.
* **Immutable** route results -- a stored optimization is a historical record and
  is never updated in place, because it is evidence about what the system
  decided at a point in time.
"""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, GEOSPHERE, IndexModel

from server.app.core.config import get_settings

log = logging.getLogger(__name__)

# Collection names, referenced through constants so a typo fails at import.
USERS = "users"
LOCATIONS = "locations"
MANDIS = "mandis"
VEHICLES = "vehicles"
TRANSPORT_REQUESTS = "transport_requests"
DEALER_REQUIREMENTS = "dealer_requirements"
ROUTE_RESULTS = "route_results"
TRUCK_AVAILABILITY = "truck_availability"
CROPS = "crops"

ALL_COLLECTIONS = [
    USERS, LOCATIONS, MANDIS, VEHICLES, TRANSPORT_REQUESTS,
    DEALER_REQUIREMENTS, ROUTE_RESULTS, TRUCK_AVAILABILITY, CROPS,
]


class Mongo:
    """Holds the client. Kept as a module-level singleton via `mongo`."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        s = get_settings()
        self.client = AsyncIOMotorClient(s.mongodb_uri, serverSelectionTimeoutMS=5000)
        await self.client.admin.command("ping")
        self.db = self.client[s.mongodb_db]
        log.info("mongodb connected: db=%s", s.mongodb_db)

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    async def healthy(self) -> bool:
        try:
            if self.client is None:
                return False
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def collection(self, name: str):
        if self.db is None:
            raise RuntimeError("MongoDB is not connected")
        return self.db[name]


mongo = Mongo()


async def ensure_indexes() -> dict[str, list[str]]:
    """Create every index the application relies on. Idempotent."""
    created: dict[str, list[str]] = {}

    plans: dict[str, list[IndexModel]] = {
        USERS: [
            IndexModel([("clerk_user_id", ASCENDING)], unique=True, sparse=True,
                       name="clerk_user_id_unique"),
            IndexModel([("email", ASCENDING)], unique=True, sparse=True,
                       name="email_unique"),
            IndexModel([("role", ASCENDING)], name="role"),
        ],
        LOCATIONS: [
            IndexModel([("location_id", ASCENDING)], unique=True, name="location_id_unique"),
            # 2dsphere powers "mandis near me" and truck matching.
            IndexModel([("geo", GEOSPHERE)], name="geo_2dsphere"),
            IndexModel([("location_type", ASCENDING), ("district", ASCENDING)],
                       name="type_district"),
            IndexModel([("state_code", ASCENDING)], name="state_code"),
            IndexModel([("name_en", "text"), ("name_hi", "text")], name="name_text"),
        ],
        MANDIS: [
            IndexModel([("mandi_id", ASCENDING)], unique=True, name="mandi_id_unique"),
            IndexModel([("geo", GEOSPHERE)], name="geo_2dsphere"),
            IndexModel([("district", ASCENDING)], name="district"),
        ],
        CROPS: [
            IndexModel([("crop_key", ASCENDING)], unique=True, name="crop_key_unique"),
        ],
        VEHICLES: [
            IndexModel([("vehicle_id", ASCENDING)], unique=True, name="vehicle_id_unique"),
            IndexModel([("owner_user_id", ASCENDING)], name="owner"),
            IndexModel([("geo", GEOSPHERE)], name="geo_2dsphere"),
            IndexModel([("district", ASCENDING), ("capacity_kg", ASCENDING)],
                       name="district_capacity"),
        ],
        TRANSPORT_REQUESTS: [
            IndexModel([("request_id", ASCENDING)], unique=True, name="request_id_unique"),
            IndexModel([("requester_user_id", ASCENDING), ("created_at", DESCENDING)],
                       name="requester_recent"),
            IndexModel([("status", ASCENDING)], name="status"),
            IndexModel([("origin.geo", GEOSPHERE)], name="origin_geo"),
        ],
        DEALER_REQUIREMENTS: [
            IndexModel([("requirement_id", ASCENDING)], unique=True,
                       name="requirement_id_unique"),
            IndexModel([("dealer_user_id", ASCENDING), ("created_at", DESCENDING)],
                       name="dealer_recent"),
            IndexModel([("status", ASCENDING)], name="status"),
            IndexModel([("delivery_location.geo", GEOSPHERE)], name="delivery_geo"),
        ],
        ROUTE_RESULTS: [
            IndexModel([("route_id", ASCENDING)], unique=True, name="route_id_unique"),
            IndexModel([("request_id", ASCENDING)], name="request"),
            IndexModel([("created_at", DESCENDING)], name="recent"),
            # Version-aware lookup: never serve a result computed under a
            # different optimization model.
            IndexModel([("vbqer_version", ASCENDING), ("cost_snapshot_id", ASCENDING)],
                       name="version_snapshot"),
        ],
        TRUCK_AVAILABILITY: [
            IndexModel([("vehicle_id", ASCENDING)], name="vehicle"),
            IndexModel([("geo", GEOSPHERE)], name="geo_2dsphere"),
            # Availability is ephemeral; expire it rather than accumulating.
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0,
                       name="ttl_expires_at"),
        ],
    }

    for coll, models in plans.items():
        try:
            names = await mongo.collection(coll).create_indexes(models)
            created[coll] = names
        except Exception as e:
            log.error("index creation failed for %s: %s", coll, e)
            created[coll] = [f"ERROR: {e}"]
    return created


def to_geojson(latitude: float, longitude: float) -> dict:
    """GeoJSON Point. Coordinates are [longitude, latitude] -- in that order."""
    return {"type": "Point", "coordinates": [float(longitude), float(latitude)]}
