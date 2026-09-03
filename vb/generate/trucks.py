"""Truck fleet generation.

Vehicle configurations are drawn from a table of physically coherent classes
rather than by sampling each attribute independently, which would produce
nonsense like a 30-tonne EV pickup. Capacity, body type, fuel and fuel economy
are all constrained by the vehicle class.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from vb.config import GenerationConfig
from vb.enums import BodyType, FuelType, VehicleClass
from vb.ids import content_id
from vb.reference import districts as dref

# class -> (capacity_kg range, kmpl range, max_route_km range, fleet share)
CLASS_PROFILE = {
    VehicleClass.PICKUP: ((700, 1500), (11.0, 15.5), (60, 180), 0.20),
    VehicleClass.LCV: ((1500, 4000), (8.0, 12.0), (100, 300), 0.30),
    VehicleClass.TWO_AXLE: ((6000, 11000), (4.5, 6.5), (150, 450), 0.26),
    VehicleClass.THREE_AXLE: ((12000, 18000), (3.4, 4.8), (200, 700), 0.16),
    VehicleClass.MULTI_AXLE: ((20000, 32000), (2.6, 3.8), (300, 1000), 0.08),
}

# Body types that physically exist for each class.
CLASS_BODIES = {
    VehicleClass.PICKUP: (BodyType.OPEN, BodyType.CLOSED),
    VehicleClass.LCV: (BodyType.OPEN, BodyType.CLOSED, BodyType.REFRIGERATED),
    VehicleClass.TWO_AXLE: (BodyType.OPEN, BodyType.CLOSED, BodyType.TIPPER),
    VehicleClass.THREE_AXLE: (BodyType.OPEN, BodyType.CLOSED, BodyType.TIPPER),
    VehicleClass.MULTI_AXLE: (BodyType.OPEN, BodyType.TIPPER),
}

# EVs and CNG are realistic only at the light end of the fleet today.
CLASS_FUELS = {
    VehicleClass.PICKUP: ((FuelType.DIESEL, FuelType.CNG, FuelType.EV), (0.60, 0.28, 0.12)),
    VehicleClass.LCV: ((FuelType.DIESEL, FuelType.CNG, FuelType.EV), (0.72, 0.24, 0.04)),
    VehicleClass.TWO_AXLE: ((FuelType.DIESEL, FuelType.CNG), (0.93, 0.07)),
    VehicleClass.THREE_AXLE: ((FuelType.DIESEL,), (1.0,)),
    VehicleClass.MULTI_AXLE: ((FuelType.DIESEL,), (1.0,)),
}

# A standard grain bori is ~50 kg; capacity_bori is a driver-facing convenience
# figure derived from that, not an authoritative conversion. See vb.units.
NOMINAL_BORI_KG = 50.0

_DRIVER_EN = ["Ramesh", "Sukhbir", "Jaspal", "Mohan", "Rakesh", "Balwant",
              "Naresh", "Satpal", "Dinesh", "Harpreet", "Vijay", "Kuldeep"]
_DRIVER_HI = ["रमेश", "सुखबीर", "जसपाल", "मोहन", "राकेश", "बलवंत",
              "नरेश", "सतपाल", "दिनेश", "हरप्रीत", "विजय", "कुलदीप"]


def build_trucks(cfg: GenerationConfig, depots: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 53)
    n = cfg.sizes.n_trucks

    classes = list(CLASS_PROFILE)
    share = np.array([CLASS_PROFILE[c][3] for c in classes])
    share = share / share.sum()
    picks = rng.choice(len(classes), size=n, p=share)

    # Home depots weighted toward more urbanised districts, where fleets base.
    dw = np.array([
        0.3 + dref.BY_NAME[d].urbanisation if d in dref.BY_NAME else 0.3
        for d in depots["district"]
    ])
    dw = dw / dw.sum()
    depot_idx = rng.choice(len(depots), size=n, p=dw)

    rows = []
    for i in range(n):
        vc = classes[int(picks[i])]
        (cap_lo, cap_hi), (kmpl_lo, kmpl_hi), (rng_lo, rng_hi), _ = CLASS_PROFILE[vc]
        depot = depots.iloc[int(depot_idx[i])]

        capacity_kg = float(np.round(rng.uniform(cap_lo, cap_hi), -1))
        bodies = CLASS_BODIES[vc]
        body = bodies[int(rng.integers(0, len(bodies)))]
        fuels, fp = CLASS_FUELS[vc]
        fuel = fuels[int(rng.choice(len(fuels), p=np.array(fp) / np.sum(fp)))]

        kmpl = float(np.round(rng.uniform(kmpl_lo, kmpl_hi), 2))
        max_route = float(np.round(rng.uniform(rng_lo, rng_hi), -1))
        if fuel is FuelType.EV:
            # Electric range is materially shorter; kmpl is a diesel-equivalent.
            max_route = min(max_route, 160.0)

        start_h = int(rng.integers(4, 10))
        dur_h = int(rng.integers(8, 15))
        di = int(rng.integers(0, len(_DRIVER_EN)))

        rows.append({
            "truck_id": content_id("truck", depot["location_id"], vc.value, i),
            "home_location_id": depot["location_id"],
            "district": depot["district"],
            "state_code": depot["state_code"],
            "driver_name_en": _DRIVER_EN[di],
            "driver_name_hi": _DRIVER_HI[di],
            "vehicle_class": vc.value,
            "capacity_kg": capacity_kg,
            "capacity_bori": int(capacity_kg // NOMINAL_BORI_KG),
            "body_type": body.value,
            "fuel_type": fuel.value,
            "avg_kmpl": kmpl,
            "max_route_km": max_route,
            "available_from": f"{start_h:02d}:00",
            "available_to": f"{min(start_h + dur_h, 23):02d}:00",
            "is_synthetic": True,
            "generation_method": "class_constrained_v1",
            "seed": cfg.seed,
            "dataset_version": cfg.dataset_version,
        })
    return pd.DataFrame(rows)


def build_truck_availability(cfg: GenerationConfig, trucks: pd.DataFrame) -> pd.DataFrame:
    """Availability slots that drive circular-logistics matching.

    A truck may surface more than once with different remaining capacity, which
    is what lets the matcher find partial return loads.
    """
    rng = np.random.default_rng(cfg.seed + 59)
    rows = []
    for _, t in trucks.iterrows():
        for k in range(int(rng.integers(1, 4))):
            remaining = float(np.round(t["capacity_kg"] * rng.uniform(0.25, 1.0), -1))
            start_h = int(t["available_from"][:2])
            slot_h = min(start_h + int(rng.integers(0, 6)), 22)
            rows.append({
                "availability_id": content_id("availability", t["truck_id"], k),
                "truck_id": t["truck_id"],
                "location_id": t["home_location_id"],
                "available_time": f"{slot_h:02d}:{int(rng.choice([0, 15, 30, 45])):02d}",
                "remaining_capacity_kg": remaining,
                "preferred_radius_km": float(np.round(
                    min(t["max_route_km"] * rng.uniform(0.3, 0.7), 250), -1)),
                "return_home_by": t["available_to"],
                "is_synthetic": True,
                "dataset_version": cfg.dataset_version,
            })
    return pd.DataFrame(rows)
