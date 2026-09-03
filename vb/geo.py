"""Geospatial primitives. All canonical coordinates are WGS84 / EPSG:4326."""

from __future__ import annotations

import math

import numpy as np

from vb.config import COARSE_BBOX

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance. Used as a QA baseline and as a feature -- never
    as the production road distance."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def haversine_matrix(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Vectorized all-pairs great-circle distance in km."""
    la = np.radians(lats)[:, None]
    lo = np.radians(lons)[:, None]
    dlat = la - la.T
    dlon = lo - lo.T
    a = np.sin(dlat / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def km_to_deg_lat(km: float) -> float:
    return km / 110.574


def km_to_deg_lon(km: float, at_lat: float) -> float:
    return km / (111.320 * math.cos(math.radians(at_lat)))


def in_coarse_bbox(lat: float, lon: float) -> bool:
    """Cheap rejection test for the north-India project region.

    This is a smoke test, not validation. Passing it says only that a point is
    not wildly misplaced; real containment is checked against district
    geometry in ``vb.validate.geo_qa``.
    """
    b = COARSE_BBOX
    return b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"]


def sample_clustered(
    rng: np.random.Generator,
    center_lat: float,
    center_lon: float,
    radius_km: float,
    n: int,
    n_clusters: int = 6,
    cluster_spread_km: float = 4.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample settlement-like points inside a district envelope.

    Uniform sampling over a district produces an unrealistically even carpet of
    villages. Real settlements cluster along corridors and around market towns,
    so we draw a handful of cluster seeds within the envelope and scatter points
    around them with a Gaussian spread. The radial seed placement uses sqrt(u)
    so seeds are area-uniform rather than piled at the centre.
    """
    seed_r = radius_km * np.sqrt(rng.uniform(0.05, 1.0, n_clusters))
    seed_t = rng.uniform(0, 2 * math.pi, n_clusters)
    seed_lat = center_lat + km_to_deg_lat(1) * seed_r * np.sin(seed_t)
    seed_lon = center_lon + np.array(
        [km_to_deg_lon(1, center_lat) * r * math.cos(t) for r, t in zip(seed_r, seed_t)]
    )

    which = rng.integers(0, n_clusters, n)
    spread_lat = km_to_deg_lat(cluster_spread_km)
    spread_lon = km_to_deg_lon(cluster_spread_km, center_lat)
    lat = seed_lat[which] + rng.normal(0, spread_lat, n)
    lon = seed_lon[which] + rng.normal(0, spread_lon, n)

    # Clamp back into the district envelope so nothing escapes its district.
    max_dlat = km_to_deg_lat(radius_km)
    max_dlon = km_to_deg_lon(radius_km, center_lat)
    lat = np.clip(lat, center_lat - max_dlat, center_lat + max_dlat)
    lon = np.clip(lon, center_lon - max_dlon, center_lon + max_dlon)
    return lat, lon


def road_access_proxy(
    lat: np.ndarray, lon: np.ndarray, center_lat: float, center_lon: float,
    radius_km: float, urbanisation: float,
) -> np.ndarray:
    """Crude 0-1 road-access score.

    We have no real road network at generation time, so accessibility is
    approximated as decaying with distance from the district town and rising
    with urbanisation. This is a *prior* for generating plausible shop and
    farmer placement, not a measured quantity, and route costs never use it.
    """
    d = np.array([haversine_km(a, b, center_lat, center_lon) for a, b in zip(lat, lon)])
    proximity = np.clip(1.0 - d / max(radius_km, 1e-6), 0.0, 1.0)
    return np.clip(0.35 + 0.45 * proximity + 0.30 * urbanisation, 0.0, 1.0)
