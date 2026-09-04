"""TomTom routing provider.

Design notes:

* **Key rotation.** Several freemium keys are configured; on a 403/429 the
  provider rotates to the next and retries. A key that has been exhausted is
  parked rather than retried in a loop.

* **Caching, not harvesting.** Responses go into a short-TTL operational cache
  (``RouteCache``). They are never written into ``Data/``: TomTom's terms on
  storing and redistributing responses as derived training data are unverified,
  and ``DATA_SOURCES.md`` records that explicitly.

* **No full O-D sweep.** ``get_matrix`` on n points is n^2 calls, which burns a
  freemium quota in minutes and is unnecessary. Callers should sparsify first
  (see ``routing.hybrid.candidate_reduction``); this class enforces a hard cap.

* **Degradation, not failure.** With no key configured, the provider reports
  ``available = False`` and callers fall back to ``OfflineGraphProvider``. The
  live application must keep working without a routing vendor.
"""

from __future__ import annotations

import logging
import os
import time
from itertools import cycle

import numpy as np
import requests

from routing.cache.result_store import RouteCache
from routing.models import LatLon, RouteCandidate
from routing.providers.base import RoutingProvider
from vb.enums import Volatility

log = logging.getLogger(__name__)

BASE_URL = os.environ.get("TOMTOM_BASE_URL", "https://api.tomtom.com")
# A full matrix over even a modest instance is quota suicide on freemium.
MAX_MATRIX_CELLS = 400
DIESEL_PRICE_INR_PER_L = 92.0
DEFAULT_KMPL = 5.0


class TomTomRoutingProvider(RoutingProvider):
    name = "tomtom"

    def __init__(
        self, api_keys: list[str] | None = None, *,
        cache: RouteCache | None = None, timeout: float = 12.0,
    ) -> None:
        keys = api_keys or [
            k.strip() for k in os.environ.get("TOMTOM_API_KEYS", "").split(",") if k.strip()
        ]
        self._keys = keys
        self._key_cycle = cycle(keys) if keys else None
        self._current = next(self._key_cycle) if self._key_cycle else None
        self._exhausted: set[str] = set()
        self.cache = cache or RouteCache()
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self._keys) and len(self._exhausted) < len(self._keys)

    def _rotate(self) -> bool:
        """Move to the next usable key. False when every key is exhausted."""
        if not self._key_cycle:
            return False
        self._exhausted.add(self._current)
        for _ in range(len(self._keys)):
            nxt = next(self._key_cycle)
            if nxt not in self._exhausted:
                log.warning("tomtom: rotating to next API key")
                self._current = nxt
                return True
        return False

    def _get(self, url: str, params: dict) -> dict | None:
        """GET with key rotation. Returns None when no key can serve it."""
        for _ in range(len(self._keys) or 1):
            if not self._current:
                return None
            try:
                r = requests.get(
                    url, params={**params, "key": self._current}, timeout=self.timeout
                )
            except requests.RequestException as e:
                log.warning("tomtom: request failed: %s", e)
                return None
            if r.status_code == 200:
                return r.json()
            # 401 belongs here too: an expired or revoked key is exactly the
            # case key rotation exists for. Without it a dead first key would
            # fail every request while two working keys sat unused.
            if r.status_code in (401, 403, 429):
                if not self._rotate():
                    log.error("tomtom: all API keys exhausted")
                    return None
                time.sleep(0.2)
                continue
            log.warning("tomtom: HTTP %s -- %s", r.status_code, r.text[:200])
            return None
        return None

    # --- normalization ------------------------------------------------------

    def _to_candidate(
        self, leg: dict, origin_id: str, destination_id: str, idx: int
    ) -> RouteCandidate:
        """Turn one TomTom route object into our internal representation.

        Fields TomTom does not return for a given plan (tolls in particular are
        not always present) are left at their neutral default rather than
        guessed, so a missing toll never masquerades as a free road.
        """
        summary = leg.get("summary", {})
        dist_km = summary.get("lengthInMeters", 0) / 1000.0
        travel_s = summary.get("travelTimeInSeconds", 0)
        delay_s = summary.get("trafficDelayInSeconds", 0)

        geometry: list[tuple[float, float]] = []
        for section in leg.get("legs", []):
            for p in section.get("points", []):
                geometry.append((p["latitude"], p["longitude"]))

        return RouteCandidate(
            route_id=f"TT_{origin_id}_{destination_id}_{idx}",
            origin_id=origin_id,
            destination_id=destination_id,
            distance_km=round(dist_km, 3),
            # travel_time is free-flow-equivalent; delay is reported separately
            # so the objective can price congestion explicitly.
            travel_time_min=round((travel_s - delay_s) / 60.0, 2),
            traffic_delay_min=round(delay_s / 60.0, 2),
            estimated_fuel_cost_inr=round(dist_km / DEFAULT_KMPL * DIESEL_PRICE_INR_PER_L, 2),
            geometry=geometry,
            traffic_snapshot_time=summary.get("departureTime"),
            source="tomtom",
        )

    # --- interface ----------------------------------------------------------

    def get_alternative_routes(
        self, origin: LatLon, destination: LatLon, max_alternatives: int = 3, **kw
    ) -> list[RouteCandidate]:
        origin_id = kw.pop("origin_id", "O")
        destination_id = kw.pop("destination_id", "D")
        req = {
            "op": "routes", "o": origin.as_tuple(), "d": destination.as_tuple(),
            "alt": max_alternatives, **kw,
        }
        if (hit := self.cache.get(req)) is not None:
            # to_dict() adds n_geometry_points, which is a derived field and not
            # a constructor argument. Storing it and replaying it verbatim made
            # every cache hit raise TypeError and silently degrade to the
            # straight-line fallback -- the first call worked, every repeat did
            # not. Strip derived keys on the way back in.
            fields = set(RouteCandidate.__dataclass_fields__)
            return [
                RouteCandidate(**{k: v for k, v in c.items() if k in fields})
                for c in hit
            ]
        if not self.available:
            return []

        loc = f"{origin.lat},{origin.lon}:{destination.lat},{destination.lon}"
        data = self._get(
            f"{BASE_URL}/routing/1/calculateRoute/{loc}/json",
            {
                "routeType": kw.get("route_type", "fastest"),
                "traffic": "true",
                "travelMode": kw.get("travel_mode", "truck"),
                "maxAlternatives": max_alternatives,
                "instructionsType": "text",
            },
        )
        if not data or "routes" not in data:
            return []

        candidates = [
            self._to_candidate(r, origin_id, destination_id, i)
            for i, r in enumerate(data["routes"])
        ]
        # Traffic-derived, so dynamic: this expires in minutes, by design.
        self.cache.put(
            req, [c.to_dict() | {"geometry": c.geometry} for c in candidates],
            volatility=Volatility.DYNAMIC, provider="tomtom",
        )
        return candidates

    def get_route(self, origin: LatLon, destination: LatLon, **kw) -> RouteCandidate:
        routes = self.get_alternative_routes(origin, destination, max_alternatives=0, **kw)
        if not routes:
            raise RuntimeError("TomTom returned no route and no cached result is available")
        return routes[0]

    def get_matrix(
        self, origins: list[LatLon], destinations: list[LatLon], **kw
    ) -> tuple[np.ndarray, np.ndarray]:
        cells = len(origins) * len(destinations)
        if cells > MAX_MATRIX_CELLS:
            raise ValueError(
                f"refusing a {len(origins)}x{len(destinations)} matrix ({cells} cells, "
                f"cap {MAX_MATRIX_CELLS}). Sparsify the graph first -- see "
                "routing.hybrid.candidate_reduction."
            )
        dist = np.zeros((len(origins), len(destinations)))
        dur = np.zeros_like(dist)
        for i, o in enumerate(origins):
            for j, d in enumerate(destinations):
                if i == j:
                    continue
                try:
                    r = self.get_route(o, d, **kw)
                    dist[i, j] = r.distance_km
                    dur[i, j] = r.travel_time_min + r.traffic_delay_min
                except RuntimeError:
                    dist[i, j] = np.nan
                    dur[i, j] = np.nan
        return dist, dur

    def get_traffic_flow(self, point: LatLon) -> dict | None:
        """Current vs free-flow speed at a point. Used for corridor scoring."""
        req = {"op": "flow", "p": point.as_tuple()}
        if (hit := self.cache.get(req)) is not None:
            return hit
        if not self.available:
            return None
        data = self._get(
            f"{BASE_URL}/traffic/services/4/flowSegmentData/relative0/10/json",
            {"point": f"{point.lat},{point.lon}"},
        )
        if not data:
            return None
        seg = data.get("flowSegmentData", {})
        out = {
            "current_speed": seg.get("currentSpeed"),
            "free_flow_speed": seg.get("freeFlowSpeed"),
            "confidence": seg.get("confidence"),
            "ratio": (seg.get("currentSpeed", 0) / seg["freeFlowSpeed"])
            if seg.get("freeFlowSpeed") else None,
        }
        self.cache.put(req, out, volatility=Volatility.DYNAMIC, provider="tomtom")
        return out
