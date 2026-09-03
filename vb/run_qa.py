"""Run the full Phase-A validation suite.

    python -m vb.run_qa
"""

from __future__ import annotations

import json
import logging
import sys

import pandas as pd
import pandera.errors

from vb import config as C
from vb.config import GenerationConfig
from vb.splits import check_leakage
from vb.validate import qa
from vb.validate.schemas import SCHEMAS

log = logging.getLogger("vb.qa")

TABLE_PATHS = {
    "locations_master": C.MASTER / "locations_master.csv",
    "mandis": C.MASTER / "mandis.csv",
    "mandi_commodities": C.MASTER / "mandi_commodities.csv",
    "crops": C.MASTER / "crops.csv",
    "scenarios": C.MASTER / "scenarios.csv",
    "shops": C.SYNTHETIC / "shops.csv",
    "farmer_nodes": C.SYNTHETIC / "farmer_nodes.csv",
    "trucks": C.SYNTHETIC / "trucks.csv",
    "truck_availability": C.SYNTHETIC / "truck_availability.csv",
    "transport_requests": C.SYNTHETIC / "transport_requests.csv",
    "route_edges": C.SYNTHETIC / "route_edges.csv",
    "route_instances": C.SYNTHETIC / "route_instances.csv",
    "instance_requests": C.SYNTHETIC / "instance_requests.csv",
}


def load_all() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_csv(path, low_memory=False)
        for name, path in TABLE_PATHS.items() if path.exists()
    }


def run() -> dict:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = GenerationConfig()
    tables = load_all()
    results: dict[str, object] = {}

    log.info("=== schema validation ===")
    schema_results = {}
    for name, schema in SCHEMAS.items():
        if name not in tables:
            continue
        try:
            schema.validate(tables[name], lazy=True)
            schema_results[name] = {"passed": True, "n_failures": 0}
            log.info("  %-22s PASS", name)
        except pandera.errors.SchemaErrors as e:
            failures = e.failure_cases
            schema_results[name] = {
                "passed": False,
                "n_failures": int(len(failures)),
                "checks": failures["check"].value_counts().to_dict(),
                "examples": failures.head(10).to_dict("records"),
            }
            log.error("  %-22s FAIL (%d cases)", name, len(failures))
            for chk, cnt in failures["check"].value_counts().head(6).items():
                log.error("       %s: %d", chk, cnt)
    results["schemas"] = schema_results

    log.info("=== geospatial QA ===")
    results["geospatial"] = qa.geospatial_qa(tables["locations_master"], tables["route_edges"])
    log.info("  passed=%s", results["geospatial"]["passed"])

    log.info("=== referential QA ===")
    results["referential"] = qa.referential_qa(tables)
    log.info("  passed=%s", results["referential"]["passed"])

    log.info("=== statistical QA ===")
    results["statistical"] = qa.statistical_qa(tables)
    log.info("  passed=%s", results["statistical"]["passed"])

    log.info("=== leakage QA ===")
    results["leakage"] = check_leakage(
        tables["transport_requests"], tables["route_instances"], cfg.holdout_districts
    )
    log.info("  passed=%s", results["leakage"]["passed"])

    all_passed = (
        all(v["passed"] for v in schema_results.values())
        and results["geospatial"]["passed"]
        and results["referential"]["passed"]
        and results["statistical"]["passed"]
        and results["leakage"]["passed"]
    )
    results["all_passed"] = all_passed

    C.QA.mkdir(parents=True, exist_ok=True)
    (C.QA / "qa_summary.json").write_text(
        json.dumps(results, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    log.info("=== OVERALL: %s ===", "PASS" if all_passed else "FAIL")
    return results


if __name__ == "__main__":
    sys.exit(0 if run()["all_passed"] else 1)
