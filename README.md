# LatticeModel

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21410220.svg)](https://doi.org/10.5281/zenodo.21410220)

Rebuild of the **OptionSet lattice** particle-slot model. Design and provenance:
[MODEL_DESIGN.md](MODEL_DESIGN.md).

The model encodes fundamental particles as coordinates in a discrete space of
measurable properties, learns emergent families without Standard Model labels,
enumerates all valid property combinations, and ranks the *valid-but-unoccupied*
cells as candidate undiscovered particles. It is a slot finder, not a theory.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python scripts/run_pipeline.py   # full pipeline → data/output/*.csv
.venv/bin/python scripts/make_pca_plot.py  # PCA plot → data/output/*.png
.venv/bin/python -m pytest tests/ -q      # acceptance tests (design §6/§10 claims)
```

## Layout

- `lattice/particles.py` — hand-built known-particle dataset (PDG values +
  coarse flags, stability, discovery years)
- `lattice/pdg_data.py` — same dataset with mass/spin/charge loaded from the
  PDG SQLite database (official `pdg` package)
- `lattice/hadrons.py` — curated composite layer: 41 hadrons (baryon octet +
  decuplet, light meson nonets, heavy-flavor ground states) with flavor
  quantum numbers (baryon number, S, C, B̃) as extra lattice axes
- `lattice/features.py` — v1 (interaction-flag) and v2 (emergent exact-spin)
  OptionSet encoders, mass banding, propagation fraction
- `lattice/enumeration.py` — grid enumeration (bounds are explicit parameters)
- `lattice/filters.py` — theory/phenomenology sanity filters (design §4)
- `lattice/model.py` — k-means emergent families, 1-NN LOOCV, novelty scoring
- `lattice/pipeline.py` — gap analysis, ablation / leave-family-out /
  temporal backtests, graviton cell, score_v02 ranking
- `tests/` — the design-doc claims as executable tests

## Verification status (rebuilt vs. original session claims)

| Claim (design §6) | Rebuilt result |
|---|---|
| 1-NN LOOCV on emergent families = 100% | ✅ 100% (k=5, min-max scaling) |
| Higgs ablation recovers neutral scalar slot, ~10⁵ MeV band | ✅ recovered |
| Top ablation recovers +2/3 quark-like slot, ~10⁵ MeV band | ✅ recovered |
| Graviton cell (spin 2, neutral, massless, stable) unoccupied | ✅ unoccupied |
| Graviton nearest knowns: photon, gluon, then neutrinos | ✅ exact match |
| 1,437 raw → 397 filtered slots | ⚠️ not comparable — original grid bounds unknown; this rebuild: 6,641 → 2,477 with the bounds in `enumeration.py` |
| §10.1 leave-family-out (charged leptons; vector bosons) | ✅ all cells recovered |
| §10.2 temporal backtest, freeze 1994 | ✅ top + Higgs recovered; ν_τ degenerate (its coarse OptionSet is identical to ν_e/ν_μ, so its cell stays occupied) |
| §13.2 PDG data integration | ✅ mass/spin/charge from PDG SQLite (2026 edition); 100% LOOCV holds on PDG values |
| Ω⁻ ablation (hadron layer) | ✅ removing Ω⁻ leaves an empty-but-allowed cell at (spin 3/2, Q=−1, S=−3); nearest knowns Ξ*⁻, Ξ*⁰, Σ*⁻ — the 1962 decuplet prediction, rerun |
| Ω⁻ mass prediction (GMO) | ✅ linear mass-vs-strangeness fit over the remaining decuplet predicts 1685 MeV vs 1672.45 measured (0.8% error; the 1962 estimate was ~1680) |
| τ mass prediction (Koide) | ✅ with τ removed, the Koide relation over (e, μ) predicts 1777.0 MeV vs 1776.86 measured (0.008% error — the 1981 prediction, rerun) |
| Top-quark ladder backtest | ✅ log-mass extrapolation from (u, c) is rough in MeV (~750 GeV) but lands the correct ~10⁵ MeV lattice band |
| §10.3 null-model baselines | ✅ leave-one-out recovery beats a uniform null at p ≈ 10⁻¹⁷ (mean percentile 0.137 over 45 ablations); 100% LOOCV unreachable by permuted labels (p = 0.005); Koide/GMO beat naive-mean nulls by 2–4 orders of magnitude — full report in `data/output/null_model_report.md` (regenerate: `scripts/run_null_baselines.py`) |
| §10.4 jitter robustness | ✅ at ±26% mass noise (far beyond measurement error) recovery and LOOCV stay at 100% across 50 trials; GMO precision degrades to null-level there but fully holds at measurement scale — precision predictions need precision inputs |
| §10.5–10.6 operating curve / FDR | ✅ pre-registered "top 10% by proximity" rule captures 71% of true pattern-completions at 7.1× the null rate (binomial p ≈ 10⁻²²); top-5% captures 64% at 12.9× |
| Historical precision audit | ✅ 16 sourced gap-predictions (`lattice/audit.py`, `scripts/run_audit.py`): precision 8/12 = 67% [39%, 86%], sensitivity 53–73%; within-pattern completions 8/8 confirmed vs beyond-pattern extrapolations 0/4 (Fisher p ≈ 0.002) |
| **Registered forward predictions** | ◇ `docs/forward-predictions-2026.md` (2026-07-17): Ξ_bb 10 250, Ω_bb 10 410, Ξ_bc 6 932, Ω_bc 7 092, all ± 48 MeV — within-pattern doubly-heavy baryon cells; held-out Ω_cc⁺ validation: predicted 3 775 vs 3 727 measured (LHCb, June 2026) |

The lattice explorer (`scripts/make_lattice3d.py` → `data/output/lattice3d.html`)
has two views: a rotatable **3D** voxel lattice (fundamental / hadron layers)
and eightfold-way **Planes** — charge × strangeness panels per (baryon number,
spin, charm, beauty) class, with known multiplets filled in and every
allowed-but-empty cell shaded by novelty. The hadron filter enforces integer
electric charge (confinement), spin-statistics, a Gell-Mann–Nishijima window,
and flavor bounds — 18,720 grid cells → 693 candidate slots.
