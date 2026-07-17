"""Gell-Mann–Okubo style mass estimation.

Within a multiplet panel (fixed baryon number, spin, charm, beauty), hadron
mass is approximately linear in strangeness — the equal-spacing rule that
predicted the Ω⁻ mass (~1680 MeV predicted, 1672 measured) before its 1964
discovery. Fitting that line over a panel's known members gives every empty
cell a predicted mass, the way Mendeleev's gaps carried predicted properties.
"""

from typing import Optional

import numpy as np
import pandas as pd


def fit_mass_vs_strangeness(members: pd.DataFrame) -> Optional[tuple[float, float]]:
    """Least-squares fit mass_mev = intercept + slope·S over a panel's known
    members. Returns (intercept, slope), or None if the panel spans fewer
    than two strangeness values (no slope determinable)."""
    if members["strangeness"].nunique() < 2:
        return None
    slope, intercept = np.polyfit(members["strangeness"], members["mass_mev"], 1)
    return float(intercept), float(slope)


def predict_mass(fit: tuple[float, float], strangeness: int) -> float:
    intercept, slope = fit
    return intercept + slope * strangeness
