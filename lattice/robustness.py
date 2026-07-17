"""Robustness and calibration experiments (MODEL_DESIGN.md §10.4–10.6).

- jitter_experiment: multiply every mass by 10^N(0, σ) — a stress test far
  beyond measurement uncertainty (σ=0.1 dex ≈ ±26%) that can flip coarse
  mass bands — and re-run the headline backtests each trial.
- operating_curve: the pre-registered decision rule "search the top k% of
  candidates by proximity", scored against the 45 leave-one-out ablations.
  Recall@k vs the null expectation k gives enrichment and a binomial
  p-value — the §10.6 false-discovery framing.
"""

import math
from statistics import median

import numpy as np
import pandas as pd

from .features import V1_FEATURES, encode_hadrons, encode_v1
from .gmo import fit_mass_vs_strangeness, predict_mass
from .hadrons import HADRON_FEATURES, known_hadrons
from .model import fit_families, loocv_accuracy
from .nullmodels import _proximity_percentile, recovery_rank_experiment
from .particles import known_particles
from .pipeline import OMEGA_CELL, run_hadrons, run_v1


def jitter_masses(table: pd.DataFrame, sigma_dex: float,
                  rng: np.random.Generator) -> pd.DataFrame:
    out = table.copy()
    factors = 10.0 ** rng.normal(0.0, sigma_dex, len(out))
    out["mass_mev"] = out["mass_mev"] * factors
    return out


def _cell_recovered(table, name, encode, features, runner) -> bool:
    enc = encode(table)
    target = enc[enc["name"] == name].iloc[0]
    result = runner(table[table["name"] != name])
    return _proximity_percentile(
        result["candidates"], target, features) is not None


def jitter_experiment(n_trials: int = 50, sigma_dex: float = 0.1,
                      seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    loocv_ok = higgs_ok = top_ok = omega_ok = 0
    gmo_errors, null_errors = [], []

    for _ in range(n_trials):
        parts = jitter_masses(known_particles(), sigma_dex, rng)
        hadrons = jitter_masses(known_hadrons(), sigma_dex, rng)

        X = encode_v1(parts)[V1_FEATURES]
        if loocv_accuracy(X, fit_families(X)) == 1.0:
            loocv_ok += 1

        if _cell_recovered(parts, "higgs", encode_v1, V1_FEATURES, run_v1):
            higgs_ok += 1
        if _cell_recovered(parts, "top", encode_v1, V1_FEATURES, run_v1):
            top_ok += 1
        if _cell_recovered(hadrons, "Omega-", encode_hadrons,
                           HADRON_FEATURES, run_hadrons):
            omega_ok += 1

        decuplet = hadrons[(hadrons["baryon"] == 1) & (hadrons["spin"] == 1.5)
                           & (hadrons["charm"] == 0) & (hadrons["beauty"] == 0)
                           & (hadrons["name"] != "Omega-")]
        measured = float(hadrons.set_index("name").loc["Omega-", "mass_mev"])
        fit = fit_mass_vs_strangeness(decuplet)
        predicted = predict_mass(fit, OMEGA_CELL["strangeness"])
        gmo_errors.append(abs(predicted - measured) / measured)
        null_errors.append(
            abs(float(decuplet["mass_mev"].mean()) - measured) / measured)

    return {
        "n_trials": n_trials, "sigma_dex": sigma_dex,
        "loocv_stable_rate": loocv_ok / n_trials,
        "higgs_recovery_rate": higgs_ok / n_trials,
        "top_recovery_rate": top_ok / n_trials,
        "omega_recovery_rate": omega_ok / n_trials,
        "gmo_median_rel_error": median(gmo_errors),
        "null_median_rel_error": median(null_errors),
    }


def _binom_upper_tail(n: int, k: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i)
               for i in range(k, n + 1))


def operating_curve(ks: tuple = (0.01, 0.05, 0.10, 0.25)) -> dict:
    recovery = recovery_rank_experiment()
    percentiles = [r["percentile"] for r in recovery["results"]]
    n = len(percentiles)

    rows = []
    for k in ks:
        hits = sum(1 for p in percentiles if p <= k)
        recall = hits / n
        rows.append({
            "k": k, "hits": hits, "recall": recall,
            "enrichment": recall / k,
            "expected_null_recall": k,
            "p_value": _binom_upper_tail(n, hits, k),
        })

    return {
        "n_ablations": n,
        "rows": rows,
        "decision_rule": ("pre-registered: flag the top 10% of candidate "
                          "cells by proximity as search targets; under the "
                          "null, 10% of true cells would be flagged by "
                          "chance"),
    }
