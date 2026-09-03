"""Crop ontology for the four target states.

Canonical names are kept strictly separate from the noisy alias pool. Aliases
exist to train the NLU parser and include transliterations, regional names,
common misspellings and ASR-style corruptions; they must never leak into a
canonical field.

``default_bag_weight_kg`` is the *crop-typical* bori weight. It is a default,
not a law: real bag weight varies by packaging and mandi practice, so the unit
converter records which weight it used and how confident it is. See
``vb.units``.
"""

from __future__ import annotations

from dataclasses import dataclass

from vb.enums import Season, Unit


@dataclass(frozen=True)
class Crop:
    key: str
    name_en: str
    name_hi: str
    aliases_en: tuple[str, ...]
    aliases_hi: tuple[str, ...]
    default_unit: Unit
    default_bag_weight_kg: float | None
    handling_class: str
    season: Season
    # Which of the four states this crop is commonly marketed in.
    states: tuple[str, ...]


CROPS: list[Crop] = [
    Crop(
        "wheat", "Wheat", "गेहूँ",
        ("wheat", "gehun", "gehu", "gehoon", "gehun ", "genhu", "wheet", "kanak"),
        ("गेहूँ", "गेहूं", "गेहु", "कनक"),
        Unit.QUINTAL, 50.0, "granular_bagged", Season.RABI, ("DL", "HR", "PB", "UP"),
    ),
    Crop(
        "paddy", "Paddy", "धान",
        ("paddy", "dhan", "dhaan", "rice paddy", "paddi", "dhann"),
        ("धान", "धाण", "चावल धान"),
        Unit.QUINTAL, 40.0, "granular_bagged", Season.KHARIF, ("HR", "PB", "UP"),
    ),
    Crop(
        "mustard", "Mustard", "सरसों",
        ("mustard", "sarso", "sarson", "sarsoo", "sarsau", "rai", "raya"),
        ("सरसों", "सरसो", "राई", "राया"),
        Unit.QUINTAL, 50.0, "oilseed_bagged", Season.RABI, ("HR", "PB", "UP", "DL"),
    ),
    Crop(
        "sugarcane", "Sugarcane", "गन्ना",
        ("sugarcane", "ganna", "gana", "sugar cane", "ikh"),
        ("गन्ना", "गन्ने", "ईख"),
        Unit.TONNE, None, "bulk_loose", Season.PERENNIAL, ("HR", "UP", "PB"),
    ),
    Crop(
        "maize", "Maize", "मक्का",
        ("maize", "makka", "makai", "corn", "makkai", "bhutta"),
        ("मक्का", "मकई", "भुट्टा"),
        Unit.QUINTAL, 50.0, "granular_bagged", Season.KHARIF, ("PB", "UP", "HR"),
    ),
    Crop(
        "bajra", "Pearl Millet", "बाजरा",
        ("bajra", "pearl millet", "bajara", "bajri"),
        ("बाजरा", "बाजरी"),
        Unit.QUINTAL, 50.0, "granular_bagged", Season.KHARIF, ("HR", "UP"),
    ),
    Crop(
        "gram", "Chickpea", "चना",
        ("gram", "chana", "chickpea", "channa", "bengal gram", "chna"),
        ("चना", "चणा", "छोला"),
        Unit.QUINTAL, 50.0, "pulse_bagged", Season.RABI, ("HR", "UP", "PB"),
    ),
    Crop(
        "moong", "Green Gram", "मूंग",
        ("moong", "mung", "green gram", "moong dal", "mong"),
        ("मूंग", "मुंग"),
        Unit.QUINTAL, 50.0, "pulse_bagged", Season.ZAID, ("UP", "HR", "PB"),
    ),
    Crop(
        "cotton", "Cotton", "कपास",
        ("cotton", "kapas", "narma", "kapaas", "cotten"),
        ("कपास", "नरमा"),
        Unit.QUINTAL, 40.0, "fibre_baled", Season.KHARIF, ("PB", "HR"),
    ),
    Crop(
        "potato", "Potato", "आलू",
        ("potato", "aloo", "alu", "aalu", "potatoe"),
        ("आलू", "आलु"),
        Unit.QUINTAL, 50.0, "perishable_bagged", Season.RABI, ("UP", "PB", "HR", "DL"),
    ),
    Crop(
        "onion", "Onion", "प्याज",
        ("onion", "pyaz", "pyaaz", "piyaz", "kanda"),
        ("प्याज", "प्याज़", "पियाज"),
        Unit.QUINTAL, 50.0, "perishable_bagged", Season.RABI, ("UP", "HR", "DL"),
    ),
    Crop(
        "tomato", "Tomato", "टमाटर",
        ("tomato", "tamatar", "tmatar", "tomatoe"),
        ("टमाटर", "टमाटार"),
        Unit.KG, 25.0, "perishable_crate", Season.ZAID, ("UP", "HR", "DL", "PB"),
    ),
    Crop(
        "cauliflower", "Cauliflower", "फूलगोभी",
        ("cauliflower", "gobhi", "phool gobhi", "gobi", "fulgobhi"),
        ("फूलगोभी", "गोभी", "फूल गोभी"),
        Unit.KG, 20.0, "perishable_crate", Season.RABI, ("UP", "HR", "DL"),
    ),
    Crop(
        "barley", "Barley", "जौ",
        ("barley", "jau", "jow", "jav"),
        ("जौ", "जव"),
        Unit.QUINTAL, 50.0, "granular_bagged", Season.RABI, ("HR", "UP", "PB"),
    ),
    Crop(
        "sunflower", "Sunflower", "सूरजमुखी",
        ("sunflower", "surajmukhi", "suraj mukhi", "sunflower seed"),
        ("सूरजमुखी", "सूरजमुखी बीज"),
        Unit.QUINTAL, 40.0, "oilseed_bagged", Season.ZAID, ("PB", "HR"),
    ),
    Crop(
        "guar", "Cluster Bean", "ग्वार",
        ("guar", "gwar", "cluster bean", "guar gum seed"),
        ("ग्वार", "ग्वार फली"),
        Unit.QUINTAL, 50.0, "pulse_bagged", Season.KHARIF, ("HR",),
    ),
    Crop(
        "arhar", "Pigeon Pea", "अरहर",
        ("arhar", "tur", "toor", "pigeon pea", "tuar", "arhar"),
        ("अरहर", "तुअर", "तूर"),
        Unit.QUINTAL, 50.0, "pulse_bagged", Season.KHARIF, ("UP",),
    ),
    Crop(
        "urad", "Black Gram", "उड़द",
        ("urad", "urd", "black gram", "udad", "urad dal"),
        ("उड़द", "उरद"),
        Unit.QUINTAL, 50.0, "pulse_bagged", Season.KHARIF, ("UP", "HR"),
    ),
]

BY_KEY: dict[str, Crop] = {c.key: c for c in CROPS}


def crops_for_state(state_code: str) -> list[Crop]:
    return [c for c in CROPS if state_code in c.states]


def alias_pool(crop: Crop) -> tuple[tuple[str, str], ...]:
    """All (surface_form, script) pairs usable for NLU corpus generation."""
    en = tuple((a, "latin") for a in crop.aliases_en)
    hi = tuple((a, "devanagari") for a in crop.aliases_hi)
    return en + hi
