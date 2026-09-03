"""Hindi / English / Hinglish utterance generation for request parsing.

The corpus trains a parser that must turn "गेहूं आजादपुर 20 बोरी" into canonical
IDs. Three design rules matter more than volume:

1. **Labels stay canonical.** Whatever noise goes into the surface form, the
   label is always the crop key, mandi key, numeric value and unit enum. Alias
   strings never appear in a label field.

2. **Every utterance carries its template family.** Splits are made by family,
   not by row, because a paraphrase of a training sentence appearing in test
   would inflate scores without measuring generalisation.

3. **Noise is modelled, not sprinkled.** ASR confusions follow phonetic
   neighbours (स/श, b/v, aa/a) rather than random character flips, because
   that is the error distribution a voice interface actually produces.
"""

from __future__ import annotations

import re

import numpy as np

from vb.enums import InputLanguage, Unit
from vb.reference import crops as cref
from vb.reference import mandis as mref

# --- Number rendering -------------------------------------------------------

HINDI_NUM_WORDS = {
    1: "एक", 2: "दो", 3: "तीन", 4: "चार", 5: "पांच", 6: "छह", 7: "सात",
    8: "आठ", 9: "नौ", 10: "दस", 12: "बारह", 15: "पंद्रह", 20: "बीस",
    25: "पच्चीस", 30: "तीस", 50: "पचास", 100: "सौ",
}
ENGLISH_NUM_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
    8: "eight", 9: "nine", 10: "ten", 12: "twelve", 15: "fifteen", 20: "twenty",
    25: "twenty five", 30: "thirty", 50: "fifty", 100: "hundred",
}
DEVANAGARI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")

UNIT_SURFACE = {
    Unit.KG: {
        "en": ("kg", "kgs", "kilo", "kilos", "kilogram"),
        "hi": ("किलो", "किग्रा", "किलोग्राम"),
    },
    Unit.BORI: {
        "en": ("bori", "bora", "bags", "bag", "sacks"),
        "hi": ("बोरी", "बोरा", "बोरे"),
    },
    Unit.QUINTAL: {
        "en": ("quintal", "quintals", "qtl", "kuntal"),
        "hi": ("क्विंटल", "कुंतल"),
    },
    Unit.TONNE: {
        "en": ("tonne", "tonnes", "ton", "tons", "mt"),
        "hi": ("टन",),
    },
}

# --- Template families ------------------------------------------------------
# Each family is a distinct sentence *shape*. Splitting by family is what stops
# a test sentence from being a trivial rephrase of a training one.

TEMPLATE_FAMILIES: dict[str, dict[str, list[str]]] = {
    "TF_CROP_MANDI_QTY": {
        "en": ["{crop} {mandi} {qty} {unit}", "{crop}, {mandi} mandi, {qty} {unit}"],
        "hi": ["{crop} {mandi} {qty} {unit}", "{crop}, {mandi} मंडी, {qty} {unit}"],
        "hinglish": ["{crop} {mandi} mandi {qty} {unit}", "{crop}, {mandi}, {qty} {unit}"],
    },
    "TF_QTY_CROP_MANDI": {
        "en": ["{qty} {unit} {crop} {mandi}", "{qty} {unit} of {crop} to {mandi}"],
        "hi": ["{qty} {unit} {crop} {mandi}", "{qty} {unit} {crop} {mandi} भेजना है"],
        "hinglish": ["{qty} {unit} {crop} {mandi}", "{qty} {unit} {crop} {mandi} bhejna hai"],
    },
    "TF_MANDI_CROP_QTY": {
        "en": ["{mandi} {crop} {qty} {unit}", "to {mandi}: {crop}, {qty} {unit}"],
        "hi": ["{mandi} {crop} {qty} {unit}", "{mandi} के लिए {crop} {qty} {unit}"],
        "hinglish": ["{mandi} {crop} {qty} {unit}", "{mandi} ke liye {crop} {qty} {unit}"],
    },
    "TF_POLITE_REQUEST": {
        "en": ["I need a truck for {qty} {unit} {crop} to {mandi}",
               "please arrange transport, {qty} {unit} {crop}, {mandi}"],
        "hi": ["मुझे {mandi} के लिए {qty} {unit} {crop} भेजना है",
               "कृपया {qty} {unit} {crop} {mandi} पहुंचाइए"],
        "hinglish": ["mujhe {mandi} ke liye {qty} {unit} {crop} bhejna hai",
                     "bhai {qty} {unit} {crop} {mandi} pahunchana hai"],
    },
    "TF_TRUCK_FIRST": {
        "en": ["truck chahiye, {crop} {qty} {unit}, {mandi}",
               "need vehicle {mandi} {crop} {qty} {unit}"],
        "hi": ["ट्रक चाहिए, {crop} {qty} {unit}, {mandi}",
               "गाड़ी भेजो {mandi} {crop} {qty} {unit}"],
        "hinglish": ["truck chahiye {crop} {qty} {unit} {mandi}",
                     "gaadi bhejo {mandi} {crop} {qty} {unit}"],
    },
    "TF_TERSE": {
        "en": ["{crop} {qty}{unit} {mandi}"],
        "hi": ["{crop} {qty}{unit} {mandi}"],
        "hinglish": ["{crop} {qty}{unit} {mandi}"],
    },
}

# --- ASR-style noise --------------------------------------------------------
# Phonetic neighbours, not random edits: these are the substitutions a speech
# recogniser actually makes on north-Indian agricultural vocabulary.
ASR_SUBSTITUTIONS_LATIN = [
    ("aa", "a"), ("ee", "i"), ("oo", "u"), ("v", "b"), ("b", "v"),
    ("s", "sh"), ("sh", "s"), ("z", "j"), ("j", "z"), ("kh", "k"),
    ("th", "t"), ("ph", "f"), ("gh", "g"),
]
ASR_SUBSTITUTIONS_DEVANAGARI = [
    ("स", "श"), ("श", "स"), ("ज़", "ज"), ("क़", "क"), ("ड़", "ड"),
    ("ँ", "ं"), ("ू", "ु"), ("ी", "ि"),
]


def _corrupt(text: str, rng: np.random.Generator, strength: float = 1.0) -> str:
    """Apply one phonetically plausible ASR-style substitution."""
    devanagari = bool(re.search(r"[ऀ-ॿ]", text))
    table = ASR_SUBSTITUTIONS_DEVANAGARI if devanagari else ASR_SUBSTITUTIONS_LATIN
    candidates = [(a, b) for a, b in table if a in text]
    if not candidates or rng.random() > strength:
        return text
    a, b = candidates[int(rng.integers(0, len(candidates)))]
    return text.replace(a, b, 1)


def _render_qty(value: float, rng: np.random.Generator, lang: str) -> str:
    """Render a number the way a person would say or type it."""
    v = int(value) if float(value).is_integer() else value
    roll = rng.random()
    if isinstance(v, int) and roll < 0.14:
        if lang == "hi" and v in HINDI_NUM_WORDS:
            return HINDI_NUM_WORDS[v]
        if lang in ("en", "hinglish") and v in ENGLISH_NUM_WORDS:
            return ENGLISH_NUM_WORDS[v]
    if lang == "hi" and roll > 0.88:
        return str(v).translate(DEVANAGARI_DIGITS)
    return str(v)


def _pick_surface(options: tuple[str, ...], rng: np.random.Generator) -> str:
    return options[int(rng.integers(0, len(options)))]


def make_utterance(
    rng: np.random.Generator,
    crop: cref.Crop,
    mandi: mref.MandiRef,
    quantity: float,
    unit: Unit,
    language: InputLanguage,
    family: str,
    *,
    is_voice: bool,
    drop_field: str | None = None,
) -> dict:
    """Build one labelled utterance.

    Returns the surface form plus canonical labels and per-slot confidence.
    ``drop_field`` omits a slot entirely, producing the incomplete inputs a real
    parser has to detect and ask about.
    """
    lang = language.value
    script_key = "hi" if lang == "hi" else "en"

    crop_alias = _pick_surface(crop.aliases_hi if lang == "hi" else crop.aliases_en, rng)
    mandi_alias = _pick_surface(mandi.aliases, rng)
    unit_alias = _pick_surface(UNIT_SURFACE[unit][script_key], rng)
    qty_text = _render_qty(quantity, rng, lang)

    # Voice input picks up recognition noise; typed input picks up typos, and
    # less often.
    noise_p = 0.30 if is_voice else 0.12
    conf_crop = conf_mandi = conf_qty = 0.95
    if rng.random() < noise_p:
        crop_alias = _corrupt(crop_alias, rng)
        conf_crop = float(np.round(rng.uniform(0.45, 0.78), 3))
    if rng.random() < noise_p:
        mandi_alias = _corrupt(mandi_alias, rng)
        conf_mandi = float(np.round(rng.uniform(0.45, 0.78), 3))
    if rng.random() < noise_p * 0.4:
        conf_qty = float(np.round(rng.uniform(0.50, 0.82), 3))

    template = _pick_surface(tuple(TEMPLATE_FAMILIES[family][lang]), rng)
    text = template.format(
        crop=crop_alias, mandi=mandi_alias, qty=qty_text, unit=unit_alias,
    )

    if drop_field == "quantity":
        text = text.replace(qty_text, "").replace(unit_alias, "")
        conf_qty = 0.0
    elif drop_field == "mandi":
        text = text.replace(mandi_alias, "")
        conf_mandi = 0.0
    elif drop_field == "crop":
        text = text.replace(crop_alias, "")
        conf_crop = 0.0
    text = re.sub(r"\s{2,}", " ", text).strip(" ,")

    return {
        "raw_utterance": text,
        "input_language": lang,
        "template_family": family,
        # Canonical labels. Never an alias.
        "label_crop_key": crop.key if drop_field != "crop" else None,
        "label_mandi_key": mandi.key if drop_field != "mandi" else None,
        "label_quantity_value": quantity if drop_field != "quantity" else None,
        "label_quantity_unit": unit.value if drop_field != "quantity" else None,
        "parsed_crop_conf": conf_crop,
        "parsed_mandi_conf": conf_mandi,
        "parsed_quantity_conf": conf_qty,
        "is_incomplete": drop_field is not None,
        "missing_field": drop_field,
    }
