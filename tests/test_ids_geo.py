"""Identifier stability, geography helpers and NCR flagging."""

from __future__ import annotations

import numpy as np
import pytest

from vb.geo import haversine_km, haversine_matrix, in_coarse_bbox, sample_clustered
from vb.ids import content_id, edge_id, instance_hash, slug
from vb.reference import districts as dref


class TestIdentifiers:
    def test_content_ids_are_deterministic(self):
        """Regeneration must not invalidate cached solver results."""
        a = content_id("location", "village", "HR", "Karnal", "Rampur", 3)
        b = content_id("location", "village", "HR", "Karnal", "Rampur", 3)
        assert a == b

    def test_different_content_gives_different_ids(self):
        a = content_id("location", "village", "HR", "Karnal", "Rampur", 3)
        b = content_id("location", "village", "HR", "Karnal", "Rampur", 4)
        assert a != b

    def test_id_carries_its_type_prefix(self):
        assert content_id("mandi", "azadpur").startswith("MND_")
        assert content_id("truck", "x").startswith("TRK_")

    def test_unknown_kind_is_rejected(self):
        with pytest.raises(KeyError):
            content_id("spaceship", "x")

    def test_edges_are_directed(self):
        """A->B and B->A must be distinct rows with distinct IDs."""
        ab = edge_id("LOC_A", "LOC_B", "SCN_BASELINE")
        ba = edge_id("LOC_B", "LOC_A", "SCN_BASELINE")
        assert ab != ba

    def test_edge_id_depends_on_scenario(self):
        assert (edge_id("LOC_A", "LOC_B", "SCN_BASELINE")
                != edge_id("LOC_A", "LOC_B", "SCN_NIGHT"))

    def test_instance_hash_is_permutation_invariant(self):
        """Two orderings of the same problem are the same problem, and must
        not be allowed to land on opposite sides of a train/test split."""
        h1 = instance_hash(["a", "b", "c"], [10.0, 20.0, 30.0], 5000)
        h2 = instance_hash(["c", "a", "b"], [30.0, 10.0, 20.0], 5000)
        assert h1 == h2

    def test_instance_hash_changes_with_capacity(self):
        assert (instance_hash(["a", "b"], [1.0, 2.0], 5000)
                != instance_hash(["a", "b"], [1.0, 2.0], 9000))

    def test_slug_handles_devanagari(self):
        # Non-ASCII collapses, which is why callers must pass an English key too.
        assert slug("Karnal Mandi") == "karnal-mandi"


class TestGeo:
    def test_haversine_known_distance(self):
        # Delhi to Chandigarh is roughly 240 km great-circle.
        d = haversine_km(28.6139, 77.2090, 30.7333, 76.7794)
        assert 230 < d < 250

    def test_haversine_is_zero_for_same_point(self):
        assert haversine_km(28.6, 77.2, 28.6, 77.2) == pytest.approx(0.0, abs=1e-9)

    def test_matrix_matches_scalar(self):
        lats = np.array([28.6, 29.4, 30.9])
        lons = np.array([77.2, 76.9, 75.8])
        M = haversine_matrix(lats, lons)
        assert M[0, 1] == pytest.approx(haversine_km(28.6, 77.2, 29.4, 76.9), rel=1e-6)
        assert np.allclose(np.diag(M), 0)
        assert np.allclose(M, M.T)  # geodesic distance is symmetric

    def test_coarse_bbox_accepts_project_region(self):
        assert in_coarse_bbox(28.6139, 77.2090)   # Delhi
        assert in_coarse_bbox(32.2740, 75.6520)   # Pathankot, northern Punjab

    def test_coarse_bbox_rejects_elsewhere(self):
        assert not in_coarse_bbox(19.0760, 72.8777)  # Mumbai
        assert not in_coarse_bbox(51.5074, -0.1278)  # London

    def test_clustered_sampling_stays_in_envelope(self):
        rng = np.random.default_rng(0)
        lat, lon = sample_clustered(rng, 29.0, 76.5, 25.0, 300)
        d = np.array([haversine_km(a, b, 29.0, 76.5) for a, b in zip(lat, lon)])
        assert d.max() <= 25.0 * 1.5

    def test_clustered_sampling_is_not_uniform(self):
        """Villages should cluster. A uniform carpet makes routing trivial."""
        rng = np.random.default_rng(1)
        lat, lon = sample_clustered(rng, 29.0, 76.5, 25.0, 500, n_clusters=5)
        d = np.array([haversine_km(a, b, 29.0, 76.5) for a, b in zip(lat, lon)])
        # A uniform disc has std/mean around 0.33; clustering pushes it higher.
        assert d.std() / d.mean() > 0.2


class TestNCRGeography:
    def test_ncr_is_explicit_not_inferred_from_state(self):
        """The whole point of the NCR flag: Haryana contains both NCR and
        non-NCR districts, so state alone cannot determine membership."""
        assert dref.is_ncr("Gurugram")
        assert dref.is_ncr("Karnal")
        assert not dref.is_ncr("Amritsar")
        assert not dref.is_ncr("Hisar")

    def test_haryana_has_both_ncr_and_non_ncr_districts(self):
        hr = [d for d in dref.DISTRICTS if d.state_code == "HR"]
        assert any(d.in_ncr for d in hr)
        assert any(not d.in_ncr for d in hr)

    def test_no_punjab_district_is_in_ncr(self):
        assert not any(d.in_ncr for d in dref.DISTRICTS if d.state_code == "PB")

    def test_every_delhi_district_is_in_ncr(self):
        assert all(d.in_ncr for d in dref.DISTRICTS if d.state_code == "DL")

    def test_unknown_district_is_not_ncr(self):
        assert not dref.is_ncr("Nowhere")

    def test_all_district_centroids_are_in_region(self):
        for d in dref.DISTRICTS:
            assert in_coarse_bbox(d.lat, d.lon), f"{d.district} is outside the region"
