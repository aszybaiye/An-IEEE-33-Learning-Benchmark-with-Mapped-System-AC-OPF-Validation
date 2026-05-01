from __future__ import annotations

import numpy as np
from sklearn.preprocessing import StandardScaler


class RiskAwareEmbedding:
    def __init__(self, embedding_dim: int = 4, risk_alpha: float = 2.0):
        self.embedding_dim = embedding_dim
        self.risk_alpha = risk_alpha
        self.scaler = StandardScaler()
        self.proj: np.ndarray | None = None

    def fit(self, x: np.ndarray, risk: np.ndarray) -> "RiskAwareEmbedding":
        x_std = self.scaler.fit_transform(x)
        w = 1.0 + self.risk_alpha * risk.reshape(-1, 1)
        x_weighted = x_std * w
        cov = np.cov(x_weighted, rowvar=False)
        eigvals, eigvecs = np.linalg.eigh(cov)
        order = np.argsort(eigvals)[::-1]
        self.proj = eigvecs[:, order[: self.embedding_dim]]
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        if self.proj is None:
            raise RuntimeError("Model is not fitted.")
        x_std = self.scaler.transform(x)
        return x_std @ self.proj

    def fit_transform(self, x: np.ndarray, risk: np.ndarray) -> np.ndarray:
        self.fit(x, risk)
        return self.transform(x)
