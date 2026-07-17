"""PCA projection of the v1 OptionSet feature space: known particles colored
by emergent family, over the theory-filtered candidate cloud (gray).

Regenerates the `particles_pca_no_sm.png` artifact (MODEL_DESIGN.md §12).
Palette: dataviz reference categorical slots 1-5 (validated, light mode).
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lattice.features import V1_FEATURES
from lattice.model import N_FAMILIES, fit_families
from lattice.pipeline import run_v1

OUT = Path(__file__).resolve().parents[1] / "data" / "output"

SURFACE = "#fcfcfb"
INK = "#262625"
INK_SECONDARY = "#6b6a63"
GRID = "#e5e5e0"
CANDIDATE_GRAY = "#b8b7ae"
SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a"]

FAMILY_LABELS = {
    frozenset({"up", "down", "charm", "strange", "top", "bottom"}):
        "quark-like (strong+EM+weak)",
    frozenset({"electron", "muon", "tau", "W"}):
        "charged, EM+weak",
    frozenset({"nu_e", "nu_mu", "nu_tau"}):
        "weak-only neutral",
    frozenset({"photon", "gluon"}):
        "massless gauge",
    frozenset({"Z", "higgs"}):
        "neutral heavy, short-lived",
}

PRETTY = {"nu_e": "ν(e,μ,τ)", "nu_mu": None, "nu_tau": None,
          "electron": "electron", "muon": "muon", "tau": "tau",
          "up": "up", "down": "down", "charm": "charm", "strange": "strange",
          "top": "top", "bottom": "bottom", "photon": "photon",
          "gluon": "gluon", "W": "W", "Z": "Z", "higgs": "Higgs"}


def main() -> None:
    result = run_v1()
    known = result["known"]
    X = known[V1_FEATURES]
    families = fit_families(X)

    scaler = MinMaxScaler().fit(X)
    pca = PCA(n_components=2, random_state=42).fit(scaler.transform(X))
    P = pca.transform(scaler.transform(X))
    C = pca.transform(scaler.transform(result["candidates"][V1_FEATURES]))

    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ax.scatter(C[:, 0], C[:, 1], s=8, c=CANDIDATE_GRAY, alpha=0.25,
               linewidths=0, zorder=1,
               label=f"empty candidate slots (n={len(C)})")

    fam_names = {f: [n for n, ff in zip(known["name"], families) if ff == f]
                 for f in range(N_FAMILIES)}
    for f in range(N_FAMILIES):
        members = frozenset(fam_names[f])
        label = FAMILY_LABELS.get(members, ", ".join(sorted(members)))
        idx = [i for i, ff in enumerate(families) if ff == f]
        ax.scatter(P[idx, 0], P[idx, 1], s=110, c=SERIES[f],
                   edgecolors=SURFACE, linewidths=2, zorder=3, label=label)

    for i, name in enumerate(known["name"]):
        text = PRETTY.get(name, name)
        if text is None:
            continue
        ax.annotate(text, (P[i, 0], P[i, 1]), xytext=(7, 5),
                    textcoords="offset points", fontsize=8.5,
                    color=INK, zorder=4)

    ax.set_title("Known particles in OptionSet space (PCA, no SM labels)",
                 color=INK, fontsize=13, loc="left", pad=12)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%} var)",
                  color=INK_SECONDARY, fontsize=9)
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%} var)",
                  color=INK_SECONDARY, fontsize=9)
    ax.tick_params(colors=INK_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

    legend = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0),
                       frameon=False, fontsize=8.5, labelcolor=INK)
    fig.tight_layout()

    out = OUT / "particles_pca_no_sm.png"
    fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
