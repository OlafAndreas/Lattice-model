"""Tests for the failed-predictions audit (docs/failed-predictions-audit.md).

The completeness tests double as a gate: they fail while any corpus entry
lacks a verified source citation."""

import pytest

from lattice.audit import (CORPUS, precision_summary, sensitivity_analysis,
                           wilson_interval)


# ------------------------------------------------------------ math

def test_wilson_interval_known_value():
    lo, hi = wilson_interval(7, 10)
    assert lo == pytest.approx(0.3968, abs=0.001)
    assert hi == pytest.approx(0.8922, abs=0.001)


def test_wilson_interval_edge_cases():
    lo, hi = wilson_interval(0, 5)
    assert lo == 0.0 and 0 < hi < 0.6
    lo, hi = wilson_interval(5, 5)
    assert 0.5 < lo < 1.0 and hi == pytest.approx(1.0, abs=1e-9)


# ------------------------------------------------------------ corpus

def test_corpus_entries_are_fully_sourced():
    """Every entry needs verified prediction and outcome/status citations —
    no TODO placeholders may remain."""
    assert len(CORPUS) >= 12
    for e in CORPUS:
        assert e["status"] in ("confirmed", "refuted", "open")
        assert "TODO" not in e["prediction_ref"], e["name"]
        assert e["prediction_ref"], e["name"]
        assert "TODO" not in e["outcome_ref"], e["name"]
        assert e["outcome_ref"], e["name"]
        assert e["basis"], e["name"]


def test_corpus_has_both_outcomes():
    statuses = {e["status"] for e in CORPUS}
    assert statuses == {"confirmed", "refuted", "open"}
    assert sum(e["status"] == "refuted" for e in CORPUS) >= 3


# ------------------------------------------------------------ scoring

def test_precision_summary_excludes_open():
    s = precision_summary()
    assert s["n_closed"] == s["n_confirmed"] + s["n_refuted"]
    assert s["n_open"] >= 3
    assert 0 < s["precision"] < 1
    lo, hi = s["wilson_95"]
    assert lo < s["precision"] < hi


def test_sensitivity_analysis_reports_range():
    variants = sensitivity_analysis()
    assert len(variants) >= 2
    precisions = [v["precision"] for v in variants]
    assert min(precisions) < max(precisions)  # grouping choices matter
    for v in variants:
        assert v["description"]


def test_within_vs_beyond_pattern_hypothesis():
    """§6 of the audit design: failures should cluster on *beyond-pattern*
    extrapolations (new rung/multiplet), successes on *within-pattern*
    completions."""
    within = [e for e in CORPUS if e["status"] != "open"
              and e["extrapolation"] == "within"]
    beyond = [e for e in CORPUS if e["status"] != "open"
              and e["extrapolation"] == "beyond"]
    assert within and beyond
    within_rate = sum(e["status"] == "confirmed" for e in within) / len(within)
    beyond_rate = sum(e["status"] == "confirmed" for e in beyond) / len(beyond)
    assert within_rate > beyond_rate