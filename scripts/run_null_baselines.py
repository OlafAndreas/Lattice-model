"""Run all null-model baseline experiments (MODEL_DESIGN.md §10.3) and
write data/output/null_model_report.md."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lattice.nullmodels import (filter_null_test, loocv_permutation_test,
                                mass_prediction_vs_null,
                                recovery_rank_experiment)
from lattice.robustness import jitter_experiment, operating_curve

OUT = Path(__file__).resolve().parents[1] / "data" / "output"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["# Null-model baseline report", ""]

    rec = recovery_rank_experiment()
    lines += [
        "## 1. Recovery-rank experiment (leave-one-out, both layers)",
        "",
        "Remove each known particle; rank its true cell among all candidate",
        "slots by proximity to remaining known structure (ascending novelty).",
        "Null: the true cell is a uniformly random candidate (percentile 0.5).",
        "",
        f"- evaluable ablations: **{rec['n']}** "
        f"(degenerate cells excluded; {rec['n_unrecovered']} unrecovered)",
        f"- mean proximity percentile: **{rec['mean_percentile']:.3f}** (null: 0.5)",
        f"- z = {rec['z']:.1f}, one-sided **p ≈ {rec['p_value']:.1e}**",
        "",
        "| particle | layer | percentile |",
        "|---|---|---|",
    ]
    for r in sorted(rec["results"], key=lambda r: r["percentile"]):
        lines.append(f"| {r['name']} | {r['layer']} | {r['percentile']:.3f} |")
    lines += [
        "",
        "Honest reading: pattern-fillers (quarks, leptons, multiplet members)",
        "rank in the top few percent; isolated states (photon, gluon, W) rank",
        "worse than chance — proximity ranking predicts *completions of "
        "existing structure*, not lone outliers.",
        "",
    ]

    perm = loocv_permutation_test()
    lines += [
        "## 2. LOOCV label-permutation test",
        "",
        f"- observed LOOCV accuracy: **{perm['observed']:.0%}**",
        f"- permuted labels (n=200): mean {perm['perm_mean']:.1%}, "
        f"max {perm['perm_max']:.1%}",
        f"- **p = {perm['p_value']:.4f}** (floor for 200 permutations)",
        "",
    ]

    lines += [
        "## 3. Mass predictions vs naive-mean null",
        "",
        "| tool | predicted | measured | rel. error | null (mean) error |",
        "|---|---|---|---|---|",
    ]
    for r in mass_prediction_vs_null():
        lines.append(
            f"| {r['tool']} | {r['predicted_mev']:,.0f} MeV "
            f"| {r['measured_mev']:,.0f} MeV | {r['rel_error']:.3%} "
            f"| {r['null_rel_error']:.0%} |")
    lines += [
        "",
        "Koide and GMO beat the naive baseline by 2–4 orders of magnitude;",
        "the quark ladder is wrong in MeV (~330%) but still far better than",
        "the mean-null in log space and lands the correct lattice band.",
        "",
    ]

    filt = filter_null_test()
    lines += ["## 4. Filter selectivity vs random-filter null", ""]
    for l in filt["layers"]:
        lines.append(
            f"- **{l['layer']}**: keep-rate {l['keep_rate']:.1%}, all "
            f"{l['n_knowns']} knowns pass; a random filter of equal "
            f"selectivity passes all knowns with p ≈ {l['p_random_filter']:.1e}")
    lines += ["", f"Caveat: {filt['caveat']}.", ""]

    lines += ["## 5. Jitter robustness (§10.4)", ""]
    for sigma, label in [(0.01, "measurement scale (σ=0.01 dex ≈ ±2.3%)"),
                         (0.1, "stress scale (σ=0.1 dex ≈ ±26%)")]:
        j = jitter_experiment(n_trials=50, sigma_dex=sigma, seed=42)
        lines += [
            f"**{label}**, 50 trials:",
            f"- LOOCV stays 100%: {j['loocv_stable_rate']:.0%} of trials",
            f"- Higgs / top / Ω⁻ cells recovered: "
            f"{j['higgs_recovery_rate']:.0%} / {j['top_recovery_rate']:.0%} / "
            f"{j['omega_recovery_rate']:.0%}",
            f"- GMO median rel. error {j['gmo_median_rel_error']:.1%} "
            f"(naive-mean null: {j['null_median_rel_error']:.1%})",
            "",
        ]
    lines += [
        "Finding: slot recovery is structurally robust even at ±26% mass",
        "noise, but GMO's *precision* advantage needs precision inputs —",
        "at stress scale extrapolation amplifies noise and the naive mean",
        "becomes competitive.",
        "",
    ]

    oc = operating_curve()
    lines += [
        "## 6. Operating curve / pre-registered decision rule (§10.5–10.6)",
        "",
        f"Rule: {oc['decision_rule']}. Scored on {oc['n_ablations']} ablations:",
        "",
        "| top k% | hits | recall | enrichment | binomial p |",
        "|---|---|---|---|---|",
    ]
    for r in oc["rows"]:
        lines.append(f"| {r['k']:.0%} | {r['hits']}/{oc['n_ablations']} "
                     f"| {r['recall']:.1%} | {r['enrichment']:.1f}× "
                     f"| {r['p_value']:.1e} |")
    lines += [
        "",
        "Reading: a search program that takes the top 10% of candidate cells",
        "by proximity captures the majority of true pattern-completions at",
        "~7× the null rate. The top-1% bar is strict in absolute recall but",
        "keeps ~7× enrichment.",
        "",
    ]

    report = "\n".join(lines)
    (OUT / "null_model_report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwritten to {OUT / 'null_model_report.md'}")


if __name__ == "__main__":
    main()
