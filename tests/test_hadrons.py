"""Tests for the curated hadron layer: dataset integrity vs PDG, flavor
quantum-number sanity, filter consistency, and the historic Ω⁻ backtest."""

import pytest

from lattice.hadrons import known_hadrons, HADRON_FEATURES
from lattice.features import encode_hadrons
from lattice.filters import hadron_filter
from lattice.enumeration import enumerate_grid_hadrons
from lattice.pipeline import run_hadrons, omega_ablation


# ------------------------------------------------------------- dataset

def test_curated_hadron_set():
    df = known_hadrons()
    assert len(df) == 42
    # multiplets complete
    names = set(df["name"])
    assert {"p", "n", "Lambda", "Sigma+", "Sigma0", "Sigma-", "Xi0", "Xi-"} <= names
    assert {"Delta++", "Delta+", "Delta0", "Delta-", "Omega-"} <= names
    assert {"pi+", "pi0", "K+", "K0", "eta", "eta'"} <= names
    assert {"J/psi", "Upsilon", "Lambda_c+", "Lambda_b0"} <= names
    assert "Xi_cc++" in names        # doubly charmed (LHCb 2017)
    # Omega_cc (LHCb, June 2026) is deliberately held OUT as an
    # out-of-sample validation target for the forward predictions
    assert "Omega_cc+" not in names


def test_gell_mann_nishijima_holds_for_all_knowns():
    """|Q − (B+S+C+B~)/2| ≤ 3/2 must hold for every curated hadron."""
    df = known_hadrons()
    q_e = df["charge_thirds"] / 3
    hyper = (df["baryon"] + df["strangeness"] + df["charm"] + df["beauty"]) / 2
    assert ((q_e - hyper).abs() <= 1.5 + 1e-9).all()


def test_baryons_half_integer_mesons_integer_spin():
    df = known_hadrons()
    baryons = df[df["baryon"] == 1]
    mesons = df[df["baryon"] == 0]
    assert (baryons["spin"] % 1 == 0.5).all()
    assert (mesons["spin"] % 1 == 0).all()


def test_pdg_masses_match_for_key_hadrons():
    df = known_hadrons().set_index("name")
    expected = {"p": 938.27, "Omega-": 1672.45, "pi+": 139.57,
                "J/psi": 3096.9, "Lambda_b0": 5619.6}
    for name, mev in expected.items():
        assert df.loc[name, "mass_mev"] == pytest.approx(mev, rel=0.02), name


# ------------------------------------------------------------- lattice

def test_hadron_filter_requires_integer_charge():
    """Confinement: every observed hadron has integer electric charge, so
    fractional-charge cells must not survive the hadron filter."""
    import pandas as pd
    row = pd.DataFrame([{"spin": 0.5, "charge_1_3": 1, "logMass": 3,
                         "stable_band": 0, "baryon": 1, "strangeness": 0,
                         "charm": 0, "beauty": 0}])
    assert len(hadron_filter(row)) == 0
    grid = enumerate_grid_hadrons()
    kept = hadron_filter(grid)
    assert (kept["charge_1_3"] % 3 == 0).all()


def test_all_hadrons_pass_hadron_filter():
    enc = encode_hadrons(known_hadrons())
    kept = hadron_filter(enc[HADRON_FEATURES])
    assert len(kept) == len(enc), "a curated hadron was rejected by filters"


def test_hadron_grid_contains_all_knowns():
    grid = enumerate_grid_hadrons()
    enc = encode_hadrons(known_hadrons())
    merged = enc[HADRON_FEATURES].merge(grid, on=HADRON_FEATURES, how="inner")
    assert len(merged) == len(enc)


def test_run_hadrons_produces_candidates():
    result = run_hadrons()
    assert result["n_filtered"] > 0
    assert (result["candidates"]["novelty"] > 0).all()


# ------------------------------------------------------------- Ω⁻ 1962

def test_omega_ablation_recovers_decuplet_corner():
    """Remove Ω⁻ and the (spin 3/2, Q=−1, S=−3, baryon) cell must surface
    as an empty-but-allowed slot — the 1962 prediction, rerun."""
    hit = omega_ablation()
    assert hit is not None
    assert hit["spin"] == 1.5
    assert hit["charge_1_3"] == -3
    assert hit["strangeness"] == -3
    assert hit["baryon"] == 1
    assert hit["novelty"] > 0
    # its nearest known neighbors are the Ξ* states, one strangeness step up
    assert any(n.startswith("Xi*") for n in hit["nearest_known"][:2])
