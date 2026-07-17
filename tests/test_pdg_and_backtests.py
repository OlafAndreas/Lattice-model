"""Tests for MODEL_DESIGN.md §13 step 2 (PDG data) and §10 steps 1-2
(leave-family-out and temporal backtests)."""

import pytest

from lattice.particles import known_particles
from lattice.pdg_data import pdg_particles
from lattice.pipeline import leave_family_out_backtest, temporal_backtest


# ---------------------------------------------------------- PDG dataset

def test_pdg_particles_same_schema_and_names():
    hand = known_particles()
    pdg = pdg_particles()
    assert list(pdg.columns) == list(hand.columns)
    assert set(pdg["name"]) == set(hand["name"])
    assert len(pdg) == 17


def test_pdg_masses_close_to_handbuilt():
    hand = known_particles().set_index("name")
    pdg = pdg_particles().set_index("name")
    for name in ["top", "higgs", "W", "Z", "electron", "muon", "tau",
                 "charm", "bottom"]:
        assert pdg.loc[name, "mass_mev"] == pytest.approx(
            hand.loc[name, "mass_mev"], rel=0.05), name


def test_pdg_spins_and_charges_match():
    hand = known_particles().set_index("name").sort_index()
    pdg = pdg_particles().set_index("name").sort_index()
    assert (pdg["spin"] == hand["spin"]).all()
    assert (pdg["charge_thirds"] == hand["charge_thirds"]).all()


def test_pdg_massless_states_stay_massless():
    pdg = pdg_particles().set_index("name")
    assert pdg.loc["photon", "mass_mev"] == 0.0
    assert pdg.loc["gluon", "mass_mev"] == 0.0


def test_pipeline_reproduces_on_pdg_data():
    """The 100% LOOCV acceptance claim must hold on real PDG values too."""
    from lattice.pipeline import run_v1
    result = run_v1(pdg_particles())
    assert result["loocv"] == 1.0


# ---------------------------------------------------- family / temporal

def test_leave_family_out_charged_leptons():
    """§10.1: removing ALL charged leptons, their three cells must still
    surface as valid empty slots."""
    recovered = leave_family_out_backtest(["electron", "muon", "tau"])
    assert set(recovered) == {"electron", "muon", "tau"}


def test_leave_family_out_vector_bosons():
    recovered = leave_family_out_backtest(["photon", "gluon", "W", "Z"])
    assert set(recovered) == {"photon", "gluon", "W", "Z"}


def test_temporal_backtest_pre_1995():
    """§10.2: freeze at 1994 → top (1995) and higgs (2012) must be flagged
    as empty-but-allowed slots. nu_tau (2000) shares its coarse OptionSet
    with nu_e/nu_mu, so its cell stays occupied — reported as degenerate,
    not recovered."""
    result = temporal_backtest(1994)
    assert set(result["held_out"]) == {"top", "nu_tau", "higgs"}
    assert set(result["recovered"]) == {"top", "higgs"}
    assert set(result["degenerate"]) == {"nu_tau"}


def test_temporal_backtest_pre_2012():
    result = temporal_backtest(2011)
    assert result["held_out"] == ["higgs"]
    assert result["recovered"] == ["higgs"]
    assert result["degenerate"] == []
