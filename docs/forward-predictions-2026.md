# Registered Forward Predictions — Doubly-Heavy Baryons

**Registered: 2026-07-17.** Method frozen as of this date in
`lattice/constituent.py` (regenerate exactly via
`python -c "from lattice.constituent import forward_predictions; ..."`;
all values asserted in `tests/test_constituent.py`).

This is the framework's transition from retrodiction to prediction. The
historical audit (`data/output/audit_report.md`) found lattice-style
gap-prediction went **8/8 on within-pattern completions and 0/4 on
beyond-pattern extrapolations**. The targets below are chosen strictly from
the within-pattern regime: ground-state slots of partially-instantiated
baryon multiplets whose neighbors are measured.

## Method

Additive constituent-quark model fit by least squares over the 21 curated
known baryons (features: strange/charm/bottom quark counts + spin-3/2 flag;
`lattice/constituent.py`). In-sample leave-one-out RMS: **33 MeV** (20
evaluable baryons). Out-of-sample validation: the **Ω_cc⁺**, announced by
LHCb on 2026-06-03 (~3727 MeV) and deliberately excluded from training, is
predicted at **3775 MeV — a 48 MeV miss**. The quoted uncertainty is
therefore ±48 MeV (the larger of the two), and the validation miss has a
known sign: the additive model lacks explicit heavy-pair binding, so true
masses are expected to sit **at or below** the central values.

## Predictions

| ID | state | content | J^P | cell (Q, S, C, B̃) | predicted mass | status at registration |
|---|---|---|---|---|---|---|
| LM-2026-001 | **Ξ_bb⁰ / Ξ_bb⁻** | bbu / bbd | ½⁺ | (0 or −1, 0, 0, −2) | **10 250 ± 48 MeV** | unobserved |
| LM-2026-002 | **Ω_bb⁻** | bbs | ½⁺ | (−1, −1, 0, −2) | **10 410 ± 48 MeV** | unobserved |
| LM-2026-003 | **Ξ_bc⁺ / Ξ_bc⁰** | bcu / bcd | ½⁺ | (+1 or 0, 0, +1, −1) | **6 932 ± 48 MeV** | unobserved; LHCb reports unconfirmed hints at 6 571 / 6 694 MeV (4.3σ / 4.1σ local) — *below* our estimate |
| LM-2026-004 | **Ω_bc⁰** | bcs | ½⁺ | (0, −1, +1, −1) | **7 092 ± 48 MeV** | unobserved |
| LM-2026-005 | **Ξ_cc⁺** | ccd | ½⁺ | (+1, 0, +2, 0) | **3 614 ± 48 MeV** | unobserved; **discriminating**: SELEX's unconfirmed 3 519 MeV claim sits ~2σ below — if SELEX is right, this entry is a miss |
| LM-2026-006 | **Ω_ccc⁺⁺** | ccc | 3/2⁺ | (+2, 0, +3, 0) | **cell-level**: ≤ 5 158 MeV (additive upper bound; expected ~300–400 below; lattice QCD ~4 800) | unobserved — "the Ω⁻ of charm" |
| LM-2026-007 | **Ω_bbb⁻** | bbb | 3/2⁺ | (−1, 0, 0, −3) | **cell-level**: ≤ 15 112 MeV (additive upper bound; expected ~500–700 below; lattice QCD ~14 400) | unobserved — "the Ω⁻ of beauty" |

Entries 006–007 are registered **cell-level only** (existence, quantum
numbers, mass band, and an upper bound): three heavy-quark pairs put the
additive model outside its validated regime, and the registration says so
rather than pretending precision.

Validation row LM-2026-V01 (not a prediction): Ω_cc⁺ (ccs, ½⁺) predicted
3 775 ± 48 vs LHCb ~3 727 MeV — within the quoted band.

## Falsification criteria

- A registered state observed with ground-state quantum numbers whose mass
  lies **within ±2σ (±96 MeV)** of the central value: hit.
- Observed **outside ±3σ (±144 MeV)**: miss (counts against the framework
  in any future audit update, exactly like the corpus's refuted entries).
- If the LHCb Ξ_bc hints at 6 571/6 694 MeV are confirmed as the ½⁺ ground
  state, that is a **miss** (≥5σ below our central value) — we do not
  reserve the right to reinterpret.
- No observation is a null result, not a hit.

## Honest context

Sharper predictions exist and predate ours: e.g., Karliner & Rosner give
Ξ_bb ≈ 10 162 ± 12 MeV (Phys. Rev. D 90, 094007 framework), and lattice
QCD is more precise still. We are not competing on precision. The
registered claim is about the *framework*: a deliberately minimal,
fully-reproducible lattice + additive fit, whose every ingredient is
tested, registering its own numbers before the fact. Note our central
values sit ~90 MeV above Karliner-Rosner's — consistent with the known
additive-model bias direction stated above; if the discoveries land on the
sharper predictions, our ±2σ windows still contain them (Ξ_bb: KR's
10 162 is 88 MeV below our 10 250, within 2σ).

## Timestamping

This file, the frozen code, and the test suite constitute the
registration. For an independent timestamp, commit this repository state
to a public host and/or archive it with a DOI (Zenodo) — see the project
roadmap.
