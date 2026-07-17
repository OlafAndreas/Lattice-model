"""Known fundamental particles with model-independent observables.

Hand-built from PDG 2024 values; MODEL_DESIGN.md §13 plans to replace this
with the PDG SQLite download. Antiparticles are folded into one entry per
species (W stands for W±). Coarse conventions follow MODEL_DESIGN.md:

- charge_thirds: electric charge in units of e/3.
- strong/em/weak: coarse interaction-signature flags. The Higgs carries no
  flags in this encoding (neutral scalar, no gauge charge) — see §11.
- stable: 1 for stable or effectively stable states. Up/down are marked
  stable as constituents of stable matter (§7 "structural" role).
- Neutrino masses are a representative sub-eV scale, not measured values.
- discovered: commonly cited experimental discovery year, used by the
  temporal backtest (§10.2).
"""

import pandas as pd

_PARTICLES = [
    # name       mass_mev   spin charge_thirds strong em weak stable discovered
    ("up",           2.16,   0.5,  2, 1, 1, 1, 1, 1968),
    ("down",         4.67,   0.5, -1, 1, 1, 1, 1, 1968),
    ("charm",     1270.0,    0.5,  2, 1, 1, 1, 0, 1974),
    ("strange",     93.4,    0.5, -1, 1, 1, 1, 0, 1947),
    ("top",     172760.0,    0.5,  2, 1, 1, 1, 0, 1995),
    ("bottom",    4180.0,    0.5, -1, 1, 1, 1, 0, 1977),
    ("electron",     0.511,  0.5, -3, 0, 1, 1, 1, 1897),
    ("muon",       105.66,   0.5, -3, 0, 1, 1, 0, 1936),
    ("tau",       1776.86,   0.5, -3, 0, 1, 1, 0, 1975),
    ("nu_e",         1e-7,   0.5,  0, 0, 0, 1, 1, 1956),
    ("nu_mu",        1e-7,   0.5,  0, 0, 0, 1, 1, 1962),
    ("nu_tau",       1e-7,   0.5,  0, 0, 0, 1, 1, 2000),
    ("photon",       0.0,    1.0,  0, 0, 1, 0, 1, 1905),
    ("gluon",        0.0,    1.0,  0, 1, 0, 0, 1, 1979),
    ("W",        80377.0,    1.0,  3, 0, 1, 1, 0, 1983),
    ("Z",        91187.6,    1.0,  0, 0, 0, 1, 0, 1983),
    ("higgs",   125250.0,    0.0,  0, 0, 0, 0, 0, 2012),
]

_COLUMNS = ["name", "mass_mev", "spin", "charge_thirds",
            "strong", "em", "weak", "stable", "discovered"]


def known_particles() -> pd.DataFrame:
    return pd.DataFrame(_PARTICLES, columns=_COLUMNS)
