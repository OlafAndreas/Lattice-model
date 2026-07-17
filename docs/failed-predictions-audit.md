# Failed-Predictions Audit — Design

Companion to `PAPER_DRAFT.md` §5.4/§6.5. Status: **executed 2026-07-17** —
all 16 corpus entries sourced to original publications and resolving
evidence (see `lattice/audit.py` for the citations, `scripts/run_audit.py`
→ `data/output/audit_report.md` for the results: precision 8/12 = 67%,
Wilson 95% [39%, 86%], sensitivity 53–73%; within-pattern 8/8 confirmed vs
beyond-pattern 0/4). **Blind two-rater pass executed 2026-07-17**
(`RATER2` in `lattice/audit.py`): within/beyond labels 16/16 agreement
(κ = 1.0); in-class 9/16 (rater 2 stricter); precision reported as the
rater range 67–89%. Residual caveat: no rater can be blind to world
knowledge of famous outcomes — the blindness achieved is to the scoring
and the other rater's labels.

## 1. Motivation

The paper's ablation experiments measure **recall**: given a particle that
*was* discovered, how highly would the lattice have ranked its cell? This is
computed over history's successes, so it cannot answer the complementary
question a skeptic must ask — **precision**: of all the lattice-style
gap-predictions physicists actually made, what fraction came true? Counting
only Ω⁻ and τ is survivor bias. This audit designs the correction.

## 2. Inclusion criteria (pre-registered before scoring)

A historical prediction is **in-class** iff all of:

1. **Lattice-style inference** — derived from completing a symmetry
   multiplet, quantum-number pattern, or empirical mass regularity; *not*
   from dynamics (anomaly fits, naturalness arguments, resonance bumps).
2. **Cell specified** — explicit quantum numbers (spin, charge, flavor
   content) plus at least a coarse mass window, published *before* any
   claimed observation.
3. **Falsifiable window closed or closable** — enough experimental reach
   has since existed to confirm or refute the specific claim.

Explicitly **out-of-class** (do not count for or against): the 750 GeV
diphoton episode (a statistical fluctuation, not a prediction); the 17 keV
neutrino (an experimental artifact); W/Z mass predictions (gauge dynamics);
the positron (relativistic dynamics); resonance claims without a prior
prediction (X(5568)).

## 3. Candidate corpus (to be sourced, then scored blind)

### Likely CONFIRMED, in-class
| prediction | predicted → found | basis |
|---|---|---|
| η meson | 1961 → 1961 | pseudoscalar octet completion |
| Ω⁻ | 1962 → 1964 | decuplet corner + GMO mass |
| charm quark | 1964/1970 → 1974 | quark–lepton pattern completion (GIM) |
| top quark | 1977 → 1995 | third-generation doublet completion |
| ν_τ | 1975 → 2000 | lepton doublet completion |
| τ mass (Koide) | 1982 → confirmed | empirical mass regularity |
| Ξ_cc, Ω_b, Ξ_b … | 1970s → 2007–2017 | SU(4)/heavy-quark multiplet slots |

### Likely REFUTED, in-class
| prediction | predicted → status | basis |
|---|---|---|
| sequential 4th generation (t′, b′, ℓ₄, ν₄) | 1970s–2000s → excluded 2012 | generation-pattern extrapolation — the canonical in-class failure |
| Θ⁺(1540) pentaquark | 1997 → claims 2003, refuted ~2006–08 | antidecuplet completion (chiral soliton) |
| other antidecuplet members (Ξ₃/₂⁻⁻ etc.) | 1997 → unconfirmed | same multiplet |
| free fractional-charge quarks | 1964 → never seen | naive quark-model cell; failure reshaped theory (confinement) |

### OPEN, in-class (excluded from precision; reported separately)
| prediction | since | status |
|---|---|---|
| glueballs | ~1975 | candidates only, unconfirmed |
| magnetic monopole | 1931 | open |
| axion | 1977 | open, window shrinking |
| SUSY partners (naturalness windows) | 1980s | windows eroded, formally open |

## 4. Scoring protocol

1. **Source each entry**: original publication, the predicted cell
   (quantum numbers + mass window), and the resolving experiment(s).
2. **Blind scoring**: two raters apply the §2 criteria to the *prediction
   text only* (outcome redacted) to decide in/out-of-class; disagreements
   documented, resolved by the pre-registered wording. Only then is the
   outcome attached.
3. Each closed in-class entry → `confirmed` or `refuted`; open entries are
   reported but excluded from the headline precision.

## 5. Statistical plan

- **Headline**: precision = confirmed / (confirmed + refuted) over closed
  in-class predictions, with a Wilson 95% interval (the corpus will be
  small — likely n ≈ 10–15 — so the interval matters more than the point).
- **Sensitivity**: recompute under every contested inclusion decision
  (e.g., counting the whole 4th-generation program as one failure vs. four;
  counting each antidecuplet member separately). Report the range, not the
  most favorable value.
- **Synthesis with the recall results**: the paper then reports the method's
  two operating characteristics side by side — recall ≈ 64–71% at the
  5–10% proximity threshold (measured by ablation), precision ≈ the audit
  value (measured by history) — and explicitly notes they come from
  different populations and eras.

## 6. Expected outcome and honest framing

A plausible reading of the candidate corpus is precision in the region of
50–70% with a wide interval: the method's famous successes are roughly
balanced by the 4th-generation program and the antidecuplet. If so, the
paper's claim sharpens usefully: lattice-gap inference is a *good
prioritizer* (large enrichment) but a *mediocre oracle* (precision far from
1), and the failures cluster exactly where §5.4 predicts — extrapolating
*beyond* the pattern (4th generation = a new rung, antidecuplet = a new
multiplet) rather than completing *within* it (Ω⁻, top, ν_τ). That
within/beyond distinction is testable on the corpus and, if it holds, is a
second original finding.

## 7. Effort estimate

Sourcing ~20 entries via INSPIRE/ADS and review articles: roughly 2–4
part-time weeks. The blind two-rater protocol needs a second person (or a
strictly separated second pass) to be credible.
