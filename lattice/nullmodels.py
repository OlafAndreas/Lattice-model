"""Null-model baselines (MODEL_DESIGN.md §10.3).

Each experiment pairs a headline claim with an explicit chance model:

1. recovery_rank_experiment — leave-one-out over both layers; the removed
   particle's cell should rank closer to known structure (low novelty)
   than a uniformly random candidate. Null: rank percentile ~ U(0,1);
   the mean of n percentiles is compared via a normal approximation.
2. loocv_permutation_test — the 100% LOOCV must not be achievable with
   shuffled family labels.
3. mass_prediction_vs_null — Koide/GMO/ladder predictions vs the naive
   "predict the mean of the remaining members" baseline, in log space.
4. filter_null_test — the theory filters pass 100% of knowns at low grid
   keep-rates; a random filter of equal selectivity would not. In-sample
   caveat: the filters were written knowing the knowns, so this measures
   consistency, not out-of-sample discovery power.
"""

import math

import numpy as np
import pandas as pd

from .features import V1_FEATURES, encode_hadrons, encode_v1
from .generations import koide_predict_third, ladder_fit, ladder_predict
from .gmo import fit_mass_vs_strangeness, predict_mass
from .hadrons import HADRON_FEATURES, known_hadrons
from .model import fit_families, loocv_accuracy
from .particles import known_particles
from .pipeline import OMEGA_CELL, run_hadrons, run_v1


def _proximity_percentile(candidates: pd.DataFrame, target: pd.Series,
                          features: list[str]) -> float | None:
    """Rank percentile of the target cell when candidates are sorted by
    proximity to known structure (ascending novelty). 0 = closest."""
    ranked = candidates.sort_values("novelty").reset_index(drop=True)
    match = (ranked[features] == target[features]).all(axis=1)
    if not match.any():
        return None
    return (int(match.idxmax()) + 0.5) / len(ranked)


def recovery_rank_experiment() -> dict:
    results, n_unrecovered = [], 0

    def run_layer(layer, table, encode, features, runner):
        nonlocal n_unrecovered
        enc = encode(table)
        for name in table["name"]:
            target = enc[enc["name"] == name].iloc[0]
            occupied = (enc[features] == target[features]).all(axis=1).sum()
            if occupied > 1:
                continue  # degenerate cell stays occupied — not evaluable
            result = runner(table[table["name"] != name])
            pct = _proximity_percentile(result["candidates"], target, features)
            if pct is None:
                n_unrecovered += 1
                continue
            results.append({"layer": layer, "name": name, "percentile": pct})

    run_layer("fundamental", known_particles(), encode_v1, V1_FEATURES, run_v1)
    run_layer("hadron", known_hadrons(), encode_hadrons, HADRON_FEATURES,
              run_hadrons)

    percentiles = np.array([r["percentile"] for r in results])
    n = len(percentiles)
    mean = float(percentiles.mean())
    # mean of n U(0,1) ≈ N(0.5, 1/sqrt(12n)); one-sided lower tail
    z = (0.5 - mean) * math.sqrt(12 * n)
    p_value = 0.5 * math.erfc(z / math.sqrt(2))

    return {"results": results, "n": n, "n_unrecovered": n_unrecovered,
            "mean_percentile": mean, "z": z, "p_value": p_value}


def loocv_permutation_test(n_permutations: int = 200, seed: int = 42) -> dict:
    X = encode_v1(known_particles())[V1_FEATURES]
    families = fit_families(X)
    observed = loocv_accuracy(X, families)

    rng = np.random.default_rng(seed)
    perm_accs = np.array([loocv_accuracy(X, rng.permutation(families))
                          for _ in range(n_permutations)])
    p_value = (np.sum(perm_accs >= observed) + 1) / (n_permutations + 1)

    return {"observed": observed, "perm_mean": float(perm_accs.mean()),
            "perm_max": float(perm_accs.max()), "p_value": float(p_value)}


def _mass_row(tool, predicted, measured, null_prediction):
    return {
        "tool": tool, "predicted_mev": predicted, "measured_mev": measured,
        "rel_error": abs(predicted - measured) / measured,
        "null_prediction_mev": null_prediction,
        "null_rel_error": abs(null_prediction - measured) / measured,
        "log_err": math.log10(predicted / measured),
        "null_log_err": math.log10(null_prediction / measured),
    }


def mass_prediction_vs_null() -> list[dict]:
    p = known_particles().set_index("name")["mass_mev"]
    h = known_hadrons()

    rows = [_mass_row("koide_tau",
                      koide_predict_third(p["electron"], p["muon"]),
                      p["tau"],
                      (p["electron"] + p["muon"]) / 2)]

    decuplet = h[(h["baryon"] == 1) & (h["spin"] == OMEGA_CELL["spin"])
                 & (h["charm"] == 0) & (h["beauty"] == 0)
                 & (h["name"] != "Omega-")]
    omega_measured = float(h.set_index("name").loc["Omega-", "mass_mev"])
    fit = fit_mass_vs_strangeness(decuplet)
    rows.append(_mass_row("gmo_omega",
                          predict_mass(fit, OMEGA_CELL["strangeness"]),
                          omega_measured,
                          float(decuplet["mass_mev"].mean())))

    rows.append(_mass_row("ladder_top",
                          ladder_predict(ladder_fit([p["up"], p["charm"]]), 2),
                          p["top"],
                          (p["up"] + p["charm"]) / 2))
    return rows


def filter_null_test() -> dict:
    layers = []
    for layer, result, n_knowns in [("fundamental", run_v1(), 17),
                                    ("hadron", run_hadrons(), 41)]:
        keep = (result["n_filtered"] + n_knowns) / result["n_grid"]
        layers.append({
            "layer": layer, "keep_rate": keep, "n_knowns": n_knowns,
            "p_random_filter": keep ** n_knowns,
        })
    return {"layers": layers,
            "caveat": ("in-sample: the filters were written knowing the "
                       "known particles, so this measures structural "
                       "consistency, not out-of-sample discovery power")}
