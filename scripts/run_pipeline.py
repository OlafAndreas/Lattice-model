"""Run the full OptionSet lattice pipeline and regenerate the artifacts
listed in MODEL_DESIGN.md §12 (CSV outputs into data/output/)."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lattice.enumeration import enumerate_grid_v2
from lattice.features import V2_FEATURES, encode_v2, propagation_fraction
from lattice.filters import theory_filter_v2
from lattice.model import nearest_known, novelty_scores
from lattice.particles import known_particles
from lattice.pipeline import (GRAVITON_CELL, ablation_backtest, graviton_cell,
                              leave_family_out_backtest, omega_ablation,
                              rank_v02, run_hadrons, run_v1, temporal_backtest)

OUT = Path(__file__).resolve().parents[1] / "data" / "output"
OUT.mkdir(parents=True, exist_ok=True)

UPS_MPS = 299_792_458  # universal potential speed (MODEL_DESIGN.md §2)


def main() -> None:
    print("=== OptionSet lattice pipeline (rebuild) ===\n")

    # ---- v1 pipeline
    result = run_v1()
    known = result["known"]
    candidates = rank_v02(result["candidates"])

    known_out = known.copy()
    known_out["universal_potential_speed_mps"] = UPS_MPS
    known_out["propagation_fraction"] = known_out["logMass"].map(propagation_fraction)
    known_out.to_csv(OUT / "known_particles_features.csv", index=False)

    candidates["universal_potential_speed_mps"] = UPS_MPS
    candidates.to_csv(OUT / "candidates_theory_filtered_ranked.csv", index=False)
    candidates.head(20).to_csv(OUT / "candidates_top20.csv", index=False)

    print(f"known particles:            {len(known)}")
    print(f"LOOCV accuracy (1-NN):      {result['loocv']:.0%}   (claim: 100%)")
    print(f"enumerated grid cells:      {result['n_grid']}")
    print(f"raw valid-but-unseen:       {result['n_raw_unseen']}   (claim: 1,437 — grid bounds differ)")
    print(f"after theory filters:       {result['n_filtered']}   (claim: 397 — grid bounds differ)")

    # ---- ablation backtests
    print("\n--- ablation backtests ---")
    for name in ("higgs", "top"):
        hit = ablation_backtest(name)
        if hit is None:
            print(f"{name} removed → slot NOT recovered ✗")
        else:
            rank = int(hit.name) + 1 if hasattr(hit, "name") else "?"
            print(f"{name} removed → slot recovered ✓  novelty={hit['novelty']:.3f}")

    # ---- family and temporal backtests (design §10)
    print("\n--- leave-family-out backtests ---")
    for family in (["electron", "muon", "tau"], ["photon", "gluon", "W", "Z"]):
        recovered = leave_family_out_backtest(family)
        mark = "✓" if set(recovered) == set(family) else "✗"
        print(f"remove {family} → recovered {recovered} {mark}")

    print("\n--- temporal backtests ---")
    for year in (1994, 2011):
        r = temporal_backtest(year)
        print(f"freeze at {year}: held out {r['held_out']} → "
              f"recovered {r['recovered']}, degenerate {r['degenerate']}")

    # ---- v2 emergent exact-spin lattice
    print("\n--- v2 emergent lattice (exact spin, no force flags) ---")
    known_v2 = encode_v2(known_particles())
    grid_v2 = theory_filter_v2(enumerate_grid_v2()).reset_index(drop=True)
    merged = grid_v2.merge(known_v2[V2_FEATURES].drop_duplicates(),
                           on=V2_FEATURES, how="left", indicator=True)
    unseen_v2 = merged[merged["_merge"] == "left_only"][V2_FEATURES].reset_index(drop=True)
    unseen_v2["novelty"] = novelty_scores(known_v2[V2_FEATURES], unseen_v2)
    unseen_v2 = unseen_v2.sort_values("novelty", ascending=False).reset_index(drop=True)
    unseen_v2.to_csv(OUT / "emergent_exactspin_candidates_ranked.csv", index=False)
    print(f"v2 candidate slots:         {len(unseen_v2)}")

    cell = graviton_cell()
    grav_rank = unseen_v2.index[
        (unseen_v2[V2_FEATURES] == pd.Series(GRAVITON_CELL)[V2_FEATURES]).all(axis=1)
    ]
    neighbors = nearest_known(known_v2[V2_FEATURES], known_v2["name"],
                              pd.DataFrame([GRAVITON_CELL])[V2_FEATURES], k=5)
    pd.DataFrame({"nearest_known": neighbors}).to_csv(
        OUT / "graviton_nearest_known_exactspin.csv", index=False)
    print(f"graviton cell occupied:     {cell['occupied']}   (claim: False)")
    print(f"graviton nearest knowns:    {neighbors}   (claim: photon, gluon, then neutrinos)")
    if len(grav_rank):
        print(f"graviton cell novelty rank: {grav_rank[0] + 1} of {len(unseen_v2)}")

    # ---- hadron (composite) layer
    print("\n--- hadron layer (41 curated states + flavor axes) ---")
    hr = run_hadrons()
    hr["candidates"].to_csv(OUT / "hadron_candidates_ranked.csv", index=False)
    print(f"hadron grid: {hr['n_grid']} → filtered candidates: {hr['n_filtered']}")
    omega = omega_ablation()
    if omega is None:
        print("Ω⁻ removed → decuplet corner NOT recovered ✗")
    else:
        print(f"Ω⁻ removed → decuplet corner recovered ✓  "
              f"novelty={omega['novelty']:.3f}, nearest {omega['nearest_known']}")
        if "predicted_mass_mev" in omega:
            print(f"  GMO mass prediction: {omega['predicted_mass_mev']:.0f} MeV "
                  f"(measured 1672 MeV)")

    # ---- generation-ladder predictions (fundamental layer)
    from lattice.generations import gen4_predictions, tau_backtest, top_ladder_backtest
    print("\n--- generation-ladder backtests ---")
    tau = tau_backtest()
    print(f"τ removed → Koide predicts {tau['predicted_mass_mev']:.1f} MeV "
          f"(measured {tau['measured_mass_mev']:.2f}, "
          f"error {tau['relative_error']:+.4%})")
    top = top_ladder_backtest()
    print(f"top removed → ladder predicts band {top['predicted_band']} "
          f"(measured band {top['measured_band']}); "
          f"~{top['predicted_mass_mev']/1e3:.0f} GeV vs 173 GeV measured")
    print("gen-4 extrapolations (EW-disfavored, shown as ◇ in the viz):")
    for p in gen4_predictions():
        print(f"  {p['label']}: ≈{p['mass_mev']/1e3:,.0f} GeV via {p['method']}")

    print(f"\nartifacts written to {OUT}")


if __name__ == "__main__":
    main()
