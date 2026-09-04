"""Curated district reference for the four target states.

PROVENANCE WARNING
------------------
District *names* are real. Centroid coordinates are APPROXIMATE, drawn from
general public geographic knowledge rather than from an authoritative
downloaded boundary file. They are therefore tagged
``geocode_precision = district_centroid`` with a modest confidence score and
``source_id = SRC_CURATED_REF``.

They are fit for: laying out a geographically plausible synthetic network,
coarse containment QA, and relative-distance sanity.
They are NOT fit for: publishing as official coordinates, or any claim of
survey accuracy. the application should replace this module with LGD/Census boundary
polygons and re-derive centroids properly.

NCR membership is an explicit per-district flag, not inferred from state, as
required by the the routing research geography spec. Rajasthan's NCR districts (Alwar,
Bharatpur) are real NCR members but fall outside the four target states and
are intentionally absent.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class District:
    state_code: str
    state: str
    district: str
    lat: float
    lon: float
    in_ncr: bool
    # Rough share of district area under cultivation. Drives farmer-node density.
    agri_intensity: float
    # Rough urbanisation level. Drives shop density and road-quality priors.
    urbanisation: float
    # Approximate radius of the district in km, used as a generation envelope.
    radius_km: float


# --- Delhi (NCT). Every district is in the NCR. -----------------------------
_DELHI = [
    District("DL", "Delhi", "New Delhi", 28.6139, 77.2090, True, 0.02, 0.99, 8),
    District("DL", "Delhi", "Central Delhi", 28.6508, 77.2200, True, 0.02, 0.99, 8),
    District("DL", "Delhi", "North Delhi", 28.7010, 77.2100, True, 0.08, 0.95, 10),
    District("DL", "Delhi", "South Delhi", 28.5245, 77.2066, True, 0.04, 0.98, 12),
    District("DL", "Delhi", "East Delhi", 28.6280, 77.2950, True, 0.03, 0.99, 8),
    District("DL", "Delhi", "West Delhi", 28.6560, 77.1000, True, 0.05, 0.97, 10),
    District("DL", "Delhi", "North West Delhi", 28.7280, 77.0700, True, 0.18, 0.90, 16),
    District("DL", "Delhi", "North East Delhi", 28.6900, 77.2700, True, 0.04, 0.99, 8),
    District("DL", "Delhi", "South West Delhi", 28.5900, 77.0300, True, 0.20, 0.88, 16),
    District("DL", "Delhi", "South East Delhi", 28.5450, 77.2700, True, 0.03, 0.98, 9),
    District("DL", "Delhi", "Shahdara", 28.6700, 77.2900, True, 0.03, 0.99, 7),
]

# --- Haryana. NCR membership varies by district. ----------------------------
_HARYANA = [
    District("HR", "Haryana", "Gurugram", 28.4595, 77.0266, True, 0.22, 0.85, 22),
    District("HR", "Haryana", "Faridabad", 28.4089, 77.3178, True, 0.25, 0.83, 20),
    District("HR", "Haryana", "Sonipat", 28.9931, 77.0151, True, 0.62, 0.42, 26),
    District("HR", "Haryana", "Panipat", 29.3909, 76.9635, True, 0.66, 0.46, 22),
    District("HR", "Haryana", "Rohtak", 28.8955, 76.6066, True, 0.68, 0.44, 24),
    District("HR", "Haryana", "Jhajjar", 28.6060, 76.6570, True, 0.70, 0.28, 25),
    District("HR", "Haryana", "Rewari", 28.1920, 76.6190, True, 0.62, 0.30, 24),
    District("HR", "Haryana", "Palwal", 28.1487, 77.3320, True, 0.72, 0.26, 22),
    District("HR", "Haryana", "Nuh", 28.1030, 77.0010, True, 0.70, 0.14, 24),
    District("HR", "Haryana", "Bhiwani", 28.7930, 76.1390, True, 0.66, 0.22, 32),
    District("HR", "Haryana", "Charkhi Dadri", 28.5920, 76.2710, True, 0.68, 0.18, 20),
    District("HR", "Haryana", "Mahendragarh", 28.2700, 76.1500, True, 0.64, 0.18, 26),
    District("HR", "Haryana", "Jind", 29.3160, 76.3150, True, 0.74, 0.24, 30),
    District("HR", "Haryana", "Karnal", 29.6857, 76.9905, True, 0.76, 0.34, 28),
    District("HR", "Haryana", "Ambala", 30.3752, 76.7821, False, 0.62, 0.44, 22),
    District("HR", "Haryana", "Kurukshetra", 29.9695, 76.8783, False, 0.78, 0.30, 22),
    District("HR", "Haryana", "Kaithal", 29.8015, 76.3995, False, 0.78, 0.22, 26),
    District("HR", "Haryana", "Yamunanagar", 30.1290, 77.2674, False, 0.60, 0.38, 22),
    District("HR", "Haryana", "Hisar", 29.1492, 75.7217, False, 0.72, 0.32, 32),
    District("HR", "Haryana", "Fatehabad", 29.5150, 75.4550, False, 0.76, 0.20, 28),
    District("HR", "Haryana", "Sirsa", 29.5349, 75.0280, False, 0.74, 0.24, 34),
    District("HR", "Haryana", "Panchkula", 30.6942, 76.8606, False, 0.34, 0.56, 18),
]

# --- Punjab. No Punjab district is in the NCR. ------------------------------
_PUNJAB = [
    District("PB", "Punjab", "Ludhiana", 30.9010, 75.8573, False, 0.72, 0.56, 28),
    District("PB", "Punjab", "Amritsar", 31.6340, 74.8723, False, 0.70, 0.53, 28),
    District("PB", "Punjab", "Jalandhar", 31.3260, 75.5762, False, 0.72, 0.52, 26),
    District("PB", "Punjab", "Patiala", 30.3398, 76.3869, False, 0.76, 0.40, 30),
    District("PB", "Punjab", "Bathinda", 30.2110, 74.9455, False, 0.78, 0.36, 30),
    District("PB", "Punjab", "Moga", 30.8158, 75.1717, False, 0.82, 0.26, 24),
    District("PB", "Punjab", "Ferozepur", 30.9250, 74.6130, False, 0.80, 0.24, 30),
    District("PB", "Punjab", "Faridkot", 30.6740, 74.7550, False, 0.80, 0.28, 20),
    District("PB", "Punjab", "Muktsar", 30.4760, 74.5160, False, 0.80, 0.24, 26),
    District("PB", "Punjab", "Sangrur", 30.2458, 75.8421, False, 0.82, 0.28, 30),
    District("PB", "Punjab", "Barnala", 30.3745, 75.5460, False, 0.80, 0.30, 20),
    District("PB", "Punjab", "Mansa", 29.9880, 75.3930, False, 0.82, 0.22, 24),
    District("PB", "Punjab", "Kapurthala", 31.3800, 75.3800, False, 0.76, 0.32, 22),
    District("PB", "Punjab", "Hoshiarpur", 31.5320, 75.9120, False, 0.60, 0.30, 30),
    District("PB", "Punjab", "Gurdaspur", 32.0410, 75.4050, False, 0.68, 0.28, 30),
    District("PB", "Punjab", "Pathankot", 32.2740, 75.6520, False, 0.50, 0.36, 20),
    District("PB", "Punjab", "Tarn Taran", 31.4520, 74.9280, False, 0.80, 0.18, 26),
    District("PB", "Punjab", "Fatehgarh Sahib", 30.6440, 76.3920, False, 0.78, 0.30, 18),
    District("PB", "Punjab", "Rupnagar", 30.9660, 76.5270, False, 0.56, 0.30, 22),
    District("PB", "Punjab", "SAS Nagar", 30.7050, 76.7180, False, 0.44, 0.58, 20),
    District("PB", "Punjab", "Nawanshahr", 31.1250, 76.1170, False, 0.72, 0.26, 20),
    District("PB", "Punjab", "Fazilka", 30.4030, 74.0280, False, 0.78, 0.22, 28),
    District("PB", "Punjab", "Malerkotla", 30.5250, 75.8800, False, 0.78, 0.34, 16),
]

# --- Uttar Pradesh. Eight districts are NCR members. ------------------------
_UP = [
    District("UP", "Uttar Pradesh", "Gautam Buddha Nagar", 28.5355, 77.3910, True, 0.34, 0.78, 22),
    District("UP", "Uttar Pradesh", "Ghaziabad", 28.6692, 77.4538, True, 0.30, 0.82, 18),
    District("UP", "Uttar Pradesh", "Meerut", 28.9845, 77.7064, True, 0.66, 0.48, 26),
    District("UP", "Uttar Pradesh", "Baghpat", 28.9440, 77.2200, True, 0.76, 0.20, 20),
    District("UP", "Uttar Pradesh", "Hapur", 28.7300, 77.7800, True, 0.72, 0.36, 18),
    District("UP", "Uttar Pradesh", "Bulandshahr", 28.4070, 77.8500, True, 0.76, 0.24, 28),
    District("UP", "Uttar Pradesh", "Muzaffarnagar", 29.4727, 77.7085, True, 0.78, 0.28, 26),
    District("UP", "Uttar Pradesh", "Shamli", 29.4500, 77.3100, True, 0.78, 0.24, 20),
    District("UP", "Uttar Pradesh", "Saharanpur", 29.9680, 77.5460, False, 0.70, 0.32, 28),
    District("UP", "Uttar Pradesh", "Bijnor", 29.3730, 78.1360, False, 0.74, 0.22, 30),
    District("UP", "Uttar Pradesh", "Moradabad", 28.8386, 78.7733, False, 0.70, 0.40, 26),
    District("UP", "Uttar Pradesh", "Rampur", 28.8000, 79.0250, False, 0.74, 0.28, 24),
    District("UP", "Uttar Pradesh", "Amroha", 28.9030, 78.4670, False, 0.74, 0.26, 22),
    District("UP", "Uttar Pradesh", "Sambhal", 28.5850, 78.5670, False, 0.76, 0.24, 24),
    District("UP", "Uttar Pradesh", "Aligarh", 27.8974, 78.0880, False, 0.74, 0.36, 28),
    District("UP", "Uttar Pradesh", "Hathras", 27.5950, 78.0520, False, 0.76, 0.26, 20),
    District("UP", "Uttar Pradesh", "Mathura", 27.4924, 77.6737, False, 0.70, 0.32, 26),
    District("UP", "Uttar Pradesh", "Agra", 27.1767, 78.0081, False, 0.66, 0.46, 30),
    District("UP", "Uttar Pradesh", "Firozabad", 27.1591, 78.3957, False, 0.70, 0.38, 22),
    District("UP", "Uttar Pradesh", "Etah", 27.5580, 78.6620, False, 0.76, 0.22, 24),
    District("UP", "Uttar Pradesh", "Mainpuri", 27.2350, 79.0270, False, 0.78, 0.20, 24),
    District("UP", "Uttar Pradesh", "Etawah", 26.7770, 79.0210, False, 0.74, 0.26, 26),
    District("UP", "Uttar Pradesh", "Kanpur Nagar", 26.4499, 80.3319, False, 0.44, 0.66, 26),
    District("UP", "Uttar Pradesh", "Kanpur Dehat", 26.4200, 79.9900, False, 0.78, 0.16, 26),
    District("UP", "Uttar Pradesh", "Unnao", 26.5460, 80.4880, False, 0.76, 0.22, 26),
    District("UP", "Uttar Pradesh", "Lucknow", 26.8467, 80.9462, False, 0.42, 0.66, 26),
    District("UP", "Uttar Pradesh", "Barabanki", 26.9250, 81.1900, False, 0.76, 0.20, 28),
    District("UP", "Uttar Pradesh", "Sitapur", 27.5680, 80.6820, False, 0.78, 0.18, 30),
    District("UP", "Uttar Pradesh", "Hardoi", 27.4160, 80.1310, False, 0.78, 0.18, 30),
    District("UP", "Uttar Pradesh", "Bareilly", 28.3670, 79.4304, False, 0.72, 0.36, 28),
    District("UP", "Uttar Pradesh", "Shahjahanpur", 27.8830, 79.9100, False, 0.76, 0.24, 28),
    District("UP", "Uttar Pradesh", "Pilibhit", 28.6310, 79.8040, False, 0.74, 0.20, 26),
    District("UP", "Uttar Pradesh", "Budaun", 28.0360, 79.1210, False, 0.78, 0.20, 28),
    District("UP", "Uttar Pradesh", "Varanasi", 25.3176, 82.9739, False, 0.52, 0.58, 22),
    District("UP", "Uttar Pradesh", "Prayagraj", 25.4358, 81.8463, False, 0.66, 0.44, 30),
    District("UP", "Uttar Pradesh", "Gorakhpur", 26.7606, 83.3732, False, 0.70, 0.36, 28),
]

DISTRICTS: list[District] = _DELHI + _HARYANA + _PUNJAB + _UP

BY_NAME: dict[str, District] = {d.district: d for d in DISTRICTS}

NCR_DISTRICTS: list[District] = [d for d in DISTRICTS if d.in_ncr]

STATE_NAMES = {"DL": "Delhi", "HR": "Haryana", "PB": "Punjab", "UP": "Uttar Pradesh"}


def for_states(state_codes: tuple[str, ...]) -> list[District]:
    return [d for d in DISTRICTS if d.state_code in state_codes]


def is_ncr(district_name: str) -> bool:
    """Explicit NCR lookup. Never infer NCR membership from the state."""
    d = BY_NAME.get(district_name)
    return bool(d and d.in_ncr)
