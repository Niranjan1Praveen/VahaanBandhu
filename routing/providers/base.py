"""Routing provider interface.

The rest of the system talks to this, never to a vendor SDK. Two consequences
that matter: the optimizer can be tested with no network at all, and swapping
TomTom for another provider is a one-file change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from routing.models import LatLon, RouteCandidate


class RoutingProvider(ABC):
    """Road-network and traffic information source."""

    name: str = "abstract"

    @abstractmethod
    def get_route(self, origin: LatLon, destination: LatLon, **kw) -> RouteCandidate:
        """Single best route between two points."""

    @abstractmethod
    def get_alternative_routes(
        self, origin: LatLon, destination: LatLon, max_alternatives: int = 3, **kw
    ) -> list[RouteCandidate]:
        """Several distinct feasible routes, for the selection layer to score."""

    @abstractmethod
    def get_matrix(
        self, origins: list[LatLon], destinations: list[LatLon], **kw
    ) -> tuple[np.ndarray, np.ndarray]:
        """(distance_km, duration_min) matrices."""

    def get_distance(self, origin: LatLon, destination: LatLon, **kw) -> float:
        return self.get_route(origin, destination, **kw).distance_km

    def get_duration(self, origin: LatLon, destination: LatLon, **kw) -> float:
        r = self.get_route(origin, destination, **kw)
        return r.travel_time_min + r.traffic_delay_min
