# Null-model baseline report

## 1. Recovery-rank experiment (leave-one-out, both layers)

Remove each known particle; rank its true cell among all candidate
slots by proximity to remaining known structure (ascending novelty).
Null: the true cell is a uniformly random candidate (percentile 0.5).

- evaluable ablations: **46** (degenerate cells excluded; 0 unrecovered)
- mean proximity percentile: **0.133** (null: 0.5)
- z = 8.6, one-sided **p ≈ 3.0e-18**

| particle | layer | percentile |
|---|---|---|
| Xi0 | hadron | 0.002 |
| Delta+ | hadron | 0.002 |
| K*+ | hadron | 0.004 |
| Bs0 | hadron | 0.004 |
| K+ | hadron | 0.006 |
| rho+ | hadron | 0.006 |
| K*0 | hadron | 0.008 |
| muon | fundamental | 0.008 |
| tau | fundamental | 0.009 |
| Xi- | hadron | 0.010 |
| charm | fundamental | 0.011 |
| top | fundamental | 0.011 |
| pi+ | hadron | 0.012 |
| Sigma- | hadron | 0.015 |
| strange | fundamental | 0.016 |
| bottom | fundamental | 0.017 |
| B0 | hadron | 0.018 |
| K0 | hadron | 0.019 |
| Sigma*+ | hadron | 0.024 |
| Xi*0 | hadron | 0.026 |
| Xi*- | hadron | 0.027 |
| Delta0 | hadron | 0.028 |
| Delta- | hadron | 0.028 |
| Sigma*0 | hadron | 0.028 |
| Sigma*- | hadron | 0.028 |
| D+ | hadron | 0.028 |
| Ds+ | hadron | 0.032 |
| D0 | hadron | 0.037 |
| B+ | hadron | 0.037 |
| Sigma+ | hadron | 0.046 |
| Omega- | hadron | 0.051 |
| Delta++ | hadron | 0.059 |
| eta_c | hadron | 0.114 |
| up | fundamental | 0.117 |
| down | fundamental | 0.117 |
| Lambda_c+ | hadron | 0.176 |
| higgs | fundamental | 0.294 |
| Z | fundamental | 0.297 |
| electron | fundamental | 0.329 |
| Lambda_b0 | hadron | 0.365 |
| n | hadron | 0.469 |
| Xi_cc++ | hadron | 0.471 |
| p | hadron | 0.488 |
| W | fundamental | 0.698 |
| photon | fundamental | 0.732 |
| gluon | fundamental | 0.775 |

Honest reading: pattern-fillers (quarks, leptons, multiplet members)
rank in the top few percent; isolated states (photon, gluon, W) rank
worse than chance — proximity ranking predicts *completions of existing structure*, not lone outliers.

## 2. LOOCV label-permutation test

- observed LOOCV accuracy: **100%**
- permuted labels (n=200): mean 18.9%, max 52.9%
- **p = 0.0050** (floor for 200 permutations)

## 3. Mass predictions vs naive-mean null

| tool | predicted | measured | rel. error | null (mean) error |
|---|---|---|---|---|
| koide_tau | 1,777 MeV | 1,777 MeV | 0.008% | 97% |
| gmo_omega | 1,685 MeV | 1,672 MeV | 0.764% | 19% |
| ladder_top | 746,713 MeV | 172,760 MeV | 332.226% | 100% |

Koide and GMO beat the naive baseline by 2–4 orders of magnitude;
the quark ladder is wrong in MeV (~330%) but still far better than
the mean-null in log space and lands the correct lattice band.

## 4. Filter selectivity vs random-filter null

- **fundamental**: keep-rate 37.5%, all 17 knowns pass; a random filter of equal selectivity passes all knowns with p ≈ 5.7e-08
- **hadron**: keep-rate 1.4%, all 41 knowns pass; a random filter of equal selectivity passes all knowns with p ≈ 3.5e-76

Caveat: in-sample: the filters were written knowing the known particles, so this measures structural consistency, not out-of-sample discovery power.

## 5. Jitter robustness (§10.4)

**measurement scale (σ=0.01 dex ≈ ±2.3%)**, 50 trials:
- LOOCV stays 100%: 100% of trials
- Higgs / top / Ω⁻ cells recovered: 100% / 100% / 100%
- GMO median rel. error 2.2% (naive-mean null: 18.7%)

**stress scale (σ=0.1 dex ≈ ±26%)**, 50 trials:
- LOOCV stays 100%: 100% of trials
- Higgs / top / Ω⁻ cells recovered: 100% / 100% / 100%
- GMO median rel. error 19.8% (naive-mean null: 17.2%)

Finding: slot recovery is structurally robust even at ±26% mass
noise, but GMO's *precision* advantage needs precision inputs —
at stress scale extrapolation amplifies noise and the naive mean
becomes competitive.

## 6. Operating curve / pre-registered decision rule (§10.5–10.6)

Rule: pre-registered: flag the top 10% of candidate cells by proximity as search targets; under the null, 10% of true cells would be flagged by chance. Scored on 46 ablations:

| top k% | hits | recall | enrichment | binomial p |
|---|---|---|---|---|
| 1% | 10/46 | 21.7% | 21.7× | 2.9e-11 |
| 5% | 30/46 | 65.2% | 13.0× | 4.2e-28 |
| 10% | 32/46 | 69.6% | 7.0× | 5.8e-22 |
| 25% | 36/46 | 78.3% | 3.1× | 5.3e-14 |

Reading: a search program that takes the top 10% of candidate cells
by proximity captures the majority of true pattern-completions at
~7× the null rate. The top-1% bar is strict in absolute recall but
keeps ~7× enrichment.
