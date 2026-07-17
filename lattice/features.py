"""OptionSet feature encoders (MODEL_DESIGN.md §2).

v1: spin parity + charge + interaction flags + mass band + stability.
v2: emergent-only — exact spin, charge, mass band, stability. No force flags.
"""

import math

import pandas as pd

V1_FEATURES = ["spin_half", "charge_1_3", "has_charge",
               "Strong", "EM", "Weak", "logMass", "stable_band"]
V2_FEATURES = ["spin", "charge_1_3", "has_charge", "logMass", "stable_band"]

MASSLESS_BAND = -9


def mass_band(mass_mev: float) -> int:
    """Coarse log10(mass/MeV) band; massless states get the -9 sentinel."""
    if mass_mev <= 0:
        return MASSLESS_BAND
    return math.floor(math.log10(mass_mev))


def propagation_fraction(log_mass_band: int) -> float:
    """1.0 for effectively massless states (propagate at c), else 0.0 (§2)."""
    return 1.0 if log_mass_band <= -8.5 else 0.0


def encode_v1(particles: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "name": particles["name"],
        "spin_half": (particles["spin"] % 1 != 0).astype(int),
        "charge_1_3": particles["charge_thirds"].astype(int),
        "has_charge": (particles["charge_thirds"] != 0).astype(int),
        "Strong": particles["strong"].astype(int),
        "EM": particles["em"].astype(int),
        "Weak": particles["weak"].astype(int),
        "logMass": particles["mass_mev"].map(mass_band),
        "stable_band": particles["stable"].astype(int),
    })
    return out


def encode_v2(particles: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "name": particles["name"],
        "spin": particles["spin"].astype(float),
        "charge_1_3": particles["charge_thirds"].astype(int),
        "has_charge": (particles["charge_thirds"] != 0).astype(int),
        "logMass": particles["mass_mev"].map(mass_band),
        "stable_band": particles["stable"].astype(int),
    })
    return out


def encode_hadrons(hadrons: pd.DataFrame) -> pd.DataFrame:
    """Hadron-layer OptionSet: emergent observables plus the conserved
    flavor quantum numbers (baryon number, S, C, B~)."""
    out = pd.DataFrame({
        "name": hadrons["name"],
        "spin": hadrons["spin"].astype(float),
        "charge_1_3": hadrons["charge_thirds"].astype(int),
        "logMass": hadrons["mass_mev"].map(mass_band),
        "stable_band": hadrons["stable"].astype(int),
        "baryon": hadrons["baryon"].astype(int),
        "strangeness": hadrons["strangeness"].astype(int),
        "charm": hadrons["charm"].astype(int),
        "beauty": hadrons["beauty"].astype(int),
    })
    return out
