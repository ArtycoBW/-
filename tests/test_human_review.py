import copy
import pytest
from ml.human_review import evaluate_pack
from backend.matching import FEATURES


def fixture():
    pairs = [{"query_id": "q1", "candidate_id": f"p{i}", "split": "test", "specialization": "backend", "features": [i / 4, .8, 1, .5, 0, 1]} for i in range(5)]
    manifest = {"source": "synthetic_profiles", "features": FEATURES, "pairs": pairs, "model": {"coef": [1] * 6, "intercept": 0}, "model_sha256": "test-only"}
    labels = [{"query_id": "q1", "candidate_id": f"p{i}", "reviewer_id": reviewer, "relevance": str(min(i, 3))} for reviewer in ("expert-1", "expert-2") for i in range(5)]
    return manifest, labels


def test_no_fabricated_labels_and_no_single_rater_evaluation():
    manifest, labels = fixture()
    for rows in ([], labels[:5]):
        with pytest.raises(ValueError, match="две"):
            evaluate_pack(manifest, rows)
    labels[0]["relevance"] = ""
    with pytest.raises(ValueError, match="пустые"):
        evaluate_pack(manifest, labels)


def test_rejects_leakage_and_duplicate_raters():
    manifest, labels = fixture()
    with pytest.raises(ValueError, match="Повтор оценки"):
        evaluate_pack(manifest, [*labels, labels[0]])
    leaked = copy.deepcopy(manifest["pairs"][0])
    leaked.update(query_id="train-q", split="train")
    manifest["pairs"].append(leaked)
    with pytest.raises(ValueError, match="Утечка"):
        evaluate_pack(manifest, labels)


def test_blind_heldout_evaluation_and_agreement():
    manifest, labels = fixture()
    report = evaluate_pack(manifest, labels)
    assert report["test_pairs"] == 5
    assert report["hybrid_ndcg5"] == pytest.approx(1)
    assert report["agreement"][0]["weighted_kappa"] == pytest.approx(1)
    assert report["delta_bootstrap_95"] is None  # One query cannot give a useful interval.
    assert report["source"] == "synthetic_profiles"
