"""Pipeline orchestration: gap analysis, ablation backtests, graviton cell
(MODEL_DESIGN.md §3, §6) and scoring (§5)."""

from typing import Optional

import pandas as pd

from .enumeration import (enumerate_grid_hadrons, enumerate_grid_v1,
                          enumerate_grid_v2)
from .features import (V1_FEATURES, V2_FEATURES, encode_hadrons, encode_v1,
                       encode_v2, propagation_fraction)
from .filters import hadron_filter, theory_filter_v1, theory_filter_v2
from .hadrons import HADRON_FEATURES, known_hadrons
from .model import fit_families, loocv_accuracy, nearest_known, novelty_scores
from .particles import known_particles

GRAVITON_CELL = {"spin": 2.0, "charge_1_3": 0, "has_charge": 0,
                 "logMass": -9, "stable_band": 1}


def _subtract_known(grid: pd.DataFrame, known: pd.DataFrame,
                    features: list[str]) -> pd.DataFrame:
    merged = grid.merge(known[features].drop_duplicates(), on=features,
                        how="left", indicator=True)
    return merged[merged["_merge"] == "left_only"][features].reset_index(drop=True)


def run_v1(particles: Optional[pd.DataFrame] = None) -> dict:
    """Full v1 pipeline: encode → families → LOOCV → enumerate → filter →
    subtract knowns → novelty-rank."""
    if particles is None:
        particles = known_particles()
    known = encode_v1(particles)
    X = known[V1_FEATURES]

    families = fit_families(X)
    loocv = loocv_accuracy(X, families)

    grid = enumerate_grid_v1()
    unseen = _subtract_known(grid, known, V1_FEATURES)
    filtered = theory_filter_v1(unseen).reset_index(drop=True)

    candidates = filtered.copy()
    candidates["novelty"] = novelty_scores(X, filtered)
    candidates = candidates.sort_values(
        "novelty", ascending=False).reset_index(drop=True)

    return {
        "known": known,
        "families": families,
        "loocv": loocv,
        "n_grid": len(grid),
        "n_raw_unseen": len(unseen),
        "n_filtered": len(filtered),
        "candidates": candidates,
    }


def ablation_backtest(name: str) -> Optional[pd.Series]:
    """Remove one known particle, rebuild, and return the candidate row
    matching the removed particle's OptionSet (None if not recovered)."""
    particles = known_particles()
    target = encode_v1(particles[particles["name"] == name]).iloc[0]
    result = run_v1(particles[particles["name"] != name])
    c = result["candidates"]
    match = c[(c[V1_FEATURES] == target[V1_FEATURES]).all(axis=1)]
    if len(match) == 0:
        return None
    return match.iloc[0]


def _recovery_check(names: list[str]) -> tuple[list[str], list[str]]:
    """Remove `names`, rebuild, and split them into (recovered, degenerate):
    recovered — the removed particle's OptionSet appears as a candidate;
    degenerate — its cell is still occupied by a remaining known particle
    with an identical coarse OptionSet (e.g., the three neutrinos)."""
    particles = known_particles()
    targets = encode_v1(particles[particles["name"].isin(names)])
    remaining = particles[~particles["name"].isin(names)]
    result = run_v1(remaining)
    c = result["candidates"]
    known_cells = encode_v1(remaining)[V1_FEATURES]

    recovered, degenerate = [], []
    for _, target in targets.iterrows():
        if (c[V1_FEATURES] == target[V1_FEATURES]).all(axis=1).any():
            recovered.append(target["name"])
        elif (known_cells == target[V1_FEATURES]).all(axis=1).any():
            degenerate.append(target["name"])
    return recovered, degenerate


def leave_family_out_backtest(family: list[str]) -> list[str]:
    """MODEL_DESIGN.md §10.1: remove an entire particle class and check the
    lattice still surfaces their cells. Returns the recovered names."""
    recovered, _ = _recovery_check(family)
    return recovered


def temporal_backtest(year: int) -> dict:
    """MODEL_DESIGN.md §10.2: freeze the dataset at `year` and check that
    later discoveries are flagged as empty-but-allowed slots."""
    particles = known_particles()
    held_out = list(particles[particles["discovered"] > year]["name"])
    recovered, degenerate = _recovery_check(held_out)
    return {"held_out": held_out, "recovered": recovered,
            "degenerate": degenerate}


def graviton_cell() -> dict:
    """Locate the graviton coordinate in the v2 emergent exact-spin lattice."""
    known = encode_v2(known_particles())
    cell = pd.DataFrame([GRAVITON_CELL])[V2_FEATURES]

    grid = theory_filter_v2(enumerate_grid_v2())
    in_grid = len(grid.merge(cell, on=V2_FEATURES)) > 0
    occupied = len(known.merge(cell, on=V2_FEATURES)) > 0

    return {
        "in_grid": in_grid,
        "occupied": occupied,
        "nearest_known": nearest_known(known[V2_FEATURES], known["name"], cell),
        "novelty": float(novelty_scores(known[V2_FEATURES], cell)[0]),
    }


OMEGA_CELL = {"spin": 1.5, "charge_1_3": -3, "logMass": 3, "stable_band": 0,
              "baryon": 1, "strangeness": -3, "charm": 0, "beauty": 0}


def run_hadrons(hadrons: Optional[pd.DataFrame] = None) -> dict:
    """Gap analysis on the composite (hadron) lattice."""
    if hadrons is None:
        hadrons = known_hadrons()
    known = encode_hadrons(hadrons)

    grid = enumerate_grid_hadrons()
    unseen = _subtract_known(grid, known, HADRON_FEATURES)
    filtered = hadron_filter(unseen).reset_index(drop=True)

    candidates = filtered.copy()
    candidates["novelty"] = novelty_scores(known[HADRON_FEATURES], filtered)
    candidates = candidates.sort_values(
        "novelty", ascending=False).reset_index(drop=True)

    return {
        "known": known,
        "n_grid": len(grid),
        "n_raw_unseen": len(unseen),
        "n_filtered": len(filtered),
        "candidates": candidates,
    }


def omega_ablation() -> Optional[dict]:
    """The 1962 backtest: remove the Ω⁻ and check that its decuplet-corner
    cell (spin 3/2, Q=−1, S=−3) resurfaces as an empty-but-allowed slot."""
    hadrons = known_hadrons()
    remaining = hadrons[hadrons["name"] != "Omega-"]
    result = run_hadrons(remaining)
    c = result["candidates"]
    cell = pd.Series(OMEGA_CELL)
    match = c[(c[HADRON_FEATURES] == cell[HADRON_FEATURES]).all(axis=1)]
    if len(match) == 0:
        return None
    known = result["known"]
    hit = match.iloc[0].to_dict()
    hit["nearest_known"] = nearest_known(
        known[HADRON_FEATURES], known["name"],
        pd.DataFrame([OMEGA_CELL])[HADRON_FEATURES], k=3)

    # GMO mass prediction from the remaining members of the Ω⁻'s panel
    from .gmo import fit_mass_vs_strangeness, predict_mass
    panel = remaining[(remaining["baryon"] == OMEGA_CELL["baryon"])
                      & (remaining["spin"] == OMEGA_CELL["spin"])
                      & (remaining["charm"] == 0) & (remaining["beauty"] == 0)]
    fit = fit_mass_vs_strangeness(panel)
    if fit is not None:
        hit["predicted_mass_mev"] = predict_mass(fit, OMEGA_CELL["strangeness"])
    return hit


def score_v02(novelty: float, measurability: float,
              propagation_fraction: float) -> float:
    """MODEL_DESIGN.md §5: 0.55·novelty + 0.35·measurability + 0.10·prop."""
    return 0.55 * novelty + 0.35 * measurability + 0.10 * propagation_fraction


def measurability_v1(row: pd.Series) -> float:
    """Heuristic detectability: rewards EM/strong signatures and
    collider-reachable mass bands. Placeholder for the per-experiment reach
    model in MODEL_DESIGN.md §13."""
    reach = 1.0 if row["logMass"] <= 5 else 0.5
    signature = 0.5 * row["EM"] + 0.3 * row["Strong"] + 0.2 * row["Weak"]
    return reach * signature


def rank_v02(candidates: pd.DataFrame) -> pd.DataFrame:
    """Attach propagation, measurability and score_v02; sort by score."""
    c = candidates.copy()
    max_novelty = c["novelty"].max() or 1.0
    c["novelty_norm"] = c["novelty"] / max_novelty
    c["propagation_fraction"] = c["logMass"].map(propagation_fraction)
    c["measurability"] = c.apply(measurability_v1, axis=1)
    c["score_v02"] = c.apply(
        lambda r: score_v02(r["novelty_norm"], r["measurability"],
                            r["propagation_fraction"]), axis=1)
    return c.sort_values("score_v02", ascending=False).reset_index(drop=True)
