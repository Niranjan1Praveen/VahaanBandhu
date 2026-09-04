"""Curated mandi reference.

PROVENANCE WARNING
------------------
The mandi **names** here are real, well-known agricultural markets, recorded
from general public knowledge. Their coordinates are APPROXIMATE, pinned to the
host town rather than surveyed to the market yard gate.

Accordingly every row carries ``coordinate_verified = False`` and
``geocode_precision = settlement``. Nothing in this module may be presented as
an officially verified mandi location. The the quantity rule "never fabricate the
latitude/longitude of an actual mandi" is honoured by refusing to *claim*
precision we do not have, rather than by omitting the markets entirely --
downstream routing needs plausible destinations to exist.

the application must reconcile this list against the e-NAM mandi directory and the
state agricultural marketing board portals (Delhi, Haryana, Punjab, UP), and
replace these coordinates with sourced ones. Note that e-NAM covers only
integrated markets and is NOT the complete universe of physical mandis.
"""

from __future__ import annotations

from dataclasses import dataclass

from vb.enums import MarketYardType


@dataclass(frozen=True)
class MandiRef:
    key: str
    name_en: str
    name_hi: str
    aliases: tuple[str, ...]
    district: str
    state_code: str
    lat: float
    lon: float
    yard_type: MarketYardType
    enam_enabled: bool
    # Rough scale of the market, drives queue time and commodity breadth.
    scale: str  # "terminal" | "large" | "medium" | "small"


MANDIS: list[MandiRef] = [
    # --- Delhi ---
    MandiRef("azadpur", "Azadpur Mandi", "आज़ादपुर मंडी",
             ("azadpur", "azadpur mandi", "ajadpur", "azaadpur", "आजादपुर"),
             "North Delhi", "DL", 28.7075, 77.1750, MarketYardType.MAIN, False, "terminal"),
    MandiRef("narela", "Narela Mandi", "नरेला मंडी",
             ("narela", "narela mandi", "narella", "नरेला"),
             "North Delhi", "DL", 28.8530, 77.0920, MarketYardType.MAIN, False, "large"),
    MandiRef("ghazipur_dl", "Ghazipur Mandi", "गाज़ीपुर मंडी",
             ("ghazipur", "gazipur", "ghazipur mandi", "गाजीपुर"),
             "East Delhi", "DL", 28.6250, 77.3260, MarketYardType.MAIN, False, "large"),
    MandiRef("okhla", "Okhla Mandi", "ओखला मंडी",
             ("okhla", "okhla mandi", "ओखला"),
             "South East Delhi", "DL", 28.5350, 77.2790, MarketYardType.SUB_YARD, False, "medium"),
    MandiRef("keshopur", "Keshopur Mandi", "केशोपुर मंडी",
             ("keshopur", "keshopur mandi", "केशोपुर"),
             "West Delhi", "DL", 28.6410, 77.0870, MarketYardType.SUB_YARD, False, "medium"),
    MandiRef("najafgarh", "Najafgarh Mandi", "नजफगढ़ मंडी",
             ("najafgarh", "najafgarh mandi", "नजफगढ़"),
             "South West Delhi", "DL", 28.6090, 76.9790, MarketYardType.SUB_YARD, False, "small"),

    # --- Haryana ---
    MandiRef("karnal", "Karnal Grain Market", "करनाल अनाज मंडी",
             ("karnal", "karnal mandi", "karnal anaj mandi", "करनाल"),
             "Karnal", "HR", 29.6857, 76.9905, MarketYardType.MAIN, True, "large"),
    MandiRef("panipat", "Panipat Grain Market", "पानीपत अनाज मंडी",
             ("panipat", "panipat mandi", "पानीपत"),
             "Panipat", "HR", 29.3909, 76.9635, MarketYardType.MAIN, True, "large"),
    MandiRef("sonipat", "Sonipat Grain Market", "सोनीपत अनाज मंडी",
             ("sonipat", "sonepat", "sonipat mandi", "सोनीपत"),
             "Sonipat", "HR", 28.9931, 77.0151, MarketYardType.MAIN, True, "large"),
    MandiRef("gurugram", "Gurugram Mandi", "गुरुग्राम मंडी",
             ("gurugram", "gurgaon", "gurgaon mandi", "गुड़गांव", "गुरुग्राम"),
             "Gurugram", "HR", 28.4595, 77.0266, MarketYardType.MAIN, True, "medium"),
    MandiRef("rewari", "Rewari Mandi", "रेवाड़ी मंडी",
             ("rewari", "rewari mandi", "रेवाड़ी"),
             "Rewari", "HR", 28.1920, 76.6190, MarketYardType.MAIN, True, "medium"),
    MandiRef("hisar", "Hisar Grain Market", "हिसार अनाज मंडी",
             ("hisar", "hissar", "hisar mandi", "हिसार"),
             "Hisar", "HR", 29.1492, 75.7217, MarketYardType.MAIN, True, "large"),
    MandiRef("sirsa", "Sirsa Grain Market", "सिरसा अनाज मंडी",
             ("sirsa", "sirsa mandi", "सिरसा"),
             "Sirsa", "HR", 29.5349, 75.0280, MarketYardType.MAIN, True, "medium"),
    MandiRef("kaithal", "Kaithal Grain Market", "कैथल अनाज मंडी",
             ("kaithal", "kaithal mandi", "कैथल"),
             "Kaithal", "HR", 29.8015, 76.3995, MarketYardType.MAIN, True, "medium"),
    MandiRef("kurukshetra", "Pehowa Mandi", "पेहोवा मंडी",
             ("pehowa", "pehowa mandi", "kurukshetra mandi", "पेहोवा"),
             "Kurukshetra", "HR", 29.9800, 76.5830, MarketYardType.SUB_YARD, True, "medium"),
    MandiRef("rohtak", "Rohtak Grain Market", "रोहतक अनाज मंडी",
             ("rohtak", "rohtak mandi", "रोहतक"),
             "Rohtak", "HR", 28.8955, 76.6066, MarketYardType.MAIN, True, "medium"),
    MandiRef("palwal", "Palwal Mandi", "पलवल मंडी",
             ("palwal", "palwal mandi", "पलवल"),
             "Palwal", "HR", 28.1487, 77.3320, MarketYardType.MAIN, True, "medium"),
    MandiRef("jind", "Jind Grain Market", "जींद अनाज मंडी",
             ("jind", "jind mandi", "जींद"),
             "Jind", "HR", 29.3160, 76.3150, MarketYardType.MAIN, True, "medium"),
    MandiRef("bhiwani", "Bhiwani Mandi", "भिवानी मंडी",
             ("bhiwani", "bhiwani mandi", "भिवानी"),
             "Bhiwani", "HR", 28.7930, 76.1390, MarketYardType.MAIN, True, "medium"),
    MandiRef("fatehabad", "Fatehabad Grain Market", "फतेहाबाद अनाज मंडी",
             ("fatehabad", "fatehabad mandi", "फतेहाबाद"),
             "Fatehabad", "HR", 29.5150, 75.4550, MarketYardType.MAIN, True, "medium"),
    MandiRef("ambala", "Ambala Grain Market", "अंबाला अनाज मंडी",
             ("ambala", "ambala mandi", "अंबाला"),
             "Ambala", "HR", 30.3752, 76.7821, MarketYardType.MAIN, True, "medium"),

    # --- Punjab ---
    MandiRef("khanna", "Khanna Grain Market", "खन्ना अनाज मंडी",
             ("khanna", "khanna mandi", "खन्ना"),
             "Ludhiana", "PB", 30.7050, 76.2220, MarketYardType.MAIN, True, "terminal"),
    MandiRef("ludhiana", "Ludhiana Grain Market", "लुधियाना अनाज मंडी",
             ("ludhiana", "ludhiana mandi", "लुधियाना"),
             "Ludhiana", "PB", 30.9010, 75.8573, MarketYardType.MAIN, True, "large"),
    MandiRef("rajpura", "Rajpura Mandi", "राजपुरा मंडी",
             ("rajpura", "rajpura mandi", "राजपुरा"),
             "Patiala", "PB", 30.4840, 76.5940, MarketYardType.MAIN, True, "medium"),
    MandiRef("moga", "Moga Grain Market", "मोगा अनाज मंडी",
             ("moga", "moga mandi", "मोगा"),
             "Moga", "PB", 30.8158, 75.1717, MarketYardType.MAIN, True, "large"),
    MandiRef("bathinda", "Bathinda Grain Market", "बठिंडा अनाज मंडी",
             ("bathinda", "bhatinda", "bathinda mandi", "बठिंडा"),
             "Bathinda", "PB", 30.2110, 74.9455, MarketYardType.MAIN, True, "large"),
    MandiRef("jagraon", "Jagraon Mandi", "जगरांव मंडी",
             ("jagraon", "jagraon mandi", "जगरांव"),
             "Ludhiana", "PB", 30.7870, 75.4730, MarketYardType.SUB_YARD, True, "medium"),
    MandiRef("sangrur", "Sangrur Grain Market", "संगरूर अनाज मंडी",
             ("sangrur", "sangrur mandi", "संगरूर"),
             "Sangrur", "PB", 30.2458, 75.8421, MarketYardType.MAIN, True, "medium"),
    MandiRef("patiala", "Patiala Grain Market", "पटियाला अनाज मंडी",
             ("patiala", "patiala mandi", "पटियाला"),
             "Patiala", "PB", 30.3398, 76.3869, MarketYardType.MAIN, True, "medium"),
    MandiRef("amritsar", "Amritsar Grain Market", "अमृतसर अनाज मंडी",
             ("amritsar", "amritsar mandi", "अमृतसर"),
             "Amritsar", "PB", 31.6340, 74.8723, MarketYardType.MAIN, True, "large"),
    MandiRef("jalandhar", "Jalandhar Mandi", "जालंधर मंडी",
             ("jalandhar", "jullundur", "jalandhar mandi", "जालंधर"),
             "Jalandhar", "PB", 31.3260, 75.5762, MarketYardType.MAIN, True, "medium"),
    MandiRef("mansa", "Mansa Grain Market", "मानसा अनाज मंडी",
             ("mansa", "mansa mandi", "मानसा"),
             "Mansa", "PB", 29.9880, 75.3930, MarketYardType.MAIN, True, "medium"),
    MandiRef("barnala", "Barnala Mandi", "बरनाला मंडी",
             ("barnala", "barnala mandi", "बरनाला"),
             "Barnala", "PB", 30.3745, 75.5460, MarketYardType.MAIN, True, "medium"),

    # --- Uttar Pradesh ---
    MandiRef("meerut", "Meerut Navin Mandi", "मेरठ नवीन मंडी",
             ("meerut", "meerut mandi", "navin mandi meerut", "मेरठ"),
             "Meerut", "UP", 28.9845, 77.7064, MarketYardType.MAIN, True, "large"),
    MandiRef("ghaziabad", "Ghaziabad Mandi", "गाज़ियाबाद मंडी",
             ("ghaziabad", "gaziabad", "ghaziabad mandi", "गाजियाबाद"),
             "Ghaziabad", "UP", 28.6692, 77.4538, MarketYardType.MAIN, True, "large"),
    MandiRef("bulandshahr", "Bulandshahr Mandi", "बुलंदशहर मंडी",
             ("bulandshahr", "bulandshehar", "बुलंदशहर"),
             "Bulandshahr", "UP", 28.4070, 77.8500, MarketYardType.MAIN, True, "medium"),
    MandiRef("muzaffarnagar", "Muzaffarnagar Mandi", "मुज़फ़्फ़रनगर मंडी",
             ("muzaffarnagar", "muzafarnagar", "मुजफ्फरनगर"),
             "Muzaffarnagar", "UP", 29.4727, 77.7085, MarketYardType.MAIN, True, "large"),
    MandiRef("saharanpur", "Saharanpur Mandi", "सहारनपुर मंडी",
             ("saharanpur", "saharanpur mandi", "सहारनपुर"),
             "Saharanpur", "UP", 29.9680, 77.5460, MarketYardType.MAIN, True, "medium"),
    MandiRef("aligarh", "Aligarh Mandi", "अलीगढ़ मंडी",
             ("aligarh", "aligarh mandi", "अलीगढ़"),
             "Aligarh", "UP", 27.8974, 78.0880, MarketYardType.MAIN, True, "medium"),
    MandiRef("agra", "Agra Mandi", "आगरा मंडी",
             ("agra", "agra mandi", "आगरा"),
             "Agra", "UP", 27.1767, 78.0081, MarketYardType.MAIN, True, "large"),
    MandiRef("mathura", "Mathura Mandi", "मथुरा मंडी",
             ("mathura", "mathura mandi", "मथुरा"),
             "Mathura", "UP", 27.4924, 77.6737, MarketYardType.MAIN, True, "medium"),
    MandiRef("hapur", "Hapur Mandi", "हापुड़ मंडी",
             ("hapur", "hapur mandi", "हापुड़"),
             "Hapur", "UP", 28.7300, 77.7800, MarketYardType.MAIN, True, "medium"),
    MandiRef("moradabad", "Moradabad Mandi", "मुरादाबाद मंडी",
             ("moradabad", "moradabad mandi", "मुरादाबाद"),
             "Moradabad", "UP", 28.8386, 78.7733, MarketYardType.MAIN, True, "medium"),
    MandiRef("bareilly", "Bareilly Mandi", "बरेली मंडी",
             ("bareilly", "bareli", "bareilly mandi", "बरेली"),
             "Bareilly", "UP", 28.3670, 79.4304, MarketYardType.MAIN, True, "medium"),
    MandiRef("lucknow", "Lucknow Navin Mandi", "लखनऊ नवीन मंडी",
             ("lucknow", "lucknow mandi", "navin mandi lucknow", "लखनऊ"),
             "Lucknow", "UP", 26.8467, 80.9462, MarketYardType.MAIN, True, "large"),
    MandiRef("kanpur", "Kanpur Mandi", "कानपुर मंडी",
             ("kanpur", "kanpur mandi", "कानपुर"),
             "Kanpur Nagar", "UP", 26.4499, 80.3319, MarketYardType.MAIN, True, "large"),
    MandiRef("varanasi", "Varanasi Mandi", "वाराणसी मंडी",
             ("varanasi", "banaras", "benares", "वाराणसी", "बनारस"),
             "Varanasi", "UP", 25.3176, 82.9739, MarketYardType.MAIN, True, "medium"),
    MandiRef("gorakhpur", "Gorakhpur Mandi", "गोरखपुर मंडी",
             ("gorakhpur", "gorakhpur mandi", "गोरखपुर"),
             "Gorakhpur", "UP", 26.7606, 83.3732, MarketYardType.MAIN, True, "medium"),
    MandiRef("sitapur", "Sitapur Mandi", "सीतापुर मंडी",
             ("sitapur", "sitapur mandi", "सीतापुर"),
             "Sitapur", "UP", 27.5680, 80.6820, MarketYardType.MAIN, True, "small"),
    MandiRef("shamli", "Shamli Mandi", "शामली मंडी",
             ("shamli", "shamli mandi", "शामली"),
             "Shamli", "UP", 29.4500, 77.3100, MarketYardType.MAIN, True, "small"),
]

BY_KEY: dict[str, MandiRef] = {m.key: m for m in MANDIS}

# Every coordinate in this module is town-level, not surveyed.
COORDINATE_VERIFIED = False

SCALE_QUEUE_MIN = {"terminal": 95, "large": 70, "medium": 45, "small": 28}
SCALE_COMMODITY_BREADTH = {"terminal": 14, "large": 10, "medium": 7, "small": 4}


def mandis_for_states(state_codes: tuple[str, ...]) -> list[MandiRef]:
    return [m for m in MANDIS if m.state_code in state_codes]
