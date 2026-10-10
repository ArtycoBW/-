"""Independent, reproducible diagnostics for the exported model (no retraining)."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
from sklearn.metrics import ndcg_score, brier_score_loss
from backend.matching import BASE_WEIGHTS, FEATURES
from ml.train import dataset

ROOT = Path(__file__).resolve().parent


def evaluate():
    raw = (ROOT / "model.json").read_bytes()
    model = json.loads(raw)
    assert model["features"] == FEATURES
    coef = np.asarray(model["coef"])
    rng = np.random.default_rng(20261011)
    reports, differences = [], []
    for seed in [91823, 61743, 41071, 31337, 78031]:
        x, labels, relevance, groups = dataset(seed, 80)
        learned = expit(x @ coef + model["intercept"])
        baseline = x @ BASE_WEIGHTS
        scores = {"formula": baseline, "hybrid": .7 * baseline + .3 * learned,
                  "random": rng.random(len(x))}
        per_query = {}
        for method, values in scores.items():
            per_query[method] = np.asarray([ndcg_score([relevance[groups == g]], [values[groups == g]], k=5) for g in np.unique(groups)])
        differences.extend((per_query["hybrid"] - per_query["formula"]).tolist())
        perturbed = x.copy()
        perturbed[:, 4] = 0
        cold = .7 * (perturbed @ BASE_WEIGHTS) + .3 * expit(perturbed @ coef + model["intercept"])
        reports.append({"seed": seed, "queries": 80, "ndcg_at_5": {name: round(float(v.mean()), 5) for name, v in per_query.items()},
                        "brier_on_synthetic_labels": round(float(brier_score_loss(labels, learned)), 5),
                        "without_fsp_ndcg_at_5": round(float(np.mean([ndcg_score([relevance[groups == g]], [cold[groups == g]], k=5) for g in np.unique(groups)])), 5)})
    diffs = np.asarray(differences)
    means = rng.choice(diffs, (2000, len(diffs)), replace=True).mean(axis=1)
    result = {"model_sha256": hashlib.sha256(raw).hexdigest(), "protocol": "5 unseen seeds, 400 query groups, 12800 synthetic pairs; paired bootstrap over queries, 2000 resamples",
              "datasets": reports, "hybrid_minus_formula_ndcg": round(float(diffs.mean()), 5),
              "difference_95pct_interval": [round(float(v), 5) for v in np.quantile(means, [.025, .975])],
              "nonnegative_coefficients": bool(np.all(coef >= -1e-10)),
              "limits": ["Independent seeds reuse the same synthetic generator: this is not external validation.",
                         "The generator and formula share feature assumptions; high NDCG is expected and must not be presented as hiring accuracy.",
                         "No claims about real-world fairness, calibration or employment outcomes."]}
    (ROOT / "robustness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("hybrid_minus_formula_ndcg", "difference_95pct_interval", "nonnegative_coefficients")}))
    return result


if __name__ == "__main__":
    evaluate()
