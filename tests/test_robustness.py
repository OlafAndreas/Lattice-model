"""Tests for §10.4 (jitter robustness) and §10.5–10.6 (calibration /
pre-registered decision rule). Thresholds are science-driven bounds set
before running the experiments; seeds make results deterministic."""

import pytest

from lattice.robustness import jitter_experiment, operating_curve


# ------------------------------------------------------- §10.4 jitter

def test_jitter_stress_scale_structure_survives():
    """Stress test: ±26% typical mass perturbation (σ=0.1 dex), far beyond
    any measurement error. Structural results (recovery, LOOCV) must
    survive; GMO's *precision* advantage is expected to degrade here —
    extrapolation amplifies input noise — and that is documented, not
    asserted away."""
    result = jitter_experiment(n_trials=20, sigma_dex=0.1, seed=42)
    assert result["n_trials"] == 20
    assert result["loocv_stable_rate"] >= 0.8
    assert result["higgs_recovery_rate"] >= 0.9
    assert result["top_recovery_rate"] >= 0.9
    assert result["omega_recovery_rate"] >= 0.9
    assert result["gmo_median_rel_error"] < 0.30


def test_jitter_measurement_scale_all_results_hold():
    """At generous measurement scale (σ=0.01 dex ≈ 2.3%, still ~100× real
    PDG precision) everything must hold, including GMO beating the null."""
    result = jitter_experiment(n_trials=20, sigma_dex=0.01, seed=42)
    assert result["loocv_stable_rate"] >= 0.95
    assert result["higgs_recovery_rate"] >= 0.95
    assert result["top_recovery_rate"] >= 0.95
    assert result["omega_recovery_rate"] >= 0.95
    assert result["gmo_median_rel_error"] < 0.05
    assert result["gmo_median_rel_error"] < result["null_median_rel_error"]


def test_jitter_is_deterministic_for_fixed_seed():
    a = jitter_experiment(n_trials=5, sigma_dex=0.1, seed=7)
    b = jitter_experiment(n_trials=5, sigma_dex=0.1, seed=7)
    assert a == b


# ---------------------------------------- §10.5–10.6 operating curve

def test_operating_curve_recall_beats_null():
    """Pre-registered rule: 'search the top k% of candidates by proximity'.
    Recall over the 45 ablations must far exceed the null expectation k."""
    curve = operating_curve()
    rows = {r["k"]: r for r in curve["rows"]}
    assert set(rows) == {0.01, 0.05, 0.10, 0.25}
    assert rows[0.10]["recall"] >= 0.5          # null expectation: 0.10
    assert rows[0.10]["enrichment"] >= 5
    assert rows[0.10]["p_value"] < 1e-6
    assert rows[0.01]["enrichment"] >= 5        # top-1% is a strict bar:
    assert rows[0.01]["recall"] >= 0.05         # judge by enrichment
    # monotone by construction
    recalls = [rows[k]["recall"] for k in (0.01, 0.05, 0.10, 0.25)]
    assert recalls == sorted(recalls)


def test_operating_curve_reports_decision_rule():
    curve = operating_curve()
    assert curve["n_ablations"] >= 40
    assert "top 10%" in curve["decision_rule"]
    # expected false-share under the rule: candidates flagged that are not
    # pattern-completions — reported, not hidden
    assert 0 < curve["rows"][2]["expected_null_recall"] <= 0.10 + 1e-9