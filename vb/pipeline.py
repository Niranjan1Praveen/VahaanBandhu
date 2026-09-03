"""Phase-A master data pipeline.

Runs acquisition -> normalization -> generation -> export in dependency order
and writes a manifest for every table. Deterministic given (seed, config).

    python -m vb.pipeline --stage prototype --version v0.1
"""

from __future__ import annotations

import argparse
import logging
import time

import pandas as pd

from vb import config as C
from vb.config import GenerationConfig
from vb.generate import farmers, graph, instances, locations, mandis, shops, trucks
from vb.generate.requests import build_transport_requests
from vb.io import write_table
from vb.source_registry import write_source_registry
from vb.splits import split_instances, split_requests

log = logging.getLogger("vb.pipeline")


def run(cfg: GenerationConfig, *, overwrite: bool = False) -> dict[str, pd.DataFrame]:
    C.ensure_dirs()
    cfg.save()
    t0 = time.time()
    out: dict[str, pd.DataFrame] = {}

    def emit(name, df, path, provenance, description):
        write_table(df, path, cfg, description=description,
                    provenance=provenance, overwrite=overwrite)
        out[name] = df
        log.info("%-24s %7d rows -> %s", name, len(df), path.name)

    log.info("--- source registry ---")
    write_source_registry(cfg)

    log.info("--- geography ---")
    villages = locations.build_villages(cfg)
    depots = locations.build_depots(cfg)

    log.info("--- mandis ---")
    mandi_locs, mandi_df, mandi_commodities = mandis.build_mandis(cfg)
    crops_df = mandis.build_crops(cfg)

    log.info("--- shops ---")
    shop_locs, shops_df = shops.build_shops(cfg, villages)

    # The location master is the union of every spatial entity, so route edges
    # and instances only ever deal in one ID space.
    locations_master = pd.concat(
        [villages, depots, mandi_locs, shop_locs], ignore_index=True
    )

    log.info("--- farmer nodes / fleet ---")
    farmer_df = farmers.build_farmer_nodes(cfg, villages, mandi_locs)
    trucks_df = trucks.build_trucks(cfg, depots)
    availability_df = trucks.build_truck_availability(cfg, trucks_df)

    log.info("--- requests + NLU corpus ---")
    requests_df = build_transport_requests(
        cfg, farmer_df, shops_df, mandi_locs, shop_locs, trucks_df
    )

    log.info("--- route graph ---")
    edges_df = graph.build_route_edges(cfg, locations_master)
    scenarios_df = graph.build_scenarios_table(cfg)

    log.info("--- optimization instances ---")
    instances_df, instance_requests_df = instances.build_route_instances(
        cfg, requests_df, trucks_df, locations_master, depots
    )

    log.info("--- splits ---")
    requests_df = split_requests(requests_df, cfg.holdout_districts, cfg.holdout_time_from)
    instances_df = split_instances(instances_df, cfg.holdout_districts)

    M, S = C.MASTER, C.SYNTHETIC
    emit("locations_master", locations_master, M / "locations_master.csv", "mixed",
         "Spatial spine: villages, depots, mandis and shops in one ID space.")
    emit("mandis", mandi_df, M / "mandis.csv", "mixed",
         "Real mandi names with approximate town-level coordinates.")
    emit("mandi_commodities", mandi_commodities, M / "mandi_commodities.csv", "mixed",
         "Junction: which commodities each mandi trades.")
    emit("crops", crops_df, M / "crops.csv", "verified",
         "Crop ontology with Hindi/English aliases and default bag weights.")
    emit("scenarios", scenarios_df, M / "scenarios.csv", "synthetic",
         "Time-dependent routing scenarios. Baseline is never overwritten.")

    emit("shops", shops_df, S / "shops.csv", "synthetic",
         "Synthetic rural building-material dealers on a demand surface.")
    emit("farmer_nodes", farmer_df, S / "farmer_nodes.csv", "synthetic",
         "Privacy-safe farm pickup points on the agricultural envelope.")
    emit("trucks", trucks_df, S / "trucks.csv", "synthetic",
         "Fleet with physically coherent class/capacity/fuel configurations.")
    emit("truck_availability", availability_df, S / "truck_availability.csv", "synthetic",
         "Availability slots supporting circular-logistics matching.")
    emit("transport_requests", requests_df, S / "transport_requests.csv", "synthetic",
         "Farmer and shop requests with Hindi/English/Hinglish utterances.")
    emit("route_edges", edges_df, S / "route_edges.csv", "synthetic",
         "Directed road-cost graph, per scenario. Offline detour model.")
    emit("route_instances", instances_df, S / "route_instances.csv", "synthetic",
         "Canonical optimization instances shared by all solvers.")
    emit("instance_requests", instance_requests_df, S / "instance_requests.csv", "synthetic",
         "Junction: which requests belong to which instance.")

    log.info("pipeline complete in %.1fs", time.time() - t0)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="VahaanBandhu Phase-A data pipeline")
    p.add_argument("--stage", default="prototype", choices=list(C.STAGE_SIZES))
    p.add_argument("--version", default="v0.1")
    p.add_argument("--seed", type=int, default=20260903)
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = GenerationConfig(stage=a.stage, dataset_version=a.version, seed=a.seed)
    run(cfg, overwrite=a.overwrite)


if __name__ == "__main__":
    main()
