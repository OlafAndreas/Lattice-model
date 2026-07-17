"""Failed-predictions audit corpus and scoring
(docs/failed-predictions-audit.md).

Measures the historical *precision* of lattice-style gap-prediction —
the complement of the recall measured by the ablation experiments.

Extrapolation classes (assigned from the prediction's basis, before
outcome lookup):
- "within":  fills a slot in an already-instantiated pattern (a multiplet
             or doublet with other members confirmed);
- "beyond":  posits a new copy of a pattern (new generation, new
             multiplet) or a new state category with no confirmed members.
"""

import math

# Citations are populated from the sourced literature; "TODO" entries fail
# the completeness test in tests/test_audit.py by design.
CORPUS = [
    # ---- confirmed, within-pattern
    dict(name="eta", status="confirmed", extrapolation="within",
         basis="eighth pseudoscalar of the meson octet",
         prediction_ref=("Gell-Mann, CTSL-20 (1961): 'χ⁰', I=0, Y=0, 0⁻, "
                         "'fairly low mass' [verified from the OSTI scan]; "
                         "Ne'eman, Nucl. Phys. 26, 222 (1961)"),
         outcome_ref=("Pevsner et al., Phys. Rev. Lett. 7, 421 (1961) [3π "
                      "resonance ~550 MeV]; 0⁻ established: Bastien et "
                      "al., Phys. Rev. Lett. 8, 114 (1962)"),
         group=None),
    dict(name="Omega-", status="confirmed", extrapolation="within",
         basis="decuplet corner, mass via GMO equal spacing",
         prediction_ref=("Gell-Mann, Proc. Int. Conf. High-Energy Nucl. "
                         "Phys., Geneva 1962 (CERN), p. 805: S=−3, I=0, "
                         "Q=−1, ~1685 MeV, metastable"),
         outcome_ref=("Barnes et al., Phys. Rev. Lett. 12, 204 (1964): "
                      "1686 ± 12 MeV, targeted search"),
         group=None),
    dict(name="charm", status="confirmed", extrapolation="within",
         basis="quark-lepton doublet symmetry (GIM completion)",
         prediction_ref=("Bjorken & Glashow, 'Elementary Particles and "
                         "SU(4)', Phys. Lett. 11, 255 (1964); GIM, Phys. "
                         "Rev. D 2, 1285 (1970); mass ~1.5 GeV: Gaillard & "
                         "Lee, Phys. Rev. D 10, 897 (1974)"),
         outcome_ref=("J/ψ: Aubert et al., Phys. Rev. Lett. 33, 1404 "
                      "(1974); Augustin et al., Phys. Rev. Lett. 33, 1406 "
                      "(1974)"),
         group=None),
    dict(name="top", status="confirmed", extrapolation="within",
         basis="weak-isospin partner of the b quark",
         prediction_ref=("Kobayashi & Maskawa, Prog. Theor. Phys. 49, 652 "
                         "(1973); topless models excluded: Kane & Peskin, "
                         "Nucl. Phys. B 195, 29 (1982); EW-fit mass 162±9 "
                         "GeV: Ellis, Fogli & Lisi, Phys. Lett. B 333, 118 "
                         "(1994)"),
         outcome_ref=("CDF, Phys. Rev. Lett. 74, 2626 (1995); D0, Phys. "
                      "Rev. Lett. 74, 2632 (1995); m_t ≈ 176 GeV"),
         group=None),
    dict(name="nu_tau", status="confirmed", extrapolation="within",
         basis="lepton doublet partner of the tau",
         prediction_ref=("structural (doublet completion) after the tau: "
                         "Perl et al., Phys. Rev. Lett. 35, 1489 (1975); "
                         "no single dedicated prediction paper"),
         outcome_ref=("DONUT, Phys. Lett. B 504, 218 (2001); announced "
                      "2000"),
         notes="prediction attribution is structural, not one publication",
         group=None),
    dict(name="tau mass (Koide)", status="confirmed", extrapolation="within",
         basis="empirical mass relation over the charged-lepton triple",
         prediction_ref=("Koide, Lett. Nuovo Cimento 34, 201 (1982); "
                         "predicted m_τ = 1776.97 MeV vs then-accepted "
                         "~1784 MeV"),
         outcome_ref=("BES, Phys. Rev. Lett. 69, 3021 (1992): m_τ = 1776.9 "
                      "+0.4/−0.5 ± 0.2 MeV; PDG today 1776.86 ± 0.12"),
         notes=("empirical relation fit to (e, μ); numerological, not "
                "derived — but its τ output disagreed with data for a "
                "decade before being vindicated"),
         group=None),
    dict(name="Xi_cc", status="confirmed", extrapolation="within",
         basis="SU(4) doubly-charmed baryon multiplet slot",
         prediction_ref=("De Rújula, Georgi & Glashow, Phys. Rev. D 12, "
                         "147 (1975): ccq at 3550–3760 MeV; sharpest "
                         "pre-discovery: Karliner & Rosner, Phys. Rev. D "
                         "90, 094007 (2014): 3627 ± 12 MeV"),
         outcome_ref=("LHCb, Phys. Rev. Lett. 119, 112001 (2017): "
                      "Ξcc⁺⁺ at 3621.40 ± 0.78 MeV"),
         notes=("SELEX's earlier Ξcc⁺ claim (2002, 3519 MeV) was never "
                "confirmed; LHCb 2017 is the accepted observation"),
         group=None),
    dict(name="Omega_b/Xi_b", status="confirmed", extrapolation="within",
         basis="bottom-baryon multiplet slots",
         prediction_ref=("Roncaglia, Lichtenberg & Predazzi, Phys. Rev. D "
                         "52, 1722 (1995): Ξ_b 5810 ± 40, Ω_b 6060 ± 50 "
                         "MeV"),
         outcome_ref=("Ξ_b: D0, Phys. Rev. Lett. 99, 052001 and CDF, 99, "
                      "052002 (2007); Ω_b: D0, Phys. Rev. Lett. 101, "
                      "232002 (2008) / CDF, Phys. Rev. D 80, 072003 "
                      "(2009); precision: LHCb, Phys. Rev. Lett. 110, "
                      "182001 (2013): 5795.8 / 6046.0 MeV"),
         notes=("D0's Ω_b mass (6165 MeV) was anomalous; CDF/LHCb values "
                "agree with the 1995 prediction"),
         group=None),
    # ---- refuted, beyond-pattern
    dict(name="Theta+(1540)", status="refuted", extrapolation="beyond",
         basis="apex of a new baryon antidecuplet (S=+1, ~1530 MeV, narrow)",
         prediction_ref=("Diakonov, Petrov & Polyakov, Z. Phys. A 359, 305 "
                         "(1997); claim: Nakano et al. (LEPS), Phys. Rev. "
                         "Lett. 91, 012002 (2003)"),
         outcome_ref=("CLAS high-statistics nulls: Battaglieri et al., Phys. "
                      "Rev. Lett. 96, 042001 (2006); McKinnon et al., Phys. "
                      "Rev. Lett. 96, 212001 (2006); PDG 2008 verdict "
                      "(Wohl, in Phys. Lett. B 667, 1): claimed pentaquarks "
                      "'do not exist'"),
         group="antidecuplet"),
    dict(name="Xi3/2--(1862)", status="refuted", extrapolation="beyond",
         basis="second slot of the same antidecuplet (S=-2, Q=-2)",
         prediction_ref=("antidecuplet slot of Diakonov et al. (1997) "
                         "[predicted ~2070 MeV]; claim: Alt et al. (NA49), "
                         "Phys. Rev. Lett. 92, 042003 (2004) at 1862 MeV"),
         outcome_ref=("nulls with far larger Ξ samples: HERA-B, Phys. Rev. "
                      "Lett. 93, 212003 (2004); WA89, Phys. Rev. C 70, "
                      "022201 (2004); COMPASS, Eur. Phys. J. C 41, 469 "
                      "(2005); delisted after PDG 2008"),
         notes=("NA49's 1862 MeV did not fit the antidecuplet's own ~2070 "
                "MeV prediction"),
         group="antidecuplet"),
    dict(name="sequential 4th generation", status="refuted",
         extrapolation="beyond",
         basis="new generation rung extrapolating the 3-generation pattern",
         prediction_ref=("representative review: Frampton, Hung & Sher, "
                         "Phys. Rept. 330, 263 (2000)"),
         outcome_ref=("excluded at 5.3σ (perturbative sequential SM4): "
                      "Eberhardt et al., Phys. Rev. Lett. 109, 241802 "
                      "(2012)"),
         group="gen4"),
    dict(name="free fractional-charge quarks", status="refuted",
         extrapolation="beyond",
         basis="isolable fractional charges implied by the naive quark model",
         prediction_ref=("Gell-Mann, Phys. Lett. 8, 214 (1964) [explicitly "
                         "hedged]; Zweig, CERN-TH-401/412 (1964)"),
         outcome_ref=("cumulative nulls: Lyons, Phys. Rept. 129, 225 (1985); "
                      "PDG Free Quark Searches (Phys. Rev. D 86, 010001, "
                      "2012): 'no evidence for free quarks … uncorroborated "
                      "events'"),
         notes=("contested inclusion: the original 'prediction' was hedged; "
                "see sensitivity variant"),
         group=None),
    # ---- open (excluded from precision)
    dict(name="glueballs", status="open", extrapolation="beyond",
         basis="gluon-only bound states from QCD self-coupling",
         prediction_ref=("Fritzsch & Gell-Mann, Proc. XVI ICHEP (Chicago "
                         "1972) Vol. 2, 135 [first speculation]; Fritzsch & "
                         "Minkowski, Nuovo Cimento A 30, 393 (1975)"),
         outcome_ref=("open: f0(1500)/f0(1710) mixing candidates; BESIII "
                      "X(2370) 0-+ candidate, Phys. Rev. Lett. 132, 181901 "
                      "(2024)"),
         group=None),
    dict(name="magnetic monopole", status="open", extrapolation="beyond",
         basis="charge quantization (Dirac)",
         prediction_ref="Dirac, Proc. R. Soc. Lond. A 133, 60 (1931)",
         outcome_ref=("open: MoEDAL excludes m ≤ 80 GeV for 2-45 Dirac "
                      "charges, Phys. Rev. Lett. 133, 071803 (2024)"),
         group=None),
    dict(name="axion", status="open", extrapolation="beyond",
         basis="Peccei-Quinn symmetry breaking",
         prediction_ref=("Peccei & Quinn, Phys. Rev. Lett. 38, 1440 (1977); "
                         "Weinberg, Phys. Rev. Lett. 40, 223 (1978); "
                         "Wilczek, Phys. Rev. Lett. 40, 279 (1978)"),
         outcome_ref=("open: ADMX excludes DFSZ 3.27-3.34 µeV, Phys. Rev. "
                      "Lett. 134, 111002 (2025); most of the band untested"),
         group=None),
    dict(name="superpartners (naturalness window)", status="open",
         extrapolation="beyond",
         basis="doubling of the spectrum with spin shifted by 1/2",
         prediction_ref="Barbieri & Giudice, Nucl. Phys. B 306, 63 (1988)",
         outcome_ref=("open/eroded: Run-2 limits gluino ~2.4 TeV, stop "
                      "~1.25 TeV (arXiv:2506.06839); Δ≤10 colored window "
                      "excluded"),
         group=None),
]


# Blind second-rater labels (independent pass, 2026-07-17): the rater saw
# only the redacted prediction texts and the pre-registered criteria — no
# statuses, outcomes, or first-rater labels. Caveat: like any expert rater,
# not blind to world knowledge of famous outcomes.
RATER2 = {
    "eta": dict(in_class=True, extrapolation="within"),
    "Omega-": dict(in_class=True, extrapolation="within"),
    "charm": dict(in_class=True, extrapolation="within"),
    "top": dict(in_class=True, extrapolation="within"),
    "nu_tau": dict(in_class=True, extrapolation="within"),
    "tau mass (Koide)": dict(in_class=True, extrapolation="within"),
    "Xi_cc": dict(in_class=True, extrapolation="within"),
    "Omega_b/Xi_b": dict(in_class=True, extrapolation="within"),
    "Theta+(1540)": dict(in_class=False, extrapolation="beyond"),
    "Xi3/2--(1862)": dict(in_class=False, extrapolation="beyond"),
    "sequential 4th generation": dict(in_class=True, extrapolation="beyond"),
    "free fractional-charge quarks": dict(in_class=False,
                                          extrapolation="beyond"),
    "glueballs": dict(in_class=False, extrapolation="beyond"),
    "magnetic monopole": dict(in_class=False, extrapolation="beyond"),
    "axion": dict(in_class=False, extrapolation="beyond"),
    "superpartners (naturalness window)": dict(in_class=False,
                                               extrapolation="beyond"),
}


def inter_rater_stats() -> dict:
    """Agreement between the first rater (CORPUS labels; everything
    in-class by construction) and the blind second rater."""
    n = len(CORPUS)
    ext_agree = sum(RATER2[e["name"]]["extrapolation"] == e["extrapolation"]
                    for e in CORPUS)
    # Cohen's kappa for extrapolation (both raters have variance here)
    p_o = ext_agree / n
    p1_within = sum(e["extrapolation"] == "within" for e in CORPUS) / n
    p2_within = sum(v["extrapolation"] == "within"
                    for v in RATER2.values()) / n
    p_e = p1_within * p2_within + (1 - p1_within) * (1 - p2_within)
    ext_kappa = (p_o - p_e) / (1 - p_e)

    in_agree = sum(RATER2[e["name"]]["in_class"] for e in CORPUS)
    disagreements = [e["name"] for e in CORPUS
                     if not RATER2[e["name"]]["in_class"]]

    # strict (rater-2) corpus: closed in-class predictions only
    strict_closed = [e for e in CORPUS
                     if RATER2[e["name"]]["in_class"]
                     and e["status"] != "open"]
    strict_confirmed = sum(e["status"] == "confirmed" for e in strict_closed)
    strict_beyond = [e for e in strict_closed
                     if e["extrapolation"] == "beyond"]

    closed = [e for e in CORPUS if e["status"] != "open"]
    beyond = [e for e in closed if e["extrapolation"] == "beyond"]

    return {
        "extrapolation_agreement": ext_agree / n,
        "extrapolation_kappa": ext_kappa,
        "in_class_agreement": in_agree / n,
        "in_class_kappa_degenerate": True,  # rater 1 has zero variance
        "in_class_disagreements": disagreements,
        "strict_n_closed": len(strict_closed),
        "strict_precision": strict_confirmed / len(strict_closed),
        "strict_wilson_95": wilson_interval(strict_confirmed,
                                            len(strict_closed)),
        "fisher_inclusive": 1 / math.comb(len(closed), len(beyond)),
        "fisher_strict": 1 / math.comb(len(strict_closed),
                                       len(strict_beyond)),
    }


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def precision_summary(corpus: list | None = None) -> dict:
    corpus = CORPUS if corpus is None else corpus
    confirmed = sum(e["status"] == "confirmed" for e in corpus)
    refuted = sum(e["status"] == "refuted" for e in corpus)
    n_open = sum(e["status"] == "open" for e in corpus)
    n_closed = confirmed + refuted
    return {
        "n_confirmed": confirmed, "n_refuted": refuted,
        "n_closed": n_closed, "n_open": n_open,
        "precision": confirmed / n_closed if n_closed else float("nan"),
        "wilson_95": wilson_interval(confirmed, n_closed),
    }


def sensitivity_analysis() -> list[dict]:
    """Recompute precision under the contested grouping choices flagged in
    the audit design §5."""
    variants = []

    base = precision_summary()
    variants.append({"description": "baseline: one entry per prediction "
                                    "program", **base})

    # 4th generation counted as four predicted species (t', b', L, nu4)
    expanded = [e for e in CORPUS]
    for extra in ("gen4:b'", "gen4:L-", "gen4:nu4"):
        expanded.append(dict(name=extra, status="refuted",
                             extrapolation="beyond", basis="gen4 species",
                             prediction_ref="-", outcome_ref="-",
                             group="gen4"))
    variants.append({"description": "4th generation counted as four "
                                    "species", **precision_summary(expanded)})

    # antidecuplet counted as a single program
    merged = [e for e in CORPUS
              if not (e["group"] == "antidecuplet"
                      and e["name"] != "Theta+(1540)")]
    variants.append({"description": "antidecuplet counted as one program",
                     **precision_summary(merged)})

    # free quarks excluded (Gell-Mann's original text hedged the prediction)
    no_fq = [e for e in CORPUS if e["name"] != "free fractional-charge quarks"]
    variants.append({"description": "free quarks excluded (hedged original "
                                    "prediction)", **precision_summary(no_fq)})

    return variants
