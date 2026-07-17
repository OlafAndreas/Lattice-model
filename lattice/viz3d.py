"""Data builder for the 3D voxel lattice visualization.

Exports the v2 emergent lattice as plain dicts ready for JSON embedding:
occupied cells (grouped known particles, colored by their v1 emergent
family) and allowed-but-empty cells (with novelty score and nearest known).
"""

import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler

from .enumeration import enumerate_grid_v2
from .features import (V1_FEATURES, V2_FEATURES, encode_hadrons, encode_v1,
                       encode_v2)
from .filters import theory_filter_v2
from .generations import gen4_predictions
from .hadrons import known_hadrons
from .model import N_FAMILIES, fit_families, novelty_scores
from .particles import known_particles
from .pipeline import GRAVITON_CELL, run_hadrons

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

PRETTY = {"up": "u", "down": "d", "charm": "c", "strange": "s", "top": "t",
          "bottom": "b", "electron": "e⁻", "muon": "μ⁻", "tau": "τ⁻",
          "nu_e": "νe", "nu_mu": "νμ", "nu_tau": "ντ", "photon": "γ",
          "gluon": "g", "W": "W±", "Z": "Z⁰", "higgs": "H⁰"}

PRETTY_HADRON = {
    "p": "p", "n": "n", "Lambda": "Λ", "Sigma+": "Σ⁺", "Sigma0": "Σ⁰",
    "Sigma-": "Σ⁻", "Xi0": "Ξ⁰", "Xi-": "Ξ⁻", "Delta++": "Δ⁺⁺",
    "Delta+": "Δ⁺", "Delta0": "Δ⁰", "Delta-": "Δ⁻", "Sigma*+": "Σ*⁺",
    "Sigma*0": "Σ*⁰", "Sigma*-": "Σ*⁻", "Xi*0": "Ξ*⁰", "Xi*-": "Ξ*⁻",
    "Omega-": "Ω⁻", "pi+": "π⁺", "pi0": "π⁰", "K+": "K⁺", "K0": "K⁰",
    "eta": "η", "eta'": "η′", "rho+": "ρ⁺", "rho0": "ρ⁰", "K*+": "K*⁺",
    "K*0": "K*⁰", "omega": "ω", "phi": "φ", "D+": "D⁺", "D0": "D⁰",
    "Ds+": "Ds⁺", "eta_c": "ηc", "J/psi": "J/ψ", "B+": "B⁺", "B0": "B⁰",
    "Bs0": "Bs⁰", "Upsilon": "Υ", "Lambda_c+": "Λc⁺", "Lambda_b0": "Λb⁰",
    "Xi_cc++": "Ξcc⁺⁺"}

MULTIPLETS = ["octet", "decuplet", "pseudoscalar", "vector", "heavy"]
MULTIPLET_LABELS = ["baryon octet (½⁺)", "baryon decuplet (3/2⁺)",
                    "pseudoscalar mesons (0⁻)", "vector mesons (1⁻)",
                    "heavy-flavor states"]


def _flavor_note(row) -> str:
    parts = []
    if row["strangeness"]: parts.append(f"S={row['strangeness']:+d}")
    if row["charm"]: parts.append(f"C={row['charm']:+d}")
    if row["beauty"]: parts.append(f"B̃={row['beauty']:+d}")
    return " ".join(parts) if parts else "no open flavor"


def build_lattice3d_data() -> dict:
    particles = known_particles()
    v1 = encode_v1(particles)
    v2 = encode_v2(particles)

    # Emergent family per particle (same clustering as the PCA plot), then
    # renumber so family index order is stable across runs.
    raw_fams = fit_families(v1[V1_FEATURES])
    members = {f: frozenset(v1["name"][raw_fams == f]) for f in set(raw_fams)}
    ordered = sorted(members, key=lambda f: sorted(members[f])[0])
    fam_index = {f: i for i, f in enumerate(ordered)}
    name_fam = {n: fam_index[f] for n, f in zip(v1["name"], raw_fams)}
    family_labels = [FAMILY_LABELS.get(members[f], ", ".join(sorted(members[f])))
                     for f in ordered]

    knowns = []
    for cell, group in v2.groupby(V2_FEATURES):
        spin, q, _, m, st = cell
        names = list(group["name"])
        knowns.append({
            "spin": float(spin), "q": int(q), "m": int(m), "st": int(st),
            "occupants": [PRETTY[n] for n in names],
            "fullnames": names,
            "fam": name_fam[names[0]],
        })

    grid = theory_filter_v2(enumerate_grid_v2())
    merged = grid.merge(v2[V2_FEATURES].drop_duplicates(), on=V2_FEATURES,
                        how="left", indicator=True)
    empty = merged[merged["_merge"] == "left_only"][V2_FEATURES].reset_index(drop=True)

    scaler = MinMaxScaler().fit(v2[V2_FEATURES])
    nn = NearestNeighbors(n_neighbors=1).fit(scaler.transform(v2[V2_FEATURES]))
    _, nearest_idx = nn.kneighbors(scaler.transform(empty))
    novelty = novelty_scores(v2[V2_FEATURES], empty)

    grav = pd.Series(GRAVITON_CELL)
    empties = []
    for i, row in empty.iterrows():
        e = {
            "spin": float(row["spin"]), "q": int(row["charge_1_3"]),
            "m": int(row["logMass"]), "st": int(row["stable_band"]),
            "nov": round(float(novelty[i]), 4),
            "near": str(v2["name"].iloc[nearest_idx[i, 0]]),
        }
        if (row[V2_FEATURES] == grav[V2_FEATURES]).all():
            e["graviton"] = True
        empties.append(e)

    hadron_knowns, hadron_empties, h_max, planes = _hadron_layer()

    gen4 = []
    for p in gen4_predictions():
        gen4.append({
            "label": p["label"], "spin": p["spin"], "q": p["q"],
            "st": p["st"], "m": min(p["band"], 6), "band_true": p["band"],
            "mass_mev": round(p["mass_mev"]), "method": p["method"],
            "head": "predicted 4th-generation cell",
        })

    from .constituent import forward_predictions
    PRED_LABEL = {"Xi_bb": "Ξbb", "Omega_bb": "Ωbb", "Xi_bc": "Ξbc",
                  "Omega_bc": "Ωbc", "Xi_cc+": "Ξcc⁺", "Omega_ccc": "Ωccc",
                  "Omega_bbb": "Ωbbb", "Omega_cc+ (validation)": "Ωcc✓"}
    hadron_preds = []
    for p in forward_predictions():
        for q in p["q_states"]:
            hadron_preds.append({
                "label": PRED_LABEL[p["name"]], "spin": p["spin"], "q": q,
                "st": 0, "m": p["band"], "band_true": p["band"],
                "mass_mev": p["mass_mev"],
                "method": (f"additive constituent fit ± "
                           f"{p['uncertainty_mev']} MeV — {p['note']}"),
                "head": ("out-of-sample validation (observed)"
                         if "validation" in p["name"]
                         else "registered forward prediction"),
            })

    return {
        "gen4": gen4,
        "hadron_preds": hadron_preds,
        "knowns": knowns,
        "empties": empties,
        "family_labels": family_labels,
        "max_novelty": round(float(novelty.max()), 4),
        "hadrons": hadron_knowns,
        "hadron_empties": hadron_empties,
        "hadron_max_novelty": h_max,
        "multiplet_labels": MULTIPLET_LABELS,
        "planes": planes,
    }


CELL_AXES = ["spin", "charge_1_3", "logMass", "stable_band"]


def _hadron_layer():
    raw = known_hadrons()
    enc = encode_hadrons(raw).merge(raw[["name", "multiplet", "mass_mev"]],
                                    on="name")

    knowns = []
    for cell, group in enc.groupby(CELL_AXES):
        spin, q, m, st = cell
        knowns.append({
            "spin": float(spin), "q": int(q), "m": int(m), "st": int(st),
            "occupants": [PRETTY_HADRON[n] for n in group["name"]],
            "details": [f"{PRETTY_HADRON[r['name']]} · {_flavor_note(r)}"
                        for _, r in group.iterrows()],
            "mult": MULTIPLETS.index(group["multiplet"].iloc[0]),
        })

    result = run_hadrons()
    c = result["candidates"]
    empties = []
    for cell, group in c.groupby(CELL_AXES):
        spin, q, m, st = cell
        top = group.loc[group["novelty"].idxmax()]
        empties.append({
            "spin": float(spin), "q": int(q), "m": int(m), "st": int(st),
            "count": int(len(group)),
            "nov": round(float(top["novelty"]), 4),
            "near": str(top_nearest(result, top)),
        })
    planes = _multiplet_planes(enc, result)
    return knowns, empties, round(float(c["novelty"].max()), 4), planes


PANEL_AXES = ["baryon", "spin", "charm", "beauty"]


def _multiplet_planes(enc, result) -> list:
    """Eightfold-way panels: one per (baryon, spin, charm, beauty) class,
    with cells on the charge × strangeness plane. Cells carry the known
    occupants and the allowed-but-unseen (mass band, stability) variants."""
    c = result["candidates"]

    cells = {}
    def cell(b, spin, ch, bt, s, q):
        key = (int(b), float(spin), int(ch), int(bt), int(s), int(q))
        return cells.setdefault(key, {"S": int(s), "q": int(q),
                                      "knowns": [], "slots": []})

    for _, r in enc.iterrows():
        cell(r["baryon"], r["spin"], r["charm"], r["beauty"],
             r["strangeness"], r["charge_1_3"])["knowns"].append({
            "label": PRETTY_HADRON[r["name"]],
            "mult": MULTIPLETS.index(r["multiplet"]),
            "m": int(r["logMass"]), "st": int(r["stable_band"]),
        })
    for _, r in c.iterrows():
        cell(r["baryon"], r["spin"], r["charm"], r["beauty"],
             r["strangeness"], r["charge_1_3"])["slots"].append({
            "m": int(r["logMass"]), "st": int(r["stable_band"]),
            "nov": round(float(r["novelty"]), 4),
            "near": top_nearest(result, r),
        })

    panels = {}
    for (b, spin, ch, bt, s, q), data in cells.items():
        panels.setdefault((b, spin, ch, bt), []).append(data)

    def title(b, spin, ch, bt):
        kind = "Baryons" if b else "Mesons"
        spin_lbl = {0.0: "0", 0.5: "½", 1.0: "1", 1.5: "3/2"}[spin]
        flavor = []
        if ch: flavor.append(f"C={ch:+d}")
        if bt: flavor.append(f"B̃={bt:+d}")
        return f"{kind} · spin {spin_lbl}" + (" · " + " ".join(flavor) if flavor else "")

    from .gmo import fit_mass_vs_strangeness, predict_mass

    out = []
    for (b, spin, ch, bt), cell_list in sorted(
            panels.items(),
            key=lambda kv: (-sum(len(c["knowns"]) for c in kv[1]),
                            kv[0][0], kv[0][1])):
        members = enc[(enc["baryon"] == b) & (enc["spin"] == spin)
                      & (enc["charm"] == ch) & (enc["beauty"] == bt)]
        fit = fit_mass_vs_strangeness(members)
        if fit is not None:
            for cell in cell_list:
                if not cell["knowns"]:
                    cell["pm"] = round(predict_mass(fit, cell["S"]))
        out.append({
            "baryon": int(b), "spin": float(spin),
            "charm": int(ch), "beauty": int(bt),
            "title": title(b, spin, ch, bt),
            "cells": sorted(cell_list, key=lambda c: (-c["S"], c["q"])),
        })
    return out


def top_nearest(result, candidate_row) -> str:
    """Name of the known hadron nearest to one candidate row."""
    from .hadrons import HADRON_FEATURES
    from .model import nearest_known
    known = result["known"]
    q = candidate_row[HADRON_FEATURES].to_frame().T
    name = nearest_known(known[HADRON_FEATURES], known["name"], q, k=1)[0]
    return PRETTY_HADRON.get(name, name)
