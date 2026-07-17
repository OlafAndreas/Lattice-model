# LatticeModel — Model Design

Distilled from the originating ChatGPT conversation ("Explain quantum physics",
share link `chatgpt.com/share/6a5938ba-d2a8-83eb-ac27-7bcdcfb1a882`).

> **Status note:** All numeric results below (accuracy, slot counts, backtest outcomes)
> are *claims from the ChatGPT session*, produced in a sandbox that has since been
> wiped. None of the code or data survived — everything must be rebuilt and
> re-verified before any result is treated as real.

---

## 1. Core idea

Treat every fundamental particle as a coordinate in a discrete feature space of
**measurable, model-independent properties** (the "OptionSet"). Known particles
occupy some cells of this lattice; cells that are *valid under learned constraints
but unoccupied* are candidate slots for undiscovered particles.

The model is explicitly a **slot finder, not a theory**: it does not compute
couplings, cross-sections, or decay widths, and it does not derive mechanisms
(e.g., it can flag a Higgs-shaped hole without deriving symmetry breaking). Its
value is mapping the "particle possibility space" without Standard Model
category bias, then ranking empty slots as search targets.

## 2. Feature encoding (OptionSet)

### v1 features (interaction-flag lattice)

| Feature | Encoding | Notes |
|---|---|---|
| `spin_half` | 0 / 1 | Integer vs half-integer spin (parity only) |
| `charge_1_3` | integer | Electric charge in units of e/3 (e.g., +2 → Q = +2/3) |
| `has_charge` | 0 / 1 | Derived flag |
| `Strong`, `EM`, `Weak` | 0 / 1 each | Interaction signature flags |
| `logMass` | coarse band | log₁₀(mass/MeV), quantized to wide bins; −9 ≈ massless |
| `stable_band` | 0 / 1 | Short-lived vs stable/long-lived |

### v2 features (emergent-only lattice)

Motivated by the observation that interaction flags (and any `Gravity` flag)
hardcode the known forces back into the model. v2 strips the encoding to raw
observables only:

- **Exact quantized spin** ∈ {0, ½, 1, 2} — upgraded from parity because with
  parity alone the graviton coordinate collides with photon/gluon.
- `charge_1_3`, `has_charge`
- `logMass` band
- `stable_band`

No force flags at all; interaction groupings are expected to **emerge** as
clusters and can be labeled post-hoc. This keeps the model open to fifth-force /
dark-sector candidates that don't fit SM interaction categories.

### v0.2 additions (universal potential speed)

- `propagation_c` / `propagation_fraction`: 1.0 for effectively massless bands
  (`logMass ≤ −8.5`, i.e., excitations propagate at c), else 0.0 (conservative —
  no guessed velocities for massive states).
- `universal_potential_speed_mps = 299 792 458` — constant field encoding the
  reframing of c as the universe's speed limit for any massless propagation
  ("UPS"), not a light-specific property.

## 3. Pipeline

1. **Dataset** — table of known fundamental particles with the features above.
   (Planned upgrade: wire in real PDG data via the PDG SQLite download instead
   of a hand-built table.)
2. **Emergent families** — unsupervised clustering (k-means) over features; no
   SM labels (quark/lepton/boson) anywhere.
3. **Classifier** — 1-NN in feature space, trained only on the features;
   decision-tree rules extracted alongside as a human-readable "grammar".
4. **Enumeration** — generate the full grid of OptionSet combinations
   (spin × charge thirds × interaction flags × mass band × stability band).
5. **Filtering** — physical sanity checks (§4) remove implausible combinations.
6. **Gap analysis** — subtract cells matched by known particles; the remainder
   are *valid-but-unseen* candidate slots, each assigned to its nearest emergent
   family by the 1-NN model.
7. **Ranking** — score empty slots (§5) into a prioritized search list.

## 4. Theory / phenomenology filters (v1)

Applied to the enumerated grid — deliberately coarse, no SM categories:

- No **massless charged** states.
- **EM without charge** allowed only for photon-like states (neutral,
  integer-spin, no weak/strong).
- **Strong + half-integer spin** must be quark-like (must also couple to EM and
  weak).
- **Neutral, integer-spin, strong-only** allowed (gluon-like).
- Drop **long-lived heavy charged** states (CHAMPs — excluded by cosmology and
  direct searches).
- No **weak-only charged** states (EM coupling follows from charge).

## 5. Scoring functions

- **Novelty** — distance from the nearest known particle in feature space.
- **Discovery Potential Score (DPS)** — for ranking search briefs:
  `0.40·novelty + 0.40·experimental reach + 0.20·(1 − background difficulty)`.
- **score_v02** — after the UPS addition:
  `0.55·novelty + 0.35·measurability + 0.10·propagation_fraction`.

## 6. Claimed results (unverified — rebuild required)

- **Backtest accuracy:** 100% leave-one-out (LOOCV) classification of known
  fundamental particles with the 1-NN classifier.
- **Slot counts:** 1,437 raw valid-but-unseen OptionSets → **397** survive the
  theory filters. Survivor interaction profiles: EM-only 111, EM+weak 96,
  strong-only 63, strong+EM 48, strong+EM+weak 48, weak-only 31.
- **Estimates of undiscovered particles:** conservative ~150–250 promising
  slots, moderate ~250–350, upper bound 397. (Earlier data-only novelty tiers:
  287 / 434 / 621.)
- **Ablation backtests:**
  - *Higgs removed* → model surfaces a neutral, spin-0, short-lived slot in the
    ~10⁵ MeV band (requires allowing zero-gauge-interaction candidates in the
    enumeration, since the coarse encoding gives the Higgs no force flags).
  - *Top quark removed* → model surfaces a spin-½, Q = +2/3,
    strong+EM+weak slot in the ~10⁵ MeV band; novelty distance 1.89; nearest
    known neighbors charm/bottom and heavy bosons.
- **Graviton placement (v2, exact spin):** unique unoccupied cell at
  `(spin = 2, charge = 0, logMass ≈ −9, stable = 1)`; nearest known neighbors
  photon and gluon, then neutrinos. With spin-parity encoding only, this cell
  is indistinguishable from photon/gluon — the reason for the exact-spin
  upgrade.

## 7. Role inference layer

A post-hoc classification of slots by "what the universe might use the particle
for", derived from the feature profile:

| Role | Profile | Known examples |
|---|---|---|
| **Structural** | fermion, low mass, stable | electron, u/d quarks |
| **Force Carrier** | boson, spin 1, mediates one interaction | photon, gluon, W/Z |
| **Mass Setter / Symmetry Breaker** | scalar with specific couplings | Higgs |
| **Bridge** | heavy, unstable, connects families/sectors | top quark, heavy neutrinos |
| **Dark Participant** | neutral, stable-ish, weak or no interaction | neutrinos, WIMP-like |

Applied to the 397 survivors, **Bridge-type slots dominate the top-20** ranked
candidates — the model's structural claim is that the densest missing territory
is *connectors and portals*, not building blocks. Historically that's where the
major discoveries happened (W, top, Higgs).

## 8. Top-ranked candidate slots (DPS order, from the session)

| Rank | Slot | Profile | Role |
|---|---|---|---|
| 1 | C7 | spin ½, Q = −1, weak+EM, ~10⁴ MeV, unstable | Bridge |
| 2 | N3 | spin ½, Q = 0, weak-only, ~10³–10⁴ MeV, unstable | Dark Participant |
| 3 | Q5 | spin ½, Q = +2/3, strong+EM+weak, ~10⁵ MeV, unstable | Bridge |
| 4 | L2 | spin ½, Q = 0, weak-only, ~10³ MeV, stable | Dark Participant (DM candidate) |
| 5 | B4 | spin 1, Q = 0, EM-only, ~10³–10⁴ MeV, unstable | Force Carrier (hidden photon-like) |
| 6 | Q6 | spin ½, Q = −1/3, strong+EM+weak, ~10⁵ MeV, unstable | Bridge |
| 7 | C2 | spin ½, Q = −1, EM-only, ~10³ MeV, stable | Structural |
| 8 | H1 | spin 0, Q = 0, no gauge interactions, ~10⁵ MeV, stable | Mass Setter |
| 9 | M5 | spin 1, Q = 0, weak-only, ~10⁵ MeV, unstable | Force Carrier (Z′-like) |
| 10 | N4 | spin ½, Q = 0, weak-only, ~10⁶ MeV, unstable | Dark Participant (sterile ν-like) |

(Slots 11–20 include exotic-charge quarks D1 (−4/3) and Y1 (−5/3), scalar
mediator S7, glueball-like G2, and hidden-sector vectors X8/T2/K4.)

Each slot maps to a **search brief** format: properties → production channels →
detector signature → backgrounds → suggested experiments (ATLAS/CMS, LHCb,
Belle II, NA64, SHiP, FASER, direct-detection).

## 9. Correspondence with open physics problems

The lattice's empty regions line up with established gaps: sterile/right-handed
neutrinos (weak-only neutral fermions), dark-matter portals (hidden vectors,
Higgs-mixing scalars), long-lived particles, extra gauge bosons (Z′ / dark
photon), vector-like "bridge" fermions, glueballs, and extended scalar sectors.
The CHAMP filter deliberately removes territory cosmology has already excluded.

## 10. Validation roadmap (to withstand hostile review)

From the "critic scientist" Q&A in the session — none of this is done yet:

1. **Leave-family-out tests** — remove entire classes (all leptons, all vector
   bosons), not just single particles.
2. **Temporal backtests** — freeze data pre-1995 / pre-2012 and score against
   the later top-quark / Higgs discoveries.
3. **Null-model baselines** — must beat random lattice filling, raw k-NN, and
   plain parametric clustering.
4. **Robustness** — jitter masses/lifetimes/spins within uncertainties; stable
   rankings ⇒ not overfit.
5. **Calibration** — confidence intervals per predicted slot, checked against
   withheld knowns.
6. **False-discovery control** — pre-registered decision rule (top-K with score
   threshold), FDR estimated by permutation tests; target FDR < 10%.
7. **Unique testable prediction** — pick one concrete slot + a 12–24 month test
   plan on existing data (template: slot coordinates → observable → experiment →
   trigger/selection → backgrounds → statistical method → pass/fail criterion).

## 11. Known limitations

- Mass is **banded**, not predicted — wide log₁₀ bins only.
- No dynamics: no couplings, widths, production rates, anomaly-cancellation, or
  symmetry arguments. A slot being "allowed" is a weak statement.
- The enumeration grid is deliberately generous; many slots are combinatorial
  noise that tighter physics would kill.
- The coarse encoding is lossy (e.g., the Higgs carries no force flags, so
  Higgs-like slots only appear if zero-gauge candidates are allowed).
- The 100%-LOOCV claim is near-tautological for 1-NN on a small, cleanly
  separated dataset — it validates the encoding, not predictive power. The
  ablation and temporal backtests are the meaningful tests.

## 12. Artifacts from the session (all lost — rebuild targets)

The ChatGPT sandbox produced, then lost on environment reset:

- `known_particles_features.csv`, `candidates_all.csv` (1,437),
  `candidates_theory_filtered_ranked.csv` (397), top-10/top-20 CSVs
- Emergent-lattice CSVs: `emergent_empty_slots_ranked.csv`,
  `emergent_exactspin_candidates_ranked.csv`, `graviton_nearest_known_exactspin.csv`
- UPS-era CSVs: `particles_features_with_universal_speed.csv`,
  `lattice_candidates_with_universal_speed.csv`
- Serialized models `kmeans.pkl`, `knn.pkl`; `learned_rules.txt`
- `optionset_model_bundle.zip`, `OptionSet_Particle_Model.ipynb`
- PDFs: top-20 brief, white paper, Standard Model chart, UPS addendum

## 13. Next steps

1. Rebuild the pipeline locally (this repo) — dataset → features → clustering →
   1-NN → enumeration → filters → ranking, with the v2 (emergent, exact-spin)
   encoding as the primary variant and v1 kept for comparison.
2. Replace the hand-built particle table with **PDG data via SQLite**.
3. Re-run and *verify* the claimed results in §6 (LOOCV, 1,437 → 397, Higgs/top
   ablations).
4. Work through the validation roadmap in §10.
5. Regenerate the top-N search briefs from verified rankings.
