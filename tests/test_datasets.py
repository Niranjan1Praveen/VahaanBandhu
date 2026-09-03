"""Dataset-level integrity: schemas, foreign keys, determinism, leakage.

These run against the generated prototype datasets, so they double as a
regression suite for the pipeline. They skip cleanly if the data has not been
generated yet.
"""

from __future__ import annotations

import pandas as pd
import pytest

from vb import config as C
from vb.config import GenerationConfig
from vb.splits import check_leakage
from vb.validate.schemas import SCHEMAS

pytestmark = pytest.mark.skipif(
    not (C.MASTER / "locations_master.csv").exists(),
    reason="prototype datasets not generated; run `python -m vb.pipeline`",
)

PATHS = {
    "locations_master": C.MASTER / "locations_master.csv",
    "mandis": C.MASTER / "mandis.csv",
    "crops": C.MASTER / "crops.csv",
    "shops": C.SYNTHETIC / "shops.csv",
    "farmer_nodes": C.SYNTHETIC / "farmer_nodes.csv",
    "trucks": C.SYNTHETIC / "trucks.csv",
    "transport_requests": C.SYNTHETIC / "transport_requests.csv",
    "route_edges": C.SYNTHETIC / "route_edges.csv",
    "route_instances": C.SYNTHETIC / "route_instances.csv",
    "instance_requests": C.SYNTHETIC / "instance_requests.csv",
}


@pytest.fixture(scope="module")
def tables():
    return {k: pd.read_csv(v, low_memory=False) for k, v in PATHS.items() if v.exists()}


class TestSchemas:
    @pytest.mark.parametrize("name", list(SCHEMAS))
    def test_table_matches_schema(self, tables, name):
        if name not in tables:
            pytest.skip(f"{name} not generated")
        SCHEMAS[name].validate(tables[name], lazy=True)


class TestForeignKeys:
    def test_every_entity_resolves_to_a_location(self, tables):
        loc_ids = set(tables["locations_master"]["location_id"])
        for table, col in [("mandis", "location_id"), ("shops", "location_id"),
                           ("farmer_nodes", "village_location_id"),
                           ("trucks", "home_location_id")]:
            missing = set(tables[table][col]) - loc_ids
            assert not missing, f"{table}.{col} has {len(missing)} dangling refs"

    def test_route_edges_reference_real_locations(self, tables):
        loc_ids = set(tables["locations_master"]["location_id"])
        e = tables["route_edges"]
        assert not set(e["origin_location_id"]) - loc_ids
        assert not set(e["destination_location_id"]) - loc_ids

    def test_instance_membership_resolves(self, tables):
        req_ids = set(tables["transport_requests"]["request_id"])
        inst_ids = set(tables["route_instances"]["instance_id"])
        j = tables["instance_requests"]
        assert not set(j["request_id"]) - req_ids
        assert not set(j["instance_id"]) - inst_ids

    def test_all_ids_are_unique(self, tables):
        for table, col in [("locations_master", "location_id"), ("mandis", "mandi_id"),
                           ("shops", "shop_id"), ("trucks", "truck_id"),
                           ("transport_requests", "request_id"),
                           ("route_instances", "instance_id")]:
            assert tables[table][col].is_unique, f"{table}.{col} has duplicates"


class TestProvenanceRules:
    def test_no_synthetic_entity_is_marked_verified(self, tables):
        loc = tables["locations_master"]
        syn = loc[loc["is_synthetic"]]
        assert (syn["confidence_score"] == 0).all()
        assert syn["verified_at"].isna().all()

    def test_mandis_do_not_claim_verified_coordinates(self, tables):
        """Phase-A has no sourced mandi coordinates. Claiming otherwise would
        misrepresent town-level approximations as surveyed positions."""
        assert not tables["mandis"]["coordinate_verified"].any()

    def test_every_table_declares_a_dataset_version(self, tables):
        for name, df in tables.items():
            if "dataset_version" in df.columns:
                assert df["dataset_version"].notna().all(), name

    def test_source_registry_exists_and_records_blockers(self):
        assert C.SOURCE_REGISTRY.exists()
        reg = pd.read_csv(C.SOURCE_REGISTRY)
        # Unacquired official sources must be recorded, not omitted.
        assert (reg["status"] == "blocked").any()


class TestQuantityRules:
    def test_unresolved_quantities_have_no_kilogram_value(self, tables):
        r = tables["transport_requests"]
        unresolved = r[r["conversion_confidence"] == "unresolved"]
        assert unresolved["quantity_kg"].isna().all()

    def test_no_feasible_request_has_a_non_positive_quantity(self, tables):
        r = tables["transport_requests"]
        feasible = r[r["feasibility_label"] == "feasible"]
        assert (feasible["quantity_kg"] > 0).all()

    def test_over_capacity_loads_are_labelled_not_dropped(self, tables):
        r = tables["transport_requests"]
        assert (r["feasibility_label"] == "infeasible").any()

    def test_the_corpus_contains_unresolved_bori_cases(self, tables):
        """If every bori resolved, the converter would not be doing its job."""
        r = tables["transport_requests"]
        assert (r["conversion_confidence"] == "unresolved").sum() > 0


class TestRouteGraph:
    def test_edges_are_directed(self, tables):
        e = tables["route_edges"]
        base = e[e["scenario_id"] == "SCN_BASELINE"]
        fwd = base.set_index(["origin_location_id", "destination_location_id"])["distance_km"]
        rev = base.set_index(["destination_location_id", "origin_location_id"])["distance_km"]
        common = fwd.index.intersection(rev.index)
        if len(common) > 10:
            diff = abs(fwd.loc[common].to_numpy() - rev.loc[common].to_numpy())
            assert diff.max() > 0, "graph is perfectly symmetric; direction is not modelled"

    def test_road_distance_is_never_shorter_than_geodesic(self, tables):
        e = tables["route_edges"]
        assert (e["distance_km"] >= e["haversine_km"] * 0.98).all()

    def test_baseline_scenario_is_present_and_distinct(self, tables):
        e = tables["route_edges"]
        assert "SCN_BASELINE" in set(e["scenario_id"])
        assert e["scenario_id"].nunique() > 1

    def test_scenarios_do_not_overwrite_the_baseline(self, tables):
        e = tables["route_edges"]
        base = e[e["scenario_id"] == "SCN_BASELINE"]["traffic_time_min"].mean()
        peak = e[e["scenario_id"] == "SCN_MORNING_PEAK"]["traffic_time_min"].mean()
        assert peak > base


class TestSplitsAndLeakage:
    def test_leakage_checks_pass(self, tables):
        cfg = GenerationConfig()
        rep = check_leakage(tables["transport_requests"], tables["route_instances"],
                            cfg.holdout_districts)
        assert rep["passed"], rep

    def test_all_three_splits_are_populated(self, tables):
        for t in ("transport_requests", "route_instances"):
            assert set(tables[t]["split"].unique()) == {"train", "validation", "test"}

    def test_held_out_districts_never_appear_in_training(self, tables):
        cfg = GenerationConfig()
        r = tables["transport_requests"]
        train_districts = set(r[r["split"] == "train"]["district"])
        assert not train_districts & set(cfg.holdout_districts)

    def test_no_utterance_appears_in_both_train_and_test(self, tables):
        r = tables["transport_requests"]
        train = set(r[r["split"] == "train"]["raw_utterance"].dropna())
        test = set(r[r["split"] == "test"]["raw_utterance"].dropna())
        assert not train & test


class TestDeterminism:
    def test_same_seed_reproduces_identical_villages(self):
        from vb.generate.locations import build_villages
        cfg = GenerationConfig(seed=999)
        a = build_villages(cfg)
        b = build_villages(cfg)
        pd.testing.assert_frame_equal(a, b)

    def test_different_seeds_produce_different_data(self):
        from vb.generate.locations import build_villages
        a = build_villages(GenerationConfig(seed=1))
        b = build_villages(GenerationConfig(seed=2))
        assert not a["latitude"].equals(b["latitude"])

    def test_config_hash_is_stable(self):
        assert GenerationConfig(seed=7).config_hash() == GenerationConfig(seed=7).config_hash()

    def test_config_hash_changes_with_seed(self):
        assert GenerationConfig(seed=7).config_hash() != GenerationConfig(seed=8).config_hash()


class TestQuantumReadiness:
    def test_quantum_ready_instances_are_actually_encodable(self, tables):
        """A permutation QUBO needs (n+1)^2 qubits. Flagging a 7-node instance
        as quantum-ready would produce a 64-qubit circuit no simulator runs."""
        i = tables["route_instances"]
        qr = i[i["quantum_ready"]]
        assert (qr["estimated_qubits_permutation"] <= 25).all()
        assert (qr["n_vehicles"] == 1).all()

    def test_a_quantum_subset_exists(self, tables):
        assert tables["route_instances"]["quantum_ready"].sum() > 0

    def test_every_instance_names_its_cost_snapshot(self, tables):
        i = tables["route_instances"]
        assert i["cost_snapshot_id"].notna().all()
        assert i["cost_snapshot_id"].nunique() >= 1
