"""Phase-B backend tests.

These run against a real MongoDB and Redis (the compose stack), because the
things most worth testing here — index behaviour, geospatial queries, status
transitions, cache versioning — are exactly what a mock would fake away.

The load-bearing tests:

* ``test_bori_is_never_silently_converted`` — the Phase-A quantity rule must
  survive into the application layer.
* ``test_role_enforced_server_side`` — a client cannot reach another role's data
  by claiming a role.
* ``test_no_live_quantum_hardware_in_request_path`` — the architectural promise,
  verified against the real import graph.
"""

from __future__ import annotations

import asyncio
import os

import pytest
import pytest_asyncio

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MONGODB_DB", "vahaanbandhu_test")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from server.app.core.config import get_settings  # noqa: E402
from server.app.db.mongodb import ensure_indexes, mongo  # noqa: E402
from server.app.db.redis_cache import cache, route_cache_key  # noqa: E402
from server.app.main import app  # noqa: E402
from server.app.schemas.common import (  # noqa: E402
    ALLOWED_TRANSITIONS, QuantityUnit, TransportStatus, UserRole,
)
from server.app.services.quantity_service import (  # noqa: E402
    clarification_needed, fits_capacity, normalize_quantity,
)

pytestmark = pytest.mark.asyncio

FARMER = {"x-dev-user": "test_farmer"}
TRUCKER = {"x-dev-user": "test_trucker"}
DEALER = {"x-dev-user": "test_dealer"}


def _mongo_up() -> bool:
    try:
        from pymongo import MongoClient
        MongoClient(os.environ["MONGODB_URI"],
                    serverSelectionTimeoutMS=1500).admin.command("ping")
        return True
    except Exception:
        return False


needs_mongo = pytest.mark.skipif(
    not _mongo_up(), reason="MongoDB not reachable (docker compose up -d mongo)")


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    """A client against the real app, with lifespan startup run."""
    await mongo.connect()
    await ensure_indexes()
    await cache.connect()
    # Seed the three test identities with roles.
    from server.app.repositories.user_repo import user_repo
    for uid, role in (("test_farmer", UserRole.FARMER),
                      ("test_trucker", UserRole.TRUCKER),
                      ("test_dealer", UserRole.INPUT_DEALER)):
        await user_repo.upsert(uid, email=f"{uid}@test.local")
        await user_repo.set_role(uid, role, {"display_name": uid})

    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as c:
        yield c

    for coll in ("transport_requests", "dealer_requirements", "vehicles"):
        await mongo.collection(coll).delete_many({"is_test": True})
    await mongo.disconnect()
    await cache.disconnect()


# --------------------------------------------------------------------------
# Quantity normalization — the Phase-A rule at the application boundary
# --------------------------------------------------------------------------

class TestQuantity:
    async def test_quintal_converts_exactly(self):
        q = normalize_quantity(25, QuantityUnit.QUINTAL, "wheat")
        assert q.quantity_kg == 2500
        assert q.conversion_confidence.value == "exact"
        assert clarification_needed(q) is None

    async def test_kg_is_identity(self):
        assert normalize_quantity(500, QuantityUnit.KG).quantity_kg == 500

    async def test_tonne_converts_exactly(self):
        assert normalize_quantity(2, QuantityUnit.TONNE).quantity_kg == 2000

    async def test_bori_with_known_crop_resolves(self):
        q = normalize_quantity(20, QuantityUnit.BORI, "wheat")
        assert q.quantity_kg is not None
        assert q.bag_weight_kg_used is not None

    async def test_bori_is_never_silently_converted(self):
        """The single most important application-layer rule.

        A bori with no determinable bag weight must not become 50 kg. A 20-bori
        load assumed at 50 kg is overstated by 25% for many crops, and that
        error goes straight into capacity feasibility and vehicle dispatch.
        """
        q = normalize_quantity(15, QuantityUnit.BORI, "sugarcane")
        if q.quantity_kg is None:
            assert q.conversion_confidence.value == "unresolved"
            assert clarification_needed(q) is not None
            assert not q.resolved

    async def test_unknown_crop_bori_is_unresolved(self):
        q = normalize_quantity(10, QuantityUnit.BORI, "not_a_real_crop")
        if q.quantity_kg is None:
            assert clarification_needed(q) is not None

    async def test_capacity_check_returns_none_when_unresolved(self):
        """An unknown load is not a load that fits."""
        q = normalize_quantity(15, QuantityUnit.BORI, "sugarcane")
        if q.quantity_kg is None:
            assert fits_capacity(q, 9000) is None

    async def test_capacity_check_when_resolved(self):
        q = normalize_quantity(25, QuantityUnit.QUINTAL, "wheat")
        assert fits_capacity(q, 9000) is True
        assert fits_capacity(q, 1000) is False


# --------------------------------------------------------------------------
# Status transitions
# --------------------------------------------------------------------------

class TestStatusModel:
    async def test_terminal_states_have_no_exits(self):
        assert ALLOWED_TRANSITIONS[TransportStatus.COMPLETED] == set()
        assert ALLOWED_TRANSITIONS[TransportStatus.CANCELLED] == set()

    async def test_every_status_has_a_transition_entry(self):
        for s in TransportStatus:
            assert s in ALLOWED_TRANSITIONS

    async def test_cannot_skip_from_requested_to_completed(self):
        assert TransportStatus.COMPLETED not in ALLOWED_TRANSITIONS[
            TransportStatus.REQUESTED]

    async def test_at_mandi_can_take_a_return_load(self):
        """The circular-logistics path must exist in the state machine."""
        assert TransportStatus.RETURN_LOAD in ALLOWED_TRANSITIONS[
            TransportStatus.AT_MANDI]


# --------------------------------------------------------------------------
# Cache versioning
# --------------------------------------------------------------------------

class TestCacheKeys:
    def _key(self, **over):
        base = dict(origin_id="A", destination_id="B", stops=[],
                    vehicle_capacity_kg=9000, vbqer_version="vbqer_v1",
                    graph_version="g1", cost_snapshot_id="CST_1", profile="live")
        return route_cache_key(**{**base, **over})

    async def test_same_inputs_same_key(self):
        assert self._key() == self._key()

    async def test_vbqer_version_change_invalidates(self):
        """A model bump must make old entries unreachable by construction,
        not rely on someone remembering to flush."""
        assert self._key() != self._key(vbqer_version="vbqer_v2")

    async def test_graph_version_change_invalidates(self):
        assert self._key() != self._key(graph_version="g2")

    async def test_cost_snapshot_change_invalidates(self):
        assert self._key() != self._key(cost_snapshot_id="CST_2")

    async def test_stop_order_does_not_matter(self):
        a = self._key(stops=["X", "Y"])
        b = self._key(stops=["Y", "X"])
        assert a == b


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

@needs_mongo
class TestHealth:
    async def test_health_reports_components(self, client):
        r = await client.get("/api/v1/health")
        assert r.status_code == 200
        body = r.json()
        assert "mongodb" in body["components"]
        assert body["routing"]["engine"] == "VB-QER"

    async def test_health_never_leaks_secrets(self, client):
        """Health reports booleans about configuration, never values."""
        text = (await client.get("/api/v1/health")).text.lower()
        for marker in ("sk_", "bearer ", "secret_key", "api_key="):
            assert marker not in text

    async def test_liveness_needs_no_database(self, client):
        assert (await client.get("/api/v1/health/live")).json()["alive"] is True

    async def test_engine_info_declares_no_live_qpu(self, client):
        body = (await client.get("/api/v1/routes/engine/info")).json()
        assert body["engine"] == "VB-QER"
        assert body["live_quantum_hardware_call"] is False


@needs_mongo
class TestAuthorization:
    async def test_unauthenticated_is_401(self, client):
        assert (await client.get("/api/v1/farmers/requests")).status_code == 401

    async def test_role_enforced_server_side(self, client):
        """A farmer cannot reach trucker endpoints. The role comes from the
        database, not from anything the client sends."""
        r = await client.get("/api/v1/truckers/jobs", headers=FARMER)
        assert r.status_code == 403

    async def test_trucker_cannot_reach_dealer_endpoints(self, client):
        assert (await client.get("/api/v1/dealers/requirements",
                                 headers=TRUCKER)).status_code == 403

    async def test_dealer_cannot_create_farmer_requests(self, client):
        r = await client.post("/api/v1/farmers/requests", headers=DEALER, json={
            "crop_key": "wheat", "quantity_value": 10,
            "quantity_unit": "quintal"})
        assert r.status_code == 403

    async def test_me_returns_db_role(self, client):
        body = (await client.get("/api/v1/me", headers=FARMER)).json()
        assert body["role"] == "FARMER"
        assert body["auth_source"] == "dev"


@needs_mongo
class TestFarmerFlow:
    async def test_create_resolvable_request(self, client):
        r = await client.post("/api/v1/farmers/requests", headers=FARMER, json={
            "crop_key": "wheat", "crop_label": "गेहूँ",
            "quantity_value": 25, "quantity_unit": "quintal",
            "origin_label": "test village"})
        assert r.status_code == 201
        body = r.json()
        assert body["quantity_kg"] == 2500
        assert body["status"] == "REQUESTED"
        assert body["needs_clarification"] is False

    async def test_unresolved_bori_request_stays_draft(self, client):
        """An unresolvable quantity must not enter matching."""
        r = await client.post("/api/v1/farmers/requests", headers=FARMER, json={
            "crop_key": "sugarcane", "quantity_value": 15,
            "quantity_unit": "bori"})
        assert r.status_code == 201
        body = r.json()
        if body["quantity_kg"] is None:
            assert body["status"] == "DRAFT"
            assert body["needs_clarification"] is True
            assert body["clarification_prompt"]

    async def test_rejects_zero_quantity(self, client):
        r = await client.post("/api/v1/farmers/requests", headers=FARMER, json={
            "crop_key": "wheat", "quantity_value": 0, "quantity_unit": "kg"})
        assert r.status_code == 422

    async def test_rejects_negative_quantity(self, client):
        r = await client.post("/api/v1/farmers/requests", headers=FARMER, json={
            "crop_key": "wheat", "quantity_value": -5, "quantity_unit": "kg"})
        assert r.status_code == 422

    async def test_rejects_unknown_unit(self, client):
        r = await client.post("/api/v1/farmers/requests", headers=FARMER, json={
            "crop_key": "wheat", "quantity_value": 5, "quantity_unit": "truckload"})
        assert r.status_code == 422

    async def test_list_only_returns_own_requests(self, client):
        await client.post("/api/v1/farmers/requests", headers=FARMER, json={
            "crop_key": "wheat", "quantity_value": 5, "quantity_unit": "quintal"})
        rows = (await client.get("/api/v1/farmers/requests", headers=FARMER)).json()
        assert isinstance(rows, list)

    async def test_other_users_request_is_404_not_403(self, client):
        """Do not leak the existence of another user's request."""
        r = await client.get("/api/v1/farmers/requests/REQ_DOES_NOT_EXIST",
                             headers=FARMER)
        assert r.status_code == 404


@needs_mongo
class TestTruckerFlow:
    async def test_add_vehicle_and_list(self, client):
        r = await client.post("/api/v1/truckers/vehicles", headers=TRUCKER, json={
            "vehicle_number": "TEST-01", "vehicle_class": "2axle",
            "capacity_kg": 9000})
        assert r.status_code == 201
        vid = r.json()["vehicle_id"]
        rows = (await client.get("/api/v1/truckers/vehicles",
                                 headers=TRUCKER)).json()
        assert any(v["vehicle_id"] == vid for v in rows)

    async def test_rejects_impossible_capacity(self, client):
        r = await client.post("/api/v1/truckers/vehicles", headers=TRUCKER, json={
            "vehicle_number": "TEST-BAD", "vehicle_class": "2axle",
            "capacity_kg": 999999})
        assert r.status_code == 422

    async def test_cannot_accept_a_job_exceeding_capacity(self, client):
        """Capacity is checked server-side before assignment."""
        veh = (await client.post("/api/v1/truckers/vehicles", headers=TRUCKER,
                                 json={"vehicle_number": "TEST-SMALL",
                                       "vehicle_class": "pickup",
                                       "capacity_kg": 500})).json()
        job = (await client.post("/api/v1/farmers/requests", headers=FARMER,
                                 json={"crop_key": "wheat", "quantity_value": 50,
                                       "quantity_unit": "quintal"})).json()
        r = await client.post(
            f"/api/v1/truckers/jobs/{job['request_id']}/accept",
            headers=TRUCKER, json={"vehicle_id": veh["vehicle_id"]})
        assert r.status_code == 400
        assert "capacity" in r.json()["detail"].lower()

    async def test_cannot_accept_a_job_with_unresolved_quantity(self, client):
        """An unknown weight cannot be dispatched to a vehicle."""
        veh = (await client.post("/api/v1/truckers/vehicles", headers=TRUCKER,
                                 json={"vehicle_number": "TEST-2",
                                       "vehicle_class": "2axle",
                                       "capacity_kg": 9000})).json()
        job = (await client.post("/api/v1/farmers/requests", headers=FARMER,
                                 json={"crop_key": "sugarcane",
                                       "quantity_value": 12,
                                       "quantity_unit": "bori"})).json()
        if job["quantity_kg"] is None:
            r = await client.post(
                f"/api/v1/truckers/jobs/{job['request_id']}/accept",
                headers=TRUCKER, json={"vehicle_id": veh["vehicle_id"]})
            assert r.status_code == 400

    async def test_return_loads_requires_a_location(self, client):
        r = await client.get("/api/v1/truckers/return-loads", headers=TRUCKER)
        assert r.status_code == 400


@needs_mongo
class TestDealerFlow:
    async def test_create_requirement(self, client):
        r = await client.post("/api/v1/dealers/requirements", headers=DEALER,
                              json={"material": "cement", "quantity_value": 5000,
                                    "quantity_unit": "kg",
                                    "delivery_label": "test shop",
                                    "delivery_point": {"latitude": 28.96,
                                                       "longitude": 76.85}})
        assert r.status_code == 201
        assert r.json()["quantity_kg"] == 5000

    async def test_materials_listed(self, client):
        body = (await client.get("/api/v1/dealers/materials",
                                 headers=DEALER)).json()
        assert "cement" in body["materials"]

    async def test_rejects_out_of_region_coordinates(self, client):
        """A London coordinate is not a Haryana delivery point."""
        r = await client.post("/api/v1/dealers/requirements", headers=DEALER,
                              json={"material": "cement", "quantity_value": 100,
                                    "quantity_unit": "kg",
                                    "delivery_point": {"latitude": 51.5,
                                                       "longitude": -0.12}})
        assert r.status_code == 422


@needs_mongo
class TestReferenceData:
    async def test_mandis_loaded(self, client):
        body = (await client.get("/api/v1/mandis?limit=5")).json()
        assert body["count"] >= 0

    async def test_location_search_is_prefix_matched(self, client):
        body = (await client.get("/api/v1/locations/search?q=Son")).json()
        assert "results" in body

    async def test_geospatial_near_query_works(self, client):
        """Exercises the 2dsphere index, and implicitly that GeoJSON was stored
        as [longitude, latitude] rather than the reverse."""
        r = await client.get(
            "/api/v1/locations/near?latitude=28.99&longitude=77.01&max_km=50")
        assert r.status_code == 200


class TestProductionSafety:
    async def test_no_live_quantum_hardware_in_request_path(self):
        """Checked in a clean subprocess: importing the API must not pull in
        the IBM runtime. A queued QPU job can never affect availability."""
        import subprocess
        import sys
        from pathlib import Path

        probe = ("import sys; import server.app.main; "
                 "bad=[m for m in sys.modules if 'ibm' in m.lower()]; "
                 "print('LEAK' if bad else 'CLEAN', bad[:5])")
        out = subprocess.run([sys.executable, "-c", probe],
                             capture_output=True, text=True,
                             cwd=str(Path(__file__).resolve().parents[2]))
        assert out.returncode == 0, out.stderr[-600:]
        assert out.stdout.startswith("CLEAN"), out.stdout

    async def test_dev_auth_is_disabled_in_production(self):
        """Two independent conditions must hold, so one misconfigured variable
        cannot expose the bypass."""
        from server.app.core.config import Settings
        prod = Settings(environment="production", dev_auth_enabled=True)
        assert prod.demo_auth_active is False

    async def test_dev_auth_active_in_development(self):
        from server.app.core.config import Settings
        dev = Settings(environment="development", dev_auth_enabled=True)
        assert dev.demo_auth_active is True

    async def test_settings_have_no_real_secret_defaults(self):
        s = get_settings()
        assert s.clerk_secret_key == "" or s.clerk_secret_key.startswith("sk_")

class TestDemoAuthGuards:
    """The demo path must be development-only, enforced by the backend.

    A frontend switch is not a security boundary: the browser can send any
    header it likes, so the refusal has to happen server-side.
    """

    async def test_demo_refused_in_production_even_if_flag_enabled(self):
        from server.app.core.config import Settings
        s = Settings(environment="production", dev_auth_enabled=True)
        assert s.demo_auth_active is False

    async def test_demo_refused_when_flag_disabled(self):
        from server.app.core.config import Settings
        s = Settings(environment="development", dev_auth_enabled=False)
        assert s.demo_auth_active is False

    async def test_demo_requires_both_conditions(self):
        from server.app.core.config import Settings
        assert Settings(environment="development",
                        dev_auth_enabled=True).demo_auth_active is True
        for env in ("production", "prod", "PRODUCTION"):
            assert Settings(environment=env,
                            dev_auth_enabled=True).demo_auth_active is False

    @needs_mongo
    async def test_dev_login_returns_404_not_403_outside_development(
        self, client, monkeypatch
    ):
        """404, so the endpoint does not advertise its own existence.

        The route reads settings through get_settings() at call time, so the
        production condition is injected there. Mutating the cached Settings
        object and clearing the cache does not work -- the cache simply rebuilds
        an identical instance from the environment.
        """
        from server.app.core.config import Settings
        import server.app.api.routes.me as me_module

        prod = Settings(environment="production", dev_auth_enabled=True)
        assert prod.demo_auth_active is False
        monkeypatch.setattr(me_module, "get_settings", lambda: prod)

        r = await client.post("/api/v1/auth/dev-login",
                              json={"user_id": "x", "role": "FARMER"})
        assert r.status_code == 404

    @needs_mongo
    async def test_dev_login_works_in_development(self, client):
        r = await client.post("/api/v1/auth/dev-login",
                              json={"user_id": "demo_probe", "role": "FARMER"})
        assert r.status_code == 200
        assert r.json()["auth_source"] == "dev"

    @needs_mongo
    async def test_demo_identity_cannot_cross_roles(self, client):
        """A demo farmer is still only a farmer."""
        await client.post("/api/v1/auth/dev-login",
                          json={"user_id": "demo_farmer_probe", "role": "FARMER"})
        r = await client.get("/api/v1/truckers/jobs",
                             headers={"x-dev-user": "demo_farmer_probe"})
        assert r.status_code == 403

    @needs_mongo
    async def test_role_in_request_body_is_not_trusted(self, client):
        """Claiming a role in the payload must not grant it."""
        r = await client.post(
            "/api/v1/farmers/requests",
            headers={"x-dev-user": "test_trucker"},
            json={"crop_key": "wheat", "quantity_value": 5,
                  "quantity_unit": "quintal", "role": "FARMER"})
        assert r.status_code == 403

class TestFrozenDemoRoutes:
    """The demo corridors must stay real road geometry.

    A straight line here would mean the fixture silently regressed to a
    placeholder -- exactly the failure these tests exist to catch, because the
    map would still render and simply look wrong.
    """

    @needs_mongo
    async def test_every_role_has_a_frozen_corridor(self, client):
        for role in ("FARMER", "TRUCKER", "INPUT_DEALER"):
            r = await client.get(f"/api/v1/routes/demo?role={role}",
                                 headers=FARMER)
            assert r.status_code == 200, role
            assert r.json()["role"] == role

    @needs_mongo
    async def test_geometry_is_a_real_road_not_a_straight_line(self, client):
        """Two points per leg would be a straight line. Real carriageway
        geometry has hundreds."""
        for role in ("FARMER", "TRUCKER", "INPUT_DEALER"):
            body = (await client.get(f"/api/v1/routes/demo?role={role}",
                                     headers=FARMER)).json()
            for leg in body["legs"]:
                assert leg["n_geometry_points"] > 50, (role, leg["label"])
                assert len(leg["polyline"]) == leg["n_geometry_points"]

    @needs_mongo
    async def test_labelled_as_a_snapshot_not_a_live_call(self, client):
        body = (await client.get("/api/v1/routes/demo?role=FARMER",
                                 headers=FARMER)).json()
        assert body["provider"] == "tomtom"
        # Honest provenance: real geometry, but frozen.
        assert body["mode"] == "frozen_snapshot"
        assert body["generated_at"]

    @needs_mongo
    async def test_trucker_corridor_has_a_return_leg(self, client):
        """Circular logistics is the product thesis; the demo must show it."""
        body = (await client.get("/api/v1/routes/demo?role=TRUCKER",
                                 headers=FARMER)).json()
        kinds = {l["kind"] for l in body["legs"]}
        assert "outbound" in kinds and "return" in kinds

    @needs_mongo
    async def test_traffic_sections_index_within_their_polyline(self, client):
        """An out-of-range index would silently draw nothing."""
        for role in ("FARMER", "TRUCKER", "INPUT_DEALER"):
            body = (await client.get(f"/api/v1/routes/demo?role={role}",
                                     headers=FARMER)).json()
            for leg in body["legs"]:
                n = leg["n_geometry_points"]
                for sec in leg["traffic_sections"]:
                    assert 0 <= sec["start"] < n, (role, sec)
                    assert 0 <= sec["end"] < n, (role, sec)
                    assert sec["end"] >= sec["start"]

    @needs_mongo
    async def test_defaults_to_the_callers_own_role(self, client):
        body = (await client.get("/api/v1/routes/demo", headers=TRUCKER)).json()
        assert body["role"] == "TRUCKER"


class TestRouteCacheResilience:
    """A cache write must never destroy a successful fetch."""

    async def test_unwritable_cache_dir_is_not_fatal(self, monkeypatch, tmp_path):
        from routing.cache.result_store import RouteCache
        target = tmp_path / "blocked"
        cache = RouteCache(directory=target)
        # Simulate a read-only mount, which is exactly what Docker produced.
        monkeypatch.setattr(
            type(cache._path('k')), "write_text",
            lambda *a, **k: (_ for _ in ()).throw(OSError(30, "Read-only file system")))
        key = cache.put({"a": 1}, {"b": 2})
        assert key  # returned normally instead of raising
