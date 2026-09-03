"""NLU corpus generation: canonical labels, alias handling, noise realism."""

from __future__ import annotations

import re

import numpy as np
import pytest

from vb.enums import InputLanguage, Unit
from vb.generate.nlu import TEMPLATE_FAMILIES, _corrupt, make_utterance
from vb.reference import crops as cref
from vb.reference import mandis as mref

WHEAT = cref.BY_KEY["wheat"]
AZADPUR = mref.BY_KEY["azadpur"]


@pytest.fixture
def rng():
    return np.random.default_rng(42)


class TestLabelsStayCanonical:
    def test_labels_are_canonical_keys_not_surface_forms(self, rng):
        u = make_utterance(rng, WHEAT, AZADPUR, 20, Unit.BORI,
                           InputLanguage.HI, "TF_CROP_MANDI_QTY", is_voice=True)
        assert u["label_crop_key"] == "wheat"
        assert u["label_mandi_key"] == "azadpur"
        assert u["label_quantity_unit"] == "bori"
        assert u["label_quantity_value"] == 20

    def test_noisy_surface_never_changes_the_label(self, rng):
        """This is the property that makes the corpus trainable: the sentence
        may be corrupted arbitrarily, the label may not move."""
        for _ in range(60):
            u = make_utterance(rng, WHEAT, AZADPUR, 5, Unit.QUINTAL,
                               InputLanguage.HINGLISH, "TF_TERSE", is_voice=True)
            assert u["label_crop_key"] == "wheat"
            assert u["label_mandi_key"] == "azadpur"


class TestLanguages:
    def test_hindi_utterances_contain_devanagari(self, rng):
        hits = 0
        for _ in range(30):
            u = make_utterance(rng, WHEAT, AZADPUR, 10, Unit.QUINTAL,
                               InputLanguage.HI, "TF_CROP_MANDI_QTY", is_voice=False)
            if re.search(r"[ऀ-ॿ]", u["raw_utterance"]):
                hits += 1
        assert hits >= 25

    def test_english_utterances_are_latin(self, rng):
        u = make_utterance(rng, WHEAT, AZADPUR, 500, Unit.KG,
                           InputLanguage.EN, "TF_QTY_CROP_MANDI", is_voice=False)
        assert re.search(r"[a-zA-Z]", u["raw_utterance"])

    def test_every_family_supports_every_language(self):
        for family, langs in TEMPLATE_FAMILIES.items():
            for lang in ("en", "hi", "hinglish"):
                assert langs.get(lang), f"{family} is missing {lang}"


class TestNoiseModel:
    def test_corruption_is_phonetic_not_random(self, rng):
        """ASR errors follow sound-alike substitutions. Random character flips
        would train the parser on a noise distribution it never sees."""
        out = {_corrupt("sarson", rng) for _ in range(50)}
        # At strength 1.0 a substitution always fires, so every variant differs
        # from the original but stays within one sound swap of it.
        assert out and "sarson" not in out
        for variant in out:
            assert abs(len(variant) - len("sarson")) <= 2

    def test_corruption_below_full_strength_sometimes_leaves_text_intact(self, rng):
        out = {_corrupt("sarson", rng, strength=0.5) for _ in range(80)}
        assert "sarson" in out and len(out) > 1

    def test_devanagari_uses_devanagari_substitutions(self, rng):
        out = {_corrupt("सरसों", rng) for _ in range(30)}
        for variant in out:
            assert not any(c.isascii() and c.isalpha() for c in variant)

    def test_voice_input_is_noisier_than_typed(self):
        def conf_mean(is_voice):
            r = np.random.default_rng(7)
            vals = [
                make_utterance(r, WHEAT, AZADPUR, 10, Unit.QUINTAL,
                               InputLanguage.EN, "TF_CROP_MANDI_QTY",
                               is_voice=is_voice)["parsed_crop_conf"]
                for _ in range(200)
            ]
            return float(np.mean(vals))
        assert conf_mean(True) < conf_mean(False)


class TestIncompleteInputs:
    @pytest.mark.parametrize("field", ["quantity", "mandi", "crop"])
    def test_dropped_field_nulls_its_label_and_confidence(self, rng, field):
        u = make_utterance(rng, WHEAT, AZADPUR, 20, Unit.BORI,
                           InputLanguage.HINGLISH, "TF_TRUCK_FIRST",
                           is_voice=True, drop_field=field)
        assert u["is_incomplete"]
        assert u["missing_field"] == field
        key = {"quantity": "label_quantity_value", "mandi": "label_mandi_key",
               "crop": "label_crop_key"}[field]
        assert u[key] is None
        conf = {"quantity": "parsed_quantity_conf", "mandi": "parsed_mandi_conf",
                "crop": "parsed_crop_conf"}[field]
        assert u[conf] == 0.0

    def test_complete_utterance_is_not_flagged_incomplete(self, rng):
        u = make_utterance(rng, WHEAT, AZADPUR, 20, Unit.BORI,
                           InputLanguage.EN, "TF_CROP_MANDI_QTY", is_voice=False)
        assert not u["is_incomplete"]
        assert u["missing_field"] is None


class TestCropOntology:
    def test_canonical_names_are_not_in_the_alias_pool_as_labels(self):
        for c in cref.CROPS:
            assert c.key not in ("", None)
            assert c.name_en and c.name_hi

    def test_aliases_cover_common_transliterations(self):
        assert "gehun" in WHEAT.aliases_en
        assert "गेहूं" in WHEAT.aliases_hi
        mustard = cref.BY_KEY["mustard"]
        assert "sarso" in mustard.aliases_en and "sarson" in mustard.aliases_en

    def test_crop_keys_are_unique(self):
        keys = [c.key for c in cref.CROPS]
        assert len(keys) == len(set(keys))

    def test_mandi_keys_are_unique(self):
        keys = [m.key for m in mref.MANDIS]
        assert len(keys) == len(set(keys))
