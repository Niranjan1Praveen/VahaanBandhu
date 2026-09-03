"""Quantity normalization. The bori cases are the ones that matter."""

from __future__ import annotations

import pytest

from vb.enums import ConversionConfidence, Unit
from vb.units import fits_vehicle, normalize


class TestExactConversions:
    @pytest.mark.parametrize("value,unit,expected", [
        (500, Unit.KG, 500.0),
        (5, Unit.QUINTAL, 500.0),
        (2.5, Unit.TONNE, 2500.0),
        (1, Unit.QUINTAL, 100.0),
    ])
    def test_definitional_units_are_exact(self, value, unit, expected):
        q = normalize(value, unit)
        assert q.kg == pytest.approx(expected)
        assert q.conversion_confidence is ConversionConfidence.EXACT
        assert q.resolved


class TestBoriConversion:
    def test_bori_with_known_crop_uses_that_crops_bag_weight(self):
        q = normalize(20, Unit.BORI, crop_key="wheat")
        assert q.kg == pytest.approx(1000.0)  # 20 x 50 kg
        assert q.bag_weight_kg_used == 50.0
        assert q.conversion_confidence is ConversionConfidence.CROP_DEFAULT

    def test_bag_weight_varies_by_crop(self):
        # Paddy bags are lighter than wheat bags. A global 50 kg assumption
        # would overstate a paddy load by 25%.
        wheat = normalize(10, Unit.BORI, crop_key="wheat")
        paddy = normalize(10, Unit.BORI, crop_key="paddy")
        assert wheat.kg == pytest.approx(500.0)
        assert paddy.kg == pytest.approx(400.0)
        assert wheat.kg != paddy.kg

    def test_bori_without_crop_or_family_is_unresolved(self):
        """The central rule: never invent a kilogram value."""
        q = normalize(20, Unit.BORI)
        assert q.kg is None
        assert not q.resolved
        assert q.conversion_confidence is ConversionConfidence.UNRESOLVED
        assert q.bag_weight_kg_used is None

    def test_bori_falls_back_to_handling_class_with_lower_confidence(self):
        q = normalize(10, Unit.BORI, crop_key=None, handling_class="perishable_crate")
        assert q.kg == pytest.approx(250.0)
        assert q.conversion_confidence is ConversionConfidence.REGIONAL_DEFAULT

    def test_sugarcane_bori_is_unresolved_because_it_has_no_bag_weight(self):
        # Sugarcane moves loose, not bagged. There is no bori weight to use.
        q = normalize(5, Unit.BORI, crop_key="sugarcane")
        assert q.kg is None
        assert q.conversion_confidence is ConversionConfidence.UNRESOLVED


class TestInvalidQuantities:
    @pytest.mark.parametrize("value", [0, -1, -100.5])
    def test_non_positive_quantities_never_resolve(self, value):
        q = normalize(value, Unit.KG)
        assert q.kg is None
        assert q.conversion_source == "invalid_quantity"


class TestCapacityCheck:
    def test_load_within_capacity(self):
        assert fits_vehicle(normalize(500, Unit.KG), 1000) is True

    def test_load_over_capacity(self):
        assert fits_vehicle(normalize(5, Unit.TONNE), 1000) is False

    def test_unresolved_load_returns_none_not_false(self):
        """An unknown load is not a load that fits, and not one that doesn't.
        Collapsing this to a bool would silently dispatch an unsized truck."""
        assert fits_vehicle(normalize(20, Unit.BORI), 1000) is None
