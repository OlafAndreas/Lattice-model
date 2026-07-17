"""Theory / phenomenology sanity filters (MODEL_DESIGN.md §4).

Deliberately coarse; no Standard Model categories. Every known particle's
OptionSet must survive these rules (asserted in tests).
"""

import pandas as pd

from .features import MASSLESS_BAND

CHAMP_MASS_BAND = 4  # stable charged states at ≥ ~10 GeV are excluded


def theory_filter_v1(grid: pd.DataFrame) -> pd.DataFrame:
    g = grid

    massless = g["logMass"] <= MASSLESS_BAND
    charged = g["has_charge"] == 1

    # No massless charged states.
    keep = ~(massless & charged)

    # EM coupling follows from charge (kills weak-only / sterile charged).
    keep &= ~(charged & (g["EM"] == 0))

    # EM without charge only for photon-like states: integer spin, no
    # strong, no weak.
    em_uncharged = (g["EM"] == 1) & ~charged
    photon_like = (g["spin_half"] == 0) & (g["Strong"] == 0) & (g["Weak"] == 0)
    keep &= ~(em_uncharged & ~photon_like)

    # Strong-coupled fermions must be quark-like: charged, EM and weak too.
    strong_fermion = (g["Strong"] == 1) & (g["spin_half"] == 1)
    quark_like = charged & (g["EM"] == 1) & (g["Weak"] == 1)
    keep &= ~(strong_fermion & ~quark_like)

    # No long-lived heavy charged states (CHAMPs).
    keep &= ~(charged & (g["stable_band"] == 1) & (g["logMass"] >= CHAMP_MASS_BAND))

    return g[keep]


def theory_filter_v2(grid: pd.DataFrame) -> pd.DataFrame:
    """Emergent lattice has no force flags; only charge/mass/stability rules
    apply."""
    g = grid
    massless = g["logMass"] <= MASSLESS_BAND
    charged = g["has_charge"] == 1
    keep = ~(massless & charged)
    keep &= ~(charged & (g["stable_band"] == 1) & (g["logMass"] >= CHAMP_MASS_BAND))
    return g[keep]


def hadron_filter(grid: pd.DataFrame) -> pd.DataFrame:
    """Sanity rules for the composite layer. Principled, not SM-derived:

    - spin-statistics: baryons (3 quarks) have half-integer spin, mesons
      (quark+antiquark) integer spin;
    - Gell-Mann–Nishijima window: Q = I3 + (B+S+C+B~)/2 with |I3| ≤ 3/2;
    - flavor content bounded by constituent count (≤2 open flavors for a
      meson, ≤3 flavored quarks in a baryon; baryons follow the particle
      convention: S ≤ 0, C ≥ 0, B~ ≤ 0);
    - confinement: hadrons carry integer electric charge;
    - stability: only the lightest baryon band supports a stable state
      (proton); everything heavier decays.
    """
    g = grid
    baryon = g["baryon"] == 1
    half_spin = g["spin"] % 1 == 0.5

    keep = (baryon & half_spin) | (~baryon & ~half_spin)

    keep &= g["charge_1_3"] % 3 == 0

    hypercharge = (g["baryon"] + g["strangeness"] + g["charm"] + g["beauty"]) / 2
    keep &= (g["charge_1_3"] / 3 - hypercharge).abs() <= 1.5

    flavor_load = g["strangeness"].abs() + g["charm"].abs() + g["beauty"].abs()
    # a meson holds one quark + one antiquark: each open flavor at most ±1
    meson_flavor_ok = ((g["strangeness"].abs() <= 1) & (g["charm"].abs() <= 1)
                       & (g["beauty"].abs() <= 1) & (flavor_load <= 2))
    keep &= ~(~baryon & ~meson_flavor_ok)
    keep &= ~(baryon & ((g["strangeness"] > 0) | (g["beauty"] > 0)
                        | (flavor_load > 3)))

    keep &= ~((g["stable_band"] == 1) & (g["logMass"] > 2))
    return g[keep]
