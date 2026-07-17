"""Grid enumeration of all OptionSet combinations (MODEL_DESIGN.md §3 step 4).

Grid bounds are explicit parameters of the rebuild; the original session's
bounds are unknown, so absolute slot counts differ from the §6 claims.
"""

import itertools

import pandas as pd

from .features import MASSLESS_BAND, V1_FEATURES, V2_FEATURES

CHARGE_THIRDS = range(-6, 7)                     # covers exotic ±4/3, ±5/3
MASS_BANDS = [MASSLESS_BAND] + list(range(-8, 7))
V2_SPINS = [0.0, 0.5, 1.0, 2.0]


def enumerate_grid_v1() -> pd.DataFrame:
    rows = []
    for spin_half, q, s, e, w, band, stable in itertools.product(
            (0, 1), CHARGE_THIRDS, (0, 1), (0, 1), (0, 1), MASS_BANDS, (0, 1)):
        rows.append((spin_half, q, int(q != 0), s, e, w, band, stable))
    return pd.DataFrame(rows, columns=V1_FEATURES)


def enumerate_grid_v2() -> pd.DataFrame:
    rows = []
    for spin, q, band, stable in itertools.product(
            V2_SPINS, CHARGE_THIRDS, MASS_BANDS, (0, 1)):
        rows.append((spin, q, int(q != 0), band, stable))
    return pd.DataFrame(rows, columns=V2_FEATURES)


HADRON_SPINS = [0.0, 0.5, 1.0, 1.5]
HADRON_MASS_BANDS = [2, 3, 4]        # ~100 MeV to tens of GeV
STRANGENESS = range(-3, 2)           # -3 (Omega) .. +1 (kaons)
CHARM = (0, 1, 2, 3)                 # up to triply charmed (Omega_ccc)
BEAUTY = (-3, -2, -1, 0, 1)          # down to triply bottom (Omega_bbb)


def enumerate_grid_hadrons() -> pd.DataFrame:
    from .hadrons import HADRON_FEATURES
    rows = []
    for spin, q, band, stable, b, s, c, bt in itertools.product(
            HADRON_SPINS, CHARGE_THIRDS, HADRON_MASS_BANDS, (0, 1),
            (0, 1), STRANGENESS, CHARM, BEAUTY):
        rows.append((spin, q, band, stable, b, s, c, bt))
    return pd.DataFrame(rows, columns=HADRON_FEATURES)
