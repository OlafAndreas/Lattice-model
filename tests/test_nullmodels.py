"""Null-model baselines (MODEL_DESIGN.md §10.3): every headline claim must
beat an explicit chance model, not just exist.

Thresholds are conservative bounds motivated by the science (better than
chance at p<1e-8, etc.), not tuned to the observed values."""

import pytest

from lattice.nullmodels import (filter_null_test, loocv_permutation_test,
                                mass_prediction_vs_null,
                                recovery_rank_experiment)


def test_recovery_ranks_beat_uniform_null():
    """Leave-one-out across BOTH layers: the removed particle's cell must
    rank far closer to known structure than a random candidate would."""
    result = recovery_rank_experiment()
    assert result["n"] >= 40                    # enough evaluable ablations
    assert result["n_unrecovered"] == 0         # every cell resurfaces
    assert result["mean_percentile"] < 0.25     # null expectation: 0.5
    assert result["p_value"] < 1e-8


def test_recovery_experiment_reports_per_particle():
    result = recovery_rank_experiment()
    rows = result["results"]
    assert {r["layer"] for r in rows} == {"fundamental", "hadron"}
    by_name = {r["name"]: r["percentile"] for r in rows}
    assert by_name["top"] < 0.05        # pattern-fillers rank near the top
    assert by_name["Omega-"] < 0.10
    assert by_name["photon"] > 0.5     # isolated states rank poorly — honest


def test_loocv_beats_permuted_labels():
    result = loocv_permutation_test(n_permutations=200, seed=42)
    assert result["observed"] == 1.0
    assert result["perm_max"] < 1.0            # no permutation reaches 100%
    assert result["p_value"] <= 1 / 200 + 1e-9


def test_mass_predictions_beat_panel_mean_null():
    rows = mass_prediction_vs_null()
    tools = {r["tool"]: r for r in rows}
    assert set(tools) == {"koide_tau", "gmo_omega", "ladder_top"}
    for r in rows:
        assert abs(r["log_err"]) < abs(r["null_log_err"]), r["tool"]
    assert tools["koide_tau"]["rel_error"] < 1e-3
    assert tools["gmo_omega"]["rel_error"] < 0.02


def test_filters_are_selective_yet_pass_all_knowns():
    result = filter_null_test()
    layers = {r["layer"]: r for r in result["layers"]}
    assert layers["hadron"]["keep_rate"] < 0.05
    assert layers["hadron"]["p_random_filter"] < 1e-50
    assert layers["fundamental"]["p_random_filter"] < 1e-6
    assert "in-sample" in result["caveat"]