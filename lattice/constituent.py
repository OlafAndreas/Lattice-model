"""Additive constituent-quark mass model over the curated baryons, and the
registered forward predictions for unobserved doubly-heavy baryons.

Model: m ≈ β₀ + β_s·n_s + β_c·n_c + β_b·n_b + β_J·[J=3/2], least squares
over the known baryons (light-quark count is 3 − n_s − n_c − n_b, absorbed
by the intercept). Deliberately crude — no hyperfine or binding terms
beyond what the data supports — with the LOO RMS as its honest error bar.
The Ω_cc⁺ (LHCb, June 2026) is excluded from training and used as an
out-of-sample validation point.
"""

import numpy as np

from .features import mass_band
from .hadrons import known_hadrons

# strange/charm/bottom quark content per curated baryon
BARYON_CONTENT = {
    "p": (0, 0, 0), "n": (0, 0, 0),
    "Lambda": (1, 0, 0), "Sigma+": (1, 0, 0), "Sigma0": (1, 0, 0),
    "Sigma-": (1, 0, 0), "Xi0": (2, 0, 0), "Xi-": (2, 0, 0),
    "Delta++": (0, 0, 0), "Delta+": (0, 0, 0), "Delta0": (0, 0, 0),
    "Delta-": (0, 0, 0), "Sigma*+": (1, 0, 0), "Sigma*0": (1, 0, 0),
    "Sigma*-": (1, 0, 0), "Xi*0": (2, 0, 0), "Xi*-": (2, 0, 0),
    "Omega-": (3, 0, 0),
    "Lambda_c+": (0, 1, 0), "Lambda_b0": (0, 0, 1), "Xi_cc++": (0, 2, 0),
}

FEATURES = ["n_s", "n_c", "n_b", "spin32"]


def _design(rows):
    X = np.array([[1.0, r[0], r[1], r[2], r[3]] for r in rows])
    return X


def _baryon_rows(exclude: str | None = None):
    h = known_hadrons()
    baryons = h[h["baryon"] == 1]
    rows, masses, names = [], [], []
    for _, r in baryons.iterrows():
        if r["name"] == exclude:
            continue
        n_s, n_c, n_b = BARYON_CONTENT[r["name"]]
        rows.append((n_s, n_c, n_b, 1.0 if r["spin"] == 1.5 else 0.0))
        masses.append(r["mass_mev"])
        names.append(r["name"])
    return rows, np.array(masses), names


def fit_baryon_model(exclude: str | None = None) -> np.ndarray:
    rows, masses, _ = _baryon_rows(exclude)
    beta, *_ = np.linalg.lstsq(_design(rows), masses, rcond=None)
    return beta


def predict_baryon(model: np.ndarray, n_s: int, n_c: int, n_b: int,
                   spin: float) -> float:
    x = np.array([1.0, n_s, n_c, n_b, 1.0 if spin == 1.5 else 0.0])
    return float(x @ model)


def loo_rms() -> tuple[float, int]:
    """Leave-one-out RMS over baryons whose removal keeps every feature
    column supported (e.g. Λb is the only b-carrier, so its LOO fit is
    singular and it is excluded from the estimate)."""
    rows, masses, names = _baryon_rows()
    arr = np.array(rows)
    errors = []
    for i, name in enumerate(names):
        remaining = np.delete(arr, i, axis=0)
        if any(remaining[:, j].sum() == 0 for j in range(3)
               if arr[i, j] > 0):
            continue  # removal would leave a flavor column unsupported
        model = fit_baryon_model(exclude=name)
        pred = predict_baryon(model, *arr[i, :3].astype(int),
                              spin=1.5 if arr[i, 3] else 0.5)
        errors.append(pred - masses[i])
    return float(np.sqrt(np.mean(np.square(errors)))), len(errors)


def forward_predictions() -> list[dict]:
    """Registered predictions for unobserved doubly-heavy baryon ground
    states (J^P = 1/2+), plus the Ω_cc⁺ out-of-sample validation row."""
    model = fit_baryon_model()
    rms, _ = loo_rms()
    # quote the larger of in-sample LOO RMS and the one out-of-sample
    # validation miss (Ω_cc⁺: predicted vs LHCb ~3727 MeV) — extrapolation
    # error exceeds interpolation error, and the registration says so
    validation_miss = abs(predict_baryon(model, 1, 2, 0, 0.5) - 3727.0)
    unc = max(rms, validation_miss)

    def entry(name, n_s, n_c, n_b, q_states, rid, kind="mass", spin=0.5,
              note=""):
        m = predict_baryon(model, n_s, n_c, n_b, spin=spin)
        return {
            "name": name, "id": rid, "kind": kind, "spin": spin,
            "S": -n_s, "C": n_c, "Bt": -n_b,
            "q_states": q_states, "mass_mev": round(m),
            "uncertainty_mev": round(unc), "band": mass_band(m),
            "note": note,
        }

    return [
        entry("Xi_bb", 0, 0, 2, [0, -3], "LM-2026-001",
              note="bbu / bbd isospin doublet; unobserved"),
        entry("Omega_bb", 1, 0, 2, [-3], "LM-2026-002",
              note="bbs; unobserved"),
        entry("Xi_bc", 0, 1, 1, [3, 0], "LM-2026-003",
              note="bcu / bcd; LHCb hints at 6571/6694 MeV (4.3σ/4.1σ), "
                   "no observation"),
        entry("Omega_bc", 1, 1, 1, [0], "LM-2026-004",
              note="bcs; unobserved"),
        entry("Xi_cc+", 0, 2, 0, [3], "LM-2026-005",
              note="ccd isospin partner of the observed Xi_cc++; "
                   "discriminating: SELEX's unconfirmed 3519 MeV claim "
                   "sits 2σ below this prediction"),
        entry("Omega_ccc", 0, 3, 0, [6], "LM-2026-006",
              kind="cell-upper-bound", spin=1.5,
              note="ccc decuplet-analog corner — the 'Omega- of charm'; "
                   "CELL-LEVEL registration: additive value is an upper "
                   "bound (three unmodeled heavy pairs; true mass expected "
                   "~300-400 MeV below; lattice QCD ~4800)"),
        entry("Omega_bbb", 0, 0, 3, [-3], "LM-2026-007",
              kind="cell-upper-bound", spin=1.5,
              note="bbb corner — the 'Omega- of beauty'; CELL-LEVEL "
                   "registration: additive value is an upper bound (true "
                   "mass expected ~500-700 MeV below; lattice QCD ~14400)"),
        entry("Omega_cc+ (validation)", 1, 2, 0, [3], "LM-2026-V01",
              kind="validation",
              note="held out of training; LHCb June 2026: ~3727 MeV"),
    ]
