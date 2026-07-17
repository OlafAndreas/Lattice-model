"""Curated composite particles (hadrons) for seeding the lattice.

41 well-established states chosen for multiplet completeness: the baryon
octet and decuplet, the light pseudoscalar and vector meson nonets, and
heavy-flavor ground states. Masses are PDG 2024 values (MeV); flavor
quantum numbers (baryon number, strangeness S, charm C, beauty B~) are
textbook constants — the PDG package does not expose them.

Antiparticles are folded into one entry per state (pi+ stands for pi±).
Charge-conjugate mesons follow the particle convention (K = S=+1,
D = C=+1, B = B~=+1). Only the proton is marked stable; the free neutron
decays (~880 s) and is encoded unstable.
"""

import pandas as pd

HADRON_FEATURES = ["spin", "charge_1_3", "logMass", "stable_band",
                   "baryon", "strangeness", "charm", "beauty"]

_HADRONS = [
    # name        mcid   mass_mev  spin  q3  B   S   C  B~  st  multiplet
    # --- baryon octet (J=1/2)
    ("p",         2212,   938.27,  0.5,  3,  1,  0,  0,  0,  1, "octet"),
    ("n",         2112,   939.57,  0.5,  0,  1,  0,  0,  0,  0, "octet"),
    ("Lambda",    3122,  1115.68,  0.5,  0,  1, -1,  0,  0,  0, "octet"),
    ("Sigma+",    3222,  1189.37,  0.5,  3,  1, -1,  0,  0,  0, "octet"),
    ("Sigma0",    3212,  1192.64,  0.5,  0,  1, -1,  0,  0,  0, "octet"),
    ("Sigma-",    3112,  1197.45,  0.5, -3,  1, -1,  0,  0,  0, "octet"),
    ("Xi0",       3322,  1314.86,  0.5,  0,  1, -2,  0,  0,  0, "octet"),
    ("Xi-",       3312,  1321.71,  0.5, -3,  1, -2,  0,  0,  0, "octet"),
    # --- baryon decuplet (J=3/2)
    ("Delta++",   2224,  1232.0,   1.5,  6,  1,  0,  0,  0,  0, "decuplet"),
    ("Delta+",    2214,  1232.0,   1.5,  3,  1,  0,  0,  0,  0, "decuplet"),
    ("Delta0",    2114,  1232.0,   1.5,  0,  1,  0,  0,  0,  0, "decuplet"),
    ("Delta-",    1114,  1232.0,   1.5, -3,  1,  0,  0,  0,  0, "decuplet"),
    ("Sigma*+",   3224,  1382.83,  1.5,  3,  1, -1,  0,  0,  0, "decuplet"),
    ("Sigma*0",   3214,  1383.7,   1.5,  0,  1, -1,  0,  0,  0, "decuplet"),
    ("Sigma*-",   3114,  1387.2,   1.5, -3,  1, -1,  0,  0,  0, "decuplet"),
    ("Xi*0",      3324,  1531.80,  1.5,  0,  1, -2,  0,  0,  0, "decuplet"),
    ("Xi*-",      3314,  1535.0,   1.5, -3,  1, -2,  0,  0,  0, "decuplet"),
    ("Omega-",    3334,  1672.45,  1.5, -3,  1, -3,  0,  0,  0, "decuplet"),
    # --- light pseudoscalar nonet (J=0)
    ("pi+",        211,   139.57,  0.0,  3,  0,  0,  0,  0,  0, "pseudoscalar"),
    ("pi0",        111,   134.98,  0.0,  0,  0,  0,  0,  0,  0, "pseudoscalar"),
    ("K+",         321,   493.68,  0.0,  3,  0,  1,  0,  0,  0, "pseudoscalar"),
    ("K0",         311,   497.61,  0.0,  0,  0,  1,  0,  0,  0, "pseudoscalar"),
    ("eta",        221,   547.86,  0.0,  0,  0,  0,  0,  0,  0, "pseudoscalar"),
    ("eta'",       331,   957.78,  0.0,  0,  0,  0,  0,  0,  0, "pseudoscalar"),
    # --- light vector nonet (J=1)
    ("rho+",       213,   775.26,  1.0,  3,  0,  0,  0,  0,  0, "vector"),
    ("rho0",       113,   775.26,  1.0,  0,  0,  0,  0,  0,  0, "vector"),
    ("K*+",        323,   891.67,  1.0,  3,  0,  1,  0,  0,  0, "vector"),
    ("K*0",        313,   895.55,  1.0,  0,  0,  1,  0,  0,  0, "vector"),
    ("omega",      223,   782.66,  1.0,  0,  0,  0,  0,  0,  0, "vector"),
    ("phi",        333,  1019.46,  1.0,  0,  0,  0,  0,  0,  0, "vector"),
    # --- heavy-flavor ground states
    ("D+",         411,  1869.66,  0.0,  3,  0,  0,  1,  0,  0, "heavy"),
    ("D0",         421,  1864.84,  0.0,  0,  0,  0,  1,  0,  0, "heavy"),
    ("Ds+",        431,  1968.35,  0.0,  3,  0,  1,  1,  0,  0, "heavy"),
    ("eta_c",      441,  2983.9,   0.0,  0,  0,  0,  0,  0,  0, "heavy"),
    ("J/psi",      443,  3096.9,   1.0,  0,  0,  0,  0,  0,  0, "heavy"),
    ("B+",         521,  5279.34,  0.0,  3,  0,  0,  0,  1,  0, "heavy"),
    ("B0",         511,  5279.66,  0.0,  0,  0,  0,  0,  1,  0, "heavy"),
    ("Bs0",        531,  5366.92,  0.0,  0,  0, -1,  0,  1,  0, "heavy"),
    ("Upsilon",    553,  9460.3,   1.0,  0,  0,  0,  0,  0,  0, "heavy"),
    ("Lambda_c+", 4122,  2286.46,  0.5,  3,  1,  0,  1,  0,  0, "heavy"),
    ("Lambda_b0", 5122,  5619.6,   0.5,  0,  1,  0,  0, -1,  0, "heavy"),
    ("Xi_cc++",   4422,  3621.4,   0.5,  6,  1,  0,  2,  0,  0, "heavy"),
]

_COLUMNS = ["name", "mcid", "mass_mev", "spin", "charge_thirds", "baryon",
            "strangeness", "charm", "beauty", "stable", "multiplet"]


def known_hadrons() -> pd.DataFrame:
    return pd.DataFrame(_HADRONS, columns=_COLUMNS)
