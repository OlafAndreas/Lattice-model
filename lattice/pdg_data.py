"""Known-particle dataset backed by the PDG SQLite database
(MODEL_DESIGN.md §13 step 2), via the official `pdg` package.

PDG supplies mass, charge and spin (J). The coarse interaction flags,
stability and discovery years are model conventions, not PDG measurables —
they are taken from the hand-built table in particles.py.

Fallbacks where PDG has no mass value: photon/gluon → 0 (massless),
neutrinos → the representative sub-eV scale from the hand-built table.
"""

from fractions import Fraction

import pandas as pd

from .particles import known_particles

MCID = {
    "down": 1, "up": 2, "strange": 3, "charm": 4, "bottom": 5, "top": 6,
    "electron": 11, "nu_e": 12, "muon": 13, "nu_mu": 14, "tau": 15,
    "nu_tau": 16, "gluon": 21, "photon": 22, "Z": 23, "W": 24, "higgs": 25,
}

_cache: pd.DataFrame | None = None


def _pdg_mass_mev(particle, fallback_mev: float) -> float:
    try:
        mass_gev = particle.mass
    except Exception:
        mass_gev = None
    if mass_gev is None:
        # Light quarks expose their mass only via the masses() list. Skip
        # limit entries (e.g., the photon-mass upper limit): a limit is a
        # bound, not a measured value.
        try:
            summary = next(iter(particle.masses())).best_summary()
            if not summary.is_limit:
                mass_gev = summary.get_value("GeV")
        except Exception:
            mass_gev = None
    if mass_gev is None:
        return fallback_mev
    return mass_gev * 1000.0


def pdg_particles() -> pd.DataFrame:
    global _cache
    if _cache is not None:
        return _cache.copy()

    import pdg

    api = pdg.connect()
    hand = known_particles().set_index("name")

    rows = []
    for name, mcid in MCID.items():
        p = api.get_particle_by_mcid(mcid)
        h = hand.loc[name]
        rows.append({
            "name": name,
            "mass_mev": _pdg_mass_mev(p, fallback_mev=h["mass_mev"]),
            "spin": float(Fraction(p.quantum_J)),
            "charge_thirds": round(p.charge * 3),
            "strong": h["strong"],
            "em": h["em"],
            "weak": h["weak"],
            "stable": h["stable"],
            "discovered": h["discovered"],
        })

    df = pd.DataFrame(rows)[known_particles().columns]
    _cache = df
    return df.copy()
