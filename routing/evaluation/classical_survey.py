"""Step 1: identify the best classical baseline, per problem family.

The research benchmark only covered 3-4 node TSPs where every solver tied at the
optimum, and it compared raw tour distance against OR-Tools' weighted objective.
That table could not identify a best algorithm because the numbers were not
comparable and the instances were trivial.

This survey fixes both problems: every solver is scored by
``routing.evaluation.metrics.evaluate`` on the instance's own objective weights,
and instances are sampled across problem types and size bands.

    python -m routing.evaluation.classical_survey
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from routing.classical.heuristics import (
    brute_force_tsp, nearest_neighbour, simulated_annealing, two_opt,
)
from routing.classical.vrp import solve_vrp
from routing.evaluation.metrics import evaluate, tour_to_routes
from routing.instances import list_instances, load_instance
from routing.models import RoutingInstance
from vb import config as C

log = logging.getLogger("vb.survey")

EXACT_NODE_LIMIT = 9


@dataclass
class SurveyRow:
    instance_id: str
    problem_type: str
    size_band: str
    n_nodes: int
    n_vehicles: int
    algorithm: str
    objective: float
    distance_km: float
    time_min: float
    toll_inr: float
    fuel_inr: float
    empty_km: float
    feasible: bool
    violations: str
    runtime_ms: float
    is_exact: bool
    cost_snapshot_id: str
    seed: int


def _row(inst: RoutingInstance, meta: dict, name: str, routes, ms: float,
         *, exact: bool = False, seed: int = 0) -> SurveyRow:
    ev = evaluate(inst, routes)
    return SurveyRow(
        instance_id=inst.instance_id,
        problem_type=inst.problem_type,
        size_band=meta["size_band"],
        n_nodes=inst.n_nodes,
        n_vehicles=len(inst.vehicle_capacities),
        algorithm=name,
        objective=round(ev.objective, 4),
        distance_km=ev.distance_km,
        time_min=ev.time_min,
        toll_inr=ev.toll_inr,
        fuel_inr=ev.fuel_inr,
        empty_km=ev.empty_km,
        feasible=ev.feasible,
        violations=";".join(ev.violations),
        runtime_ms=round(ms, 3),
        is_exact=exact,
        cost_snapshot_id=inst.cost_snapshot_id,
        seed=seed,
    )


def survey_instance(inst: RoutingInstance, meta: dict, *, seed: int = 42,
                    ortools_time_s: int = 5) -> list[SurveyRow]:
    """Run every applicable classical solver on one instance."""
    D = inst.distance_matrix
    rows: list[SurveyRow] = []

    # Exact ground truth where the instance is small enough.
    if inst.n_nodes <= EXACT_NODE_LIMIT:
        r = brute_force_tsp(D, inst.depot_index, max_nodes=EXACT_NODE_LIMIT)
        rows.append(_row(inst, meta, "brute_force_exact",
                         tour_to_routes(r.tour, inst.depot_index), r.runtime_ms,
                         exact=True, seed=seed))

    nn = nearest_neighbour(D, inst.depot_index)
    rows.append(_row(inst, meta, "nearest_neighbour",
                     tour_to_routes(nn.tour, inst.depot_index), nn.runtime_ms, seed=seed))

    t2 = two_opt(D, nn.tour)
    rows.append(_row(inst, meta, "nearest_neighbour+2opt",
                     tour_to_routes(t2.tour, inst.depot_index),
                     nn.runtime_ms + t2.runtime_ms, seed=seed))

    sa = simulated_annealing(D, inst.depot_index, seed=seed)
    rows.append(_row(inst, meta, "simulated_annealing",
                     tour_to_routes(sa.tour, inst.depot_index), sa.runtime_ms, seed=seed))

    # OR-Tools, in two configurations, because first-solution strategy matters
    # more than metaheuristic choice on instances of this size.
    for fs in ("path_cheapest_arc", "savings"):
        t0 = time.perf_counter()
        try:
            sol = solve_vrp(inst, time_limit_s=ortools_time_s,
                            first_solution=fs, seed=seed)
            ms = (time.perf_counter() - t0) * 1000
            routes = sol.ordered_stops if sol.feasible else []
            rows.append(_row(inst, meta, f"ortools_{fs}", routes, ms, seed=seed))
        except Exception as e:  # a solver failure is a finding, not a crash
            log.warning("ortools(%s) failed on %s: %s", fs, inst.instance_id, e)
    return rows


def run(n_per_group: int = 6, seed: int = 42,
        max_nodes: int = 26) -> pd.DataFrame:
    """Survey a stratified sample across problem types and size bands."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    allinst = list_instances()

    # Cap node count: the exact solver and the QUBO work we build on this are
    # only meaningful at small scale, and a 60-node instance would dominate
    # runtime without informing the hybrid design.
    allinst = allinst[allinst["n_customers"] + 1 <= max_nodes]

    rng = np.random.default_rng(seed)
    chosen: list[str] = []
    for (ptype, band), g in allinst.groupby(["problem_type", "size_band"]):
        take = min(n_per_group, len(g))
        idx = rng.choice(len(g), take, replace=False)
        chosen.extend(g.iloc[idx]["instance_id"].tolist())

    log.info("surveying %d instances across problem families", len(chosen))
    meta_by_id = allinst.set_index("instance_id").to_dict("index")

    rows: list[SurveyRow] = []
    for k, iid in enumerate(chosen, 1):
        inst = load_instance(iid)
        rows.extend(survey_instance(inst, meta_by_id[iid], seed=seed))
        if k % 10 == 0:
            log.info("  %d/%d", k, len(chosen))

    df = pd.DataFrame([asdict(r) for r in rows])
    out = C.RES / "benchmarks" / "classical_survey.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    log.info("wrote %s (%d rows)", out, len(df))
    return df


def best_per_family(df: pd.DataFrame) -> pd.DataFrame:
    """Rank algorithms within each problem type.

    Ranking is on mean *relative* objective against the best feasible result for
    each instance, so a family containing one large instance does not dominate
    the average.
    """
    feas = df[df["feasible"]].copy()
    best = feas.groupby("instance_id")["objective"].min().rename("instance_best")
    feas = feas.join(best, on="instance_id")
    feas["rel_excess"] = (feas["objective"] - feas["instance_best"]) / feas["instance_best"]

    summary = (
        feas.groupby(["problem_type", "algorithm"])
        .agg(n=("instance_id", "nunique"),
             mean_rel_excess=("rel_excess", "mean"),
             wins=("rel_excess", lambda s: int((s < 1e-9).sum())),
             mean_objective=("objective", "mean"),
             mean_runtime_ms=("runtime_ms", "mean"))
        .reset_index()
    )
    # Feasibility rate must come from the full frame, not the feasible subset.
    total = df.groupby(["problem_type", "algorithm"])["feasible"].agg(["size", "mean"])
    total.columns = ["n_attempted", "feasible_rate"]
    summary = summary.merge(total.reset_index(), on=["problem_type", "algorithm"])
    return summary.sort_values(["problem_type", "mean_rel_excess"])


def main() -> None:
    df = run()
    summary = best_per_family(df)
    pd.set_option("display.width", 220)
    print(summary.to_string(index=False))

    winners = {}
    for ptype, g in summary.groupby("problem_type"):
        g = g[g["feasible_rate"] > 0.95]
        if len(g):
            winners[ptype] = g.iloc[0]["algorithm"]
    out = C.RES / "benchmarks" / "classical_survey_summary.json"
    out.write_text(json.dumps(
        {"winners": winners, "summary": summary.to_dict("records")},
        indent=2, default=str), encoding="utf-8")
    print("\nbest classical per family:", json.dumps(winners, indent=2))


if __name__ == "__main__":
    main()
