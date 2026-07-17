"""Emergent families, LOOCV backtest, and novelty scoring (MODEL_DESIGN.md §3).

All distances are computed in standardized feature space (scaler fit on the
known particles).
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
from sklearn.preprocessing import MinMaxScaler

RANDOM_STATE = 42
# k=5 emergent families: quarks / charged-EM-weak states (charged leptons+W) /
# neutrinos / massless gauge / neutral heavy short-lived (Z+Higgs).
# Min-max scaling (not z-score): with 17 points the near-constant flag columns
# get inflated variance under z-scoring, which breaks 1-NN LOOCV on the
# family labels.
N_FAMILIES = 5


def _scale(X_known: pd.DataFrame, *others: pd.DataFrame):
    scaler = MinMaxScaler().fit(X_known)
    scaled = [scaler.transform(X_known)]
    scaled += [scaler.transform(o) for o in others]
    return scaled if others else scaled[0]


def fit_families(X: pd.DataFrame, k: int = N_FAMILIES) -> np.ndarray:
    """Unsupervised k-means family labels — no SM categories."""
    Xs = _scale(X)
    return KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit_predict(Xs)


def loocv_accuracy(X: pd.DataFrame, labels: np.ndarray) -> float:
    """Leave-one-out accuracy of a 1-NN classifier on the family labels."""
    Xs = _scale(X)
    hits = 0
    for i in range(len(Xs)):
        mask = np.ones(len(Xs), dtype=bool)
        mask[i] = False
        knn = KNeighborsClassifier(n_neighbors=1).fit(Xs[mask], labels[mask])
        hits += int(knn.predict(Xs[i:i + 1])[0] == labels[i])
    return hits / len(Xs)


def novelty_scores(X_known: pd.DataFrame, X_query: pd.DataFrame) -> np.ndarray:
    """Distance from each query point to its nearest known particle."""
    Xs, Qs = _scale(X_known, X_query)
    nn = NearestNeighbors(n_neighbors=1).fit(Xs)
    dist, _ = nn.kneighbors(Qs)
    return dist[:, 0]


def nearest_known(X_known: pd.DataFrame, names: pd.Series,
                  X_query: pd.DataFrame, k: int = 3) -> list[str]:
    """Names of the k nearest known particles to a single query point."""
    Xs, Qs = _scale(X_known, X_query)
    nn = NearestNeighbors(n_neighbors=k).fit(Xs)
    _, idx = nn.kneighbors(Qs)
    return [names.iloc[i] for i in idx[0]]
