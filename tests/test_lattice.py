"""Acceptance tests for the OptionSet lattice rebuild.

Each test encodes a claim from MODEL_DESIGN.md that the rebuilt pipeline
must reproduce (structurally — exact slot counts from the original ChatGPT
session are not reproducible and are reported, not asserted).
"""

import numpy as np
import pandas as pd
import pytest

from lattice.particles import known_particles
from lattice.features import encode_v1, encode_v2, mass_band, V1_FEATURES, V2_FEATURES
from lattice.model import fit_families, loocv_accuracy, novelty_scores
from lattice.enumeration import enumerate_grid_v1, enumerate_grid_v2
from lattice.filters import theory_filter_v1, theory_filter_v2
from lattice.pipeline import run_v1, ablation_backtest, graviton_cell, score_v02


# ---------------------------------------------------------------- dataset

EXPECTED_NAMES = {
    "up", "down", "charm", "strange", "top", "bottom",
    "electron", "muon", "tau", "nu_e", "nu_mu", "nu_tau",
    "photon", "gluon", "W", "Z", "higgs",
}


def test_known_particles_complete():
    df = known_particles()
    assert set(df["name"]) == EXPECTED_NAMES
    assert len(df) == 17
    for col in ["mass_mev", "spin", "charge_thirds", "strong", "em", "weak", "stable"]:
        assert col in df.columns
        assert df[col].notna().all()


# ---------------------------------------------------------------- features

def test_mass_band():
    assert mass_band(0.0) == -9          # massless sentinel
    assert mass_band(172_760) == 5       # top quark → ~10⁵ MeV band
    assert mass_band(125_250) == 5       # Higgs → ~10⁵ MeV band
    assert mass_band(0.511) == -1        # electron
    assert mass_band(1e-7) == -7         # neutrino-scale


def test_v1_encoding_top_quark():
    v1 = encode_v1(known_particles()).set_index("name")
    top = v1.loc["top"]
    assert top["spin_half"] == 1
    assert top["charge_1_3"] == 2        # Q = +2/3
    assert top["has_charge"] == 1
    assert (top["Strong"], top["EM"], top["Weak"]) == (1, 1, 1)
    assert top["logMass"] == 5
    assert top["stable_band"] == 0


def test_v1_encoding_photon():
    v1 = encode_v1(known_particles()).set_index("name")
    ph = v1.loc["photon"]
    assert ph["spin_half"] == 0
    assert ph["charge_1_3"] == 0 and ph["has_charge"] == 0
    assert (ph["Strong"], ph["EM"], ph["Weak"]) == (0, 1, 0)
    assert ph["logMass"] == -9
    assert ph["stable_band"] == 1


def test_v2_encoding_uses_exact_spin():
    v2 = encode_v2(known_particles()).set_index("name")
    assert v2.loc["photon", "spin"] == 1.0
    assert v2.loc["electron", "spin"] == 0.5
    assert v2.loc["higgs", "spin"] == 0.0
    assert "Strong" not in v2.columns and "EM" not in v2.columns


# ---------------------------------------------------------------- filters

def test_all_knowns_pass_theory_filter():
    v1 = encode_v1(known_particles())
    kept = theory_filter_v1(v1[V1_FEATURES])
    assert len(kept) == len(v1), "a known particle was rejected by the filters"


def _row(**kw):
    base = dict(spin_half=0, charge_1_3=0, has_charge=0,
                Strong=0, EM=0, Weak=0, logMass=0, stable_band=0)
    base.update(kw)
    return pd.DataFrame([base])


def test_filter_rejects_massless_charged():
    row = _row(charge_1_3=3, has_charge=1, EM=1, logMass=-9)
    assert len(theory_filter_v1(row)) == 0


def test_filter_rejects_charged_without_em():
    row = _row(charge_1_3=3, has_charge=1, Weak=1)  # weak-only charged
    assert len(theory_filter_v1(row)) == 0


def test_filter_rejects_strong_fermion_not_quarklike():
    row = _row(spin_half=1, Strong=1, EM=0, Weak=0)  # strong-only fermion
    assert len(theory_filter_v1(row)) == 0


def test_filter_rejects_em_without_charge_unless_photonlike():
    not_photonlike = _row(EM=1, Weak=1)  # neutral EM+weak boson w/o charge
    assert len(theory_filter_v1(not_photonlike)) == 0
    photonlike = _row(EM=1, logMass=-9, stable_band=1)
    assert len(theory_filter_v1(photonlike)) == 1


def test_filter_rejects_heavy_stable_charged_champ():
    champ = _row(spin_half=1, charge_1_3=-3, has_charge=1, EM=1, Weak=1,
                 logMass=5, stable_band=1)
    assert len(theory_filter_v1(champ)) == 0


def test_filter_keeps_gluonlike_strong_only_neutral_boson():
    row = _row(Strong=1, logMass=3)
    assert len(theory_filter_v1(row)) == 1


# ---------------------------------------------------------------- model

def test_loocv_accuracy_is_100_percent():
    """Design §6: 1-NN LOOCV on emergent (k-means) family labels = 100%."""
    v1 = encode_v1(known_particles())
    X = v1[V1_FEATURES]
    families = fit_families(X)
    assert loocv_accuracy(X, families) == 1.0


def test_novelty_positive_for_unseen_zero_for_known():
    v1 = encode_v1(known_particles())
    X = v1[V1_FEATURES]
    unseen = _row(spin_half=1, charge_1_3=2, has_charge=1,
                  Strong=1, EM=1, Weak=1, logMass=6)
    assert novelty_scores(X, unseen[V1_FEATURES])[0] > 0
    assert novelty_scores(X, X.iloc[[0]])[0] == 0


# ---------------------------------------------------------------- pipeline

def test_candidates_exclude_known_optionsets():
    result = run_v1()
    knowns = encode_v1(known_particles())[V1_FEATURES]
    merged = result["candidates"].merge(knowns, on=V1_FEATURES, how="inner")
    assert len(merged) == 0
    assert result["n_raw_unseen"] > 0
    assert result["n_filtered"] > 0
    assert result["n_filtered"] <= result["n_raw_unseen"]


def test_higgs_ablation_recovers_higgs_like_slot():
    """Design §6: with Higgs removed, a neutral scalar, no gauge flags,
    ~10⁵ MeV, short-lived slot must appear among the candidates."""
    hit = ablation_backtest("higgs")
    assert hit is not None
    assert hit["spin_half"] == 0
    assert hit["has_charge"] == 0
    assert (hit["Strong"], hit["EM"], hit["Weak"]) == (0, 0, 0)
    assert hit["logMass"] == 5
    assert hit["stable_band"] == 0
    assert hit["novelty"] > 0


def test_top_ablation_recovers_top_like_slot():
    """Design §6: with top removed, a spin-½, Q=+2/3, strong+EM+weak,
    ~10⁵ MeV slot must appear among the candidates."""
    hit = ablation_backtest("top")
    assert hit is not None
    assert hit["spin_half"] == 1
    assert hit["charge_1_3"] == 2
    assert (hit["Strong"], hit["EM"], hit["Weak"]) == (1, 1, 1)
    assert hit["logMass"] == 5
    assert hit["stable_band"] == 0
    assert hit["novelty"] > 0


def test_top_slot_not_a_candidate_when_top_is_known():
    """The top's cell is occupied — it must NOT appear as a candidate."""
    result = run_v1()
    c = result["candidates"]
    occupied = c[(c["spin_half"] == 1) & (c["charge_1_3"] == 2)
                 & (c["Strong"] == 1) & (c["EM"] == 1) & (c["Weak"] == 1)
                 & (c["logMass"] == 5) & (c["stable_band"] == 0)]
    assert len(occupied) == 0


def test_graviton_cell_unique_and_neighbors_photon_gluon():
    """Design §6: in the v2 exact-spin lattice, (spin=2, Q=0, massless,
    stable) is an unoccupied valid cell; nearest knowns are photon+gluon."""
    cell = graviton_cell()
    assert cell["in_grid"] is True
    assert cell["occupied"] is False
    assert set(cell["nearest_known"][:2]) == {"photon", "gluon"}


def test_score_v02_weights():
    """Design §5: score_v02 = 0.55·novelty + 0.35·measurability + 0.10·prop."""
    s = score_v02(novelty=1.0, measurability=0.0, propagation_fraction=0.0)
    assert s == pytest.approx(0.55)
    s = score_v02(novelty=0.0, measurability=1.0, propagation_fraction=1.0)
    assert s == pytest.approx(0.45)
