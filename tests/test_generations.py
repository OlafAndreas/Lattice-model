"""Tests for generation-ladder mass prediction on the fundamental layer.

Two tools: the Koide relation (precision, charged leptons) and log-mass
ladder extrapolation (band-level, quarks). Anchors are hand-computed."""

import pytest

from lattice.features import mass_band
from lattice.generations import (gen4_predictions, koide_predict_third,
                                 koide_q, ladder_fit, ladder_predict,
                                 tau_backtest, top_ladder_backtest)


def test_koide_relation_holds_for_charged_leptons():
    q = koide_q([0.511, 105.66, 1776.86])
    assert q == pytest.approx(2 / 3, abs=1e-4)


def test_koide_predicts_tau_from_e_and_mu():
    """The 1981 Koide prediction: given e and μ, the relation pins τ."""
    predicted = koide_predict_third(0.511, 105.66)
    assert predicted == pytest.approx(1776.86, rel=1e-3)


def test_tau_backtest():
    result = tau_backtest()
    assert result["predicted_mass_mev"] == pytest.approx(1777.0, rel=1e-3)
    assert result["measured_mass_mev"] == pytest.approx(1776.86, rel=1e-4)
    assert abs(result["relative_error"]) < 1e-3


def test_top_ladder_backtest_recovers_mass_band():
    """Ladder extrapolation from u,c is rough in MeV (~750 GeV vs 173) but
    must land the top quark in the correct coarse mass band."""
    result = top_ladder_backtest()
    assert result["predicted_band"] == mass_band(172_760)
    assert result["predicted_mass_mev"] == pytest.approx(746_600, rel=0.01)


def test_ladder_fit_least_squares():
    fit = ladder_fit([4.67, 93.4, 4180.0])       # down-type ladder
    assert ladder_predict(fit, 3) == pytest.approx(109_344, rel=0.01)


def test_gen4_predictions():
    preds = {p["label"]: p for p in gen4_predictions()}
    assert set(preds) == {"ℓ₄", "b′", "t′"}
    assert preds["ℓ₄"]["mass_mev"] == pytest.approx(43_687, rel=0.01)
    assert preds["ℓ₄"]["method"].startswith("Koide")
    assert preds["b′"]["mass_mev"] == pytest.approx(109_344, rel=0.01)
    assert preds["t′"]["mass_mev"] == pytest.approx(6.23e7, rel=0.02)
    for p in preds.values():
        assert p["spin"] == 0.5 and p["st"] == 0
    assert preds["ℓ₄"]["q"] == -3
    assert preds["b′"]["q"] == -1
    assert preds["t′"]["q"] == 2