"""Tests for the blind second-rater pass (audit protocol §4)."""

import pytest

from lattice.audit import CORPUS, RATER2, inter_rater_stats


def test_rater2_covers_every_corpus_entry():
    assert set(RATER2) == {e["name"] for e in CORPUS}
    for v in RATER2.values():
        assert isinstance(v["in_class"], bool)
        assert v["extrapolation"] in ("within", "beyond")


def test_extrapolation_labels_fully_agree():
    stats = inter_rater_stats()
    assert stats["extrapolation_agreement"] == 1.0
    assert stats["extrapolation_kappa"] == pytest.approx(1.0)


def test_in_class_disagreement_is_reported_not_hidden():
    stats = inter_rater_stats()
    assert stats["in_class_agreement"] == pytest.approx(9 / 16)
    # rater 1 rated everything in-class, so Cohen's kappa is degenerate
    assert stats["in_class_kappa_degenerate"] is True
    assert len(stats["in_class_disagreements"]) == 7


def test_strict_rater_precision():
    """Under rater 2's stricter in-class labels the corpus shrinks to 9
    closed predictions and precision RISES to 8/9."""
    stats = inter_rater_stats()
    assert stats["strict_n_closed"] == 9
    assert stats["strict_precision"] == pytest.approx(8 / 9)
    lo, hi = stats["strict_wilson_95"]
    assert lo < 8 / 9 < hi


def test_within_beyond_significance_is_rater_dependent():
    """Honesty check: the Fisher probability of the within/beyond split is
    ~0.002 under the inclusive labels but only ~0.11 under the strict
    labels (0/1 beyond-pattern failures instead of 0/4) — reported, not
    asserted away."""
    stats = inter_rater_stats()
    assert stats["fisher_inclusive"] == pytest.approx(1 / 495, rel=0.01)
    assert stats["fisher_strict"] == pytest.approx(1 / 9, rel=0.01)