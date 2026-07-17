"""Tests for Gell-Mann–Okubo style mass prediction: within a multiplet
panel, mass is ~linear in strangeness, so empty cells get a predicted mass
from their neighbors — Mendeleev's eka-element move."""

import pytest

from lattice.gmo import fit_mass_vs_strangeness, predict_mass
from lattice.hadrons import known_hadrons
from lattice.pipeline import omega_ablation
from lattice.viz3d import build_lattice3d_data

OMEGA_MEASURED_MEV = 1672.45


def test_decuplet_fit_equal_spacing():
    h = known_hadrons()
    decuplet = h[(h["multiplet"] == "decuplet") & (h["name"] != "Omega-")]
    fit = fit_mass_vs_strangeness(decuplet)
    assert fit is not None
    _, slope = fit
    assert slope == pytest.approx(-150, abs=15)  # ~150 MeV per unit S


def test_fit_requires_two_strangeness_values():
    h = known_hadrons()
    deltas = h[h["name"].str.startswith("Delta")]  # all S=0
    assert fit_mass_vs_strangeness(deltas) is None


def test_omega_ablation_predicts_mass():
    """The 1962 result: with Ω⁻ removed, the model must predict both the
    cell AND its mass, within 2% of the measured 1672 MeV."""
    hit = omega_ablation()
    assert hit is not None
    assert hit["predicted_mass_mev"] == pytest.approx(
        OMEGA_MEASURED_MEV, rel=0.02)


def test_planes_cells_carry_mass_predictions():
    data = build_lattice3d_data()
    decuplet = next(p for p in data["planes"]
                    if p["baryon"] == 1 and p["spin"] == 1.5
                    and p["charm"] == 0 and p["beauty"] == 0)
    empty_cells = [c for c in decuplet["cells"] if not c["knowns"]]
    assert empty_cells
    assert all("pm" in c for c in empty_cells)
    # panels with no knowns can have no fit, hence no predictions
    unexplored = [p for p in data["planes"]
                  if not any(c["knowns"] for c in p["cells"])]
    for p in unexplored:
        assert all("pm" not in c for c in p["cells"])