"""Tests for the additive constituent-quark mass model and the registered
forward predictions (docs/forward-predictions-2026.md)."""

import pytest

from lattice.constituent import (fit_baryon_model, forward_predictions,
                                 loo_rms, predict_baryon)

OMEGA_CC_MEASURED = 3727.0  # LHCb, announced 2026-06-03 — held OUT of training


def test_baryon_fit_reproduces_knowns():
    model = fit_baryon_model()
    # nucleon: 3 light quarks, spin 1/2
    assert predict_baryon(model, n_s=0, n_c=0, n_b=0, spin=0.5) \
        == pytest.approx(939, abs=80)
    # Omega-: sss, spin 3/2
    assert predict_baryon(model, n_s=3, n_c=0, n_b=0, spin=1.5) \
        == pytest.approx(1672, abs=80)
    # Lambda_b: udb
    assert predict_baryon(model, n_s=0, n_c=0, n_b=1, spin=0.5) \
        == pytest.approx(5620, abs=80)


def test_loo_rms_is_honest_and_small():
    rms, n_evaluable = loo_rms()
    assert rms < 120           # MeV — the model's honest error bar
    assert n_evaluable >= 15   # singleton-feature states excluded (e.g. Λb)


def test_omega_cc_holdout_validation():
    """Ω_cc⁺ (observed June 2026) was deliberately excluded from training:
    the model must predict its mass out-of-sample within ~2× LOO RMS."""
    model = fit_baryon_model()
    pred = predict_baryon(model, n_s=1, n_c=2, n_b=0, spin=0.5)
    assert pred == pytest.approx(OMEGA_CC_MEASURED, abs=150)


def test_forward_predictions_registered_targets():
    preds = {p["name"]: p for p in forward_predictions()}
    assert {"Xi_bb", "Omega_bb", "Xi_bc", "Omega_bc", "Xi_cc+",
            "Omega_ccc", "Omega_bbb", "Omega_cc+ (validation)"} == set(preds)
    # doubly-bottom in the literature ballpark (Karliner-Rosner ~10.16 GeV)
    assert 9_800 < preds["Xi_bb"]["mass_mev"] < 10_600
    assert preds["Omega_bb"]["mass_mev"] > preds["Xi_bb"]["mass_mev"]
    # bottom-charm sits between doubly-charm and doubly-bottom
    assert 3_621 < preds["Xi_bc"]["mass_mev"] < preds["Xi_bb"]["mass_mev"]
    # the discriminating stance: our Xi_cc+ is ~2σ above SELEX's 3519 claim
    assert preds["Xi_cc+"]["mass_mev"] - 3519 > \
        1.9 * preds["Xi_cc+"]["uncertainty_mev"]
    # triply-heavy corners registered cell-level, values as upper bounds
    assert preds["Omega_ccc"]["kind"] == "cell-upper-bound"
    assert preds["Omega_bbb"]["kind"] == "cell-upper-bound"
    assert preds["Omega_ccc"]["spin"] == 1.5
    # registry IDs unique and complete
    ids = [p["id"] for p in preds.values()]
    assert len(ids) == len(set(ids))
    assert sum(i.startswith("LM-2026-0") for i in ids) == 7
    for p in preds.values():
        assert p["uncertainty_mev"] > 0
        assert p["band"] in (3, 4)
        assert p["q_states"], p["name"]


def test_forward_prediction_cells_are_valid_empty_lattice_cells():
    """Every registered cell must be allowed by the hadron filters and
    unoccupied by any known."""
    import pandas as pd
    from lattice.enumeration import enumerate_grid_hadrons
    from lattice.features import encode_hadrons
    from lattice.filters import hadron_filter
    from lattice.hadrons import HADRON_FEATURES, known_hadrons

    grid = hadron_filter(enumerate_grid_hadrons())
    known = encode_hadrons(known_hadrons())[HADRON_FEATURES]
    for p in forward_predictions():
        if "validation" in p["name"]:
            continue
        for q in p["q_states"]:
            cell = pd.DataFrame([{
                "spin": p["spin"], "charge_1_3": q, "logMass": p["band"],
                "stable_band": 0, "baryon": 1,
                "strangeness": p["S"], "charm": p["C"], "beauty": p["Bt"],
            }])[HADRON_FEATURES]
            assert len(grid.merge(cell, on=HADRON_FEATURES)) == 1, \
                f"{p['name']} q={q} not in filtered grid"
            assert len(known.merge(cell, on=HADRON_FEATURES)) == 0, \
                f"{p['name']} q={q} already occupied"