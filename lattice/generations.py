"""Generation-ladder mass prediction for the fundamental layer.

Two empirical tools, used where each actually works:

- **Koide relation** (charged leptons, precision): Q = Σm / (Σ√m)² = 2/3.
  Given two members, solving Q = 2/3 pins the third — Koide predicted the
  τ mass to four digits in 1981, before measurements converged on it.
- **Log-mass ladder** (quarks, band-level): log₁₀(mass) is roughly linear
  in generation index. Extrapolation misses in MeV (u,c → ~750 GeV for the
  top vs 173 measured) but lands the correct coarse mass band — the lattice
  currency.

Both extrapolate to a hypothetical 4th generation. Honest caveat carried
with those predictions: precision electroweak fits disfavor a sequential
4th SM-like generation.
"""

import math

import numpy as np

from .features import mass_band
from .particles import known_particles


def koide_q(masses: list[float]) -> float:
    total = sum(masses)
    roots = sum(math.sqrt(m) for m in masses)
    return total / roots**2


def koide_predict_third(m1: float, m2: float) -> float:
    """Solve Q = 2/3 for the third mass given two members. The quadratic
    (in √m₃) gives x = 2s + √(6s² − 3(m₁+m₂)) with s = √m₁ + √m₂."""
    s = math.sqrt(m1) + math.sqrt(m2)
    x = 2 * s + math.sqrt(6 * s**2 - 3 * (m1 + m2))
    return x**2


def ladder_fit(masses: list[float]) -> tuple[float, float]:
    """Least-squares fit of log₁₀(mass) vs generation index (0, 1, 2, …).
    Returns (intercept, slope)."""
    gens = np.arange(len(masses))
    slope, intercept = np.polyfit(gens, np.log10(masses), 1)
    return float(intercept), float(slope)


def ladder_predict(fit: tuple[float, float], generation: int) -> float:
    intercept, slope = fit
    return 10 ** (intercept + slope * generation)


def _mass(name: str) -> float:
    p = known_particles().set_index("name")
    return float(p.loc[name, "mass_mev"])


def tau_backtest() -> dict:
    """Remove τ; predict its mass from e and μ via Koide."""
    predicted = koide_predict_third(_mass("electron"), _mass("muon"))
    measured = _mass("tau")
    return {"predicted_mass_mev": predicted,
            "measured_mass_mev": measured,
            "relative_error": (predicted - measured) / measured}


def top_ladder_backtest() -> dict:
    """Remove top; extrapolate the up-type ladder from u and c. Rough in
    MeV, correct at band level."""
    fit = ladder_fit([_mass("up"), _mass("charm")])
    predicted = ladder_predict(fit, 2)
    return {"predicted_mass_mev": predicted,
            "predicted_band": mass_band(predicted),
            "measured_band": mass_band(_mass("top"))}


def gen4_predictions() -> list[dict]:
    """Hypothetical 4th-generation cells: charged lepton via the Koide
    chain (μ, τ), quarks via full-ladder extrapolation."""
    l4 = koide_predict_third(_mass("muon"), _mass("tau"))
    b4 = ladder_predict(ladder_fit(
        [_mass("down"), _mass("strange"), _mass("bottom")]), 3)
    t4 = ladder_predict(ladder_fit(
        [_mass("up"), _mass("charm"), _mass("top")]), 3)

    return [
        {"label": "ℓ₄", "spin": 0.5, "q": -3, "st": 0,
         "mass_mev": l4, "band": mass_band(l4),
         "method": "Koide chain (μ, τ)"},
        {"label": "b′", "spin": 0.5, "q": -1, "st": 0,
         "mass_mev": b4, "band": mass_band(b4),
         "method": "log-mass ladder (d, s, b)"},
        {"label": "t′", "spin": 0.5, "q": 2, "st": 0,
         "mass_mev": t4, "band": mass_band(t4),
         "method": "log-mass ladder (u, c, t)"},
    ]
