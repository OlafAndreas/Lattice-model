"""Generate the four paper figures into data/output/ (light mode,
print-oriented; palette = validated dataviz reference)."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lattice.nullmodels import recovery_rank_experiment
from lattice.robustness import operating_curve
from lattice.viz3d import build_lattice3d_data

OUT = Path(__file__).resolve().parents[1] / "data" / "output"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#262625", "#6b6a63", "#e3e3dd"
GHOST = "#77766c"
SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a"]

DATA = build_lattice3d_data()
SPIN_SHELF = {0.0: 0, 0.5: 1, 1.0: 2, 1.5: 3, 2.0: 4}


def fig1_lattice3d():
    fig = plt.figure(figsize=(9, 6.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(SURFACE)

    for e in DATA["empties"]:
        a = 0.06 + 0.30 * e["nov"] / DATA["max_novelty"]
        ax.scatter(e["m"], e["q"] / 3, SPIN_SHELF[e["spin"]], s=5,
                   c=GHOST, alpha=a, linewidths=0)
    for k in DATA["knowns"]:
        ax.scatter(k["m"], k["q"] / 3, SPIN_SHELF[k["spin"]], s=90,
                   c=SERIES[k["fam"]], edgecolors=SURFACE, linewidths=1.2,
                   zorder=5)
        ax.text(k["m"] + 0.25, k["q"] / 3, SPIN_SHELF[k["spin"]] + 0.16,
                " ".join(k["occupants"]), fontsize=6.5, color=INK)
    grav = next(e for e in DATA["empties"] if e.get("graviton"))
    ax.scatter(grav["m"], grav["q"] / 3, SPIN_SHELF[grav["spin"]], s=160,
               marker="*", facecolors="none", edgecolors=INK,
               linewidths=1.2, zorder=6)
    ax.text(grav["m"] + 0.3, grav["q"] / 3, SPIN_SHELF[grav["spin"]] + 0.2,
            "graviton?", fontsize=7, color=INK, style="italic")

    ax.set_xlabel("log₁₀(mass/MeV) band", fontsize=8, color=INK2)
    ax.set_ylabel("charge (e)", fontsize=8, color=INK2)
    ax.set_zticks([0, 1, 2, 3, 4])
    ax.set_zticklabels(["0", "½", "1", "3/2", "2"], fontsize=7)
    ax.set_zlabel("spin", fontsize=8, color=INK2)
    ax.tick_params(labelsize=7, colors=INK2)
    ax.view_init(elev=16, azim=-58)
    ax.set_title("The 3D OptionSet lattice (fundamental layer, emergent v2 "
                 "encoding)\nsolid = known particles by emergent family · "
                 "gray = allowed-but-empty cells (darker = more novel)",
                 fontsize=9, color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_lattice3d.png", facecolor=SURFACE,
                bbox_inches="tight")
    plt.close(fig)


PANEL_KEYS = [(1, 1.5, 0, 0, "Baryon decuplet (3/2⁺)"),
              (1, 0.5, 0, 0, "Baryon octet (½⁺)"),
              (0, 0.0, 0, 0, "Pseudoscalar mesons (0⁻)"),
              (0, 1.0, 0, 0, "Vector mesons (1⁻)")]


def fig2_planes():
    fig, axes = plt.subplots(2, 2, figsize=(9, 7), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    for ax, (b, spin, ch, bt, title) in zip(axes.flat, PANEL_KEYS):
        panel = next(p for p in DATA["planes"]
                     if (p["baryon"], p["spin"], p["charm"], p["beauty"])
                     == (b, spin, ch, bt))
        ax.set_facecolor(SURFACE)
        for c in panel["cells"]:
            x, y = c["q"] / 3, c["S"]
            if c["knowns"]:
                mult = c["knowns"][0]["mult"]
                ax.add_patch(plt.Rectangle((x - 0.42, y - 0.42), 0.84, 0.84,
                             facecolor=SERIES[mult], alpha=0.25,
                             edgecolor=SERIES[mult], linewidth=1.4))
                ax.text(x, y, "\n".join(k["label"] for k in c["knowns"]),
                        ha="center", va="center", fontsize=7.5, color=INK)
            elif c["slots"]:
                nov = max(s["nov"] for s in c["slots"])
                a = 0.10 + 0.4 * nov / DATA["hadron_max_novelty"]
                ax.add_patch(plt.Rectangle((x - 0.42, y - 0.42), 0.84, 0.84,
                             facecolor=GHOST, alpha=a, edgecolor="none"))
        qs = sorted({c["q"] / 3 for c in panel["cells"]})
        Ss = sorted({c["S"] for c in panel["cells"]})
        ax.set_xlim(min(qs) - 0.7, max(qs) + 0.7)
        ax.set_ylim(min(Ss) - 0.7, max(Ss) + 0.7)
        ax.set_xticks(qs)
        ax.set_yticks(Ss)
        ax.set_xlabel("charge (e)", fontsize=8, color=INK2)
        ax.set_ylabel("strangeness", fontsize=8, color=INK2)
        ax.set_title(title, fontsize=9.5, color=INK)
        ax.tick_params(labelsize=7.5, colors=INK2)
        for s in ax.spines.values():
            s.set_color(GRID)
    fig.suptitle("Eightfold-way multiplet planes: knowns (colored) and "
                 "allowed-but-empty cells (gray, darker = more novel)",
                 fontsize=10, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT / "fig2_planes.png", facecolor=SURFACE,
                bbox_inches="tight")
    plt.close(fig)


def fig3_recovery():
    rec = recovery_rank_experiment()
    fig, ax = plt.subplots(figsize=(9, 3.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    rng = np.random.default_rng(3)
    for i, layer in enumerate(("fundamental", "hadron")):
        pts = [r for r in rec["results"] if r["layer"] == layer]
        ys = i + rng.uniform(-0.16, 0.16, len(pts))
        ax.scatter([p["percentile"] for p in pts], ys, s=42,
                   c=SERIES[0] if i == 0 else SERIES[4],
                   edgecolors=SURFACE, linewidths=0.8, zorder=3)
        for p, y in zip(pts, ys):
            if p["percentile"] > 0.45 or p["name"] in ("top", "Omega-"):
                ax.annotate(p["name"], (p["percentile"], y), xytext=(4, 5),
                            textcoords="offset points", fontsize=7,
                            color=INK2)
    ax.axvline(0.5, color=INK2, linewidth=1, linestyle="--")
    ax.text(0.502, 1.42, "null expectation (0.5)", fontsize=7.5, color=INK2)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["fundamental", "hadron"], fontsize=9)
    ax.set_xlabel("proximity percentile of the true cell "
                  "(0 = closest to known structure)", fontsize=8.5,
                  color=INK2)
    ax.set_xlim(-0.02, 1.0)
    ax.set_title(f"Leave-one-out recovery ranks — {rec['n']} ablations, "
                 f"mean {rec['mean_percentile']:.3f}, p ≈ "
                 f"{rec['p_value']:.0e}", fontsize=9.5, color=INK)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_color(GRID)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_recovery.png", facecolor=SURFACE,
                bbox_inches="tight")
    plt.close(fig)


def fig4_operating_curve():
    oc = operating_curve(ks=(0.01, 0.02, 0.05, 0.10, 0.15, 0.25, 0.5))
    fig, ax = plt.subplots(figsize=(6.4, 4.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ks = [r["k"] for r in oc["rows"]]
    recalls = [r["recall"] for r in oc["rows"]]
    ax.plot([0, 0.55], [0, 0.55], color=INK2, linewidth=1, linestyle="--")
    ax.text(0.38, 0.33, "null (recall = k)", fontsize=8, color=INK2,
            rotation=38)
    ax.plot(ks, recalls, color=SERIES[0], linewidth=2, marker="o",
            markersize=7, markeredgecolor=SURFACE, zorder=3)
    for r in oc["rows"]:
        if r["k"] in (0.05, 0.10, 0.25):
            ax.annotate(f"{r['enrichment']:.1f}×",
                        (r["k"], r["recall"]), xytext=(6, -11),
                        textcoords="offset points", fontsize=8, color=INK)
    ax.set_xlabel("candidate fraction searched (top k% by proximity)",
                  fontsize=8.5, color=INK2)
    ax.set_ylabel("recall of true cells", fontsize=8.5, color=INK2)
    ax.set_title(f"Operating curve over {oc['n_ablations']} ablations "
                 "(labels = enrichment vs null)", fontsize=9.5, color=INK)
    ax.set_xlim(0, 0.55)
    ax.set_ylim(0, 0.9)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_color(GRID)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_operating_curve.png", facecolor=SURFACE,
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig1_lattice3d()
    fig2_planes()
    fig3_recovery()
    fig4_operating_curve()
    print("wrote fig1–fig4 to", OUT)
