from types import SimpleNamespace
import numpy as np
from backend import matching
from backend.assessment import generate_questions, evaluate
from ml.train import dataset, ranking_metrics

def profile(**kwargs):
    p=dict(skills=["Python","Postgres"],score=90,grade="middle",active_at=2_000_000_000,work_format="remote")
    p.update(kwargs)
    return SimpleNamespace(**p)

def need(): return SimpleNamespace(skills=["py","postgresql"],grade="middle",work_format="remote")

def test_aliases_boundaries_and_no_contact_features():
    x=matching.features(profile(),need(),[],now=2_000_000_000)
    assert x==[1,.9,1,1,0,1]
    assert matching.features(profile(),need(),range(100),now=2_000_000_000)[4]==1
    assert matching.features(profile(active_at=0),need(),[],now=2_000_000_000)[3]==0
    assert not {"age","gender","name","contact"} & set(matching.FEATURES)

def test_missing_model_fallback(monkeypatch,tmp_path):
    monkeypatch.setattr(matching,"MODEL_PATH",str(tmp_path/'absent.json'))
    r=matching.rank(profile(),need(),[])
    assert r['mode']=='rules-v1' and r['missing_skills']==[]
    assert 0<=r['score']<=100
    assert matching.rank(profile(),need(),range(3))['score']>=r['score']

def test_reproducible_splits_and_rank_metrics():
    a,b,c=dataset(42,4),dataset(42,4),dataset(43,4)
    assert np.array_equal(a[0],b[0]) and not np.array_equal(a[0],c[0])
    r=ranking_metrics(a[2],a[2],a[3])
    assert r['ndcg_at_5']==1.0

def test_bank_grading_has_no_nan_shortcut():
    q=generate_questions('backend','senior',42)
    assert evaluate(q,{x['id']:'NaN' for x in q})[0]==0
    assert evaluate(q,{x['id']:x['answer'] for x in q})[0]==100


def test_exported_model_identity_and_monotonicity():
    import hashlib
    import json
    from pathlib import Path
    model_path = Path(matching.MODEL_PATH)
    artifact = json.loads(model_path.read_text(encoding="utf-8"))
    metrics = json.loads(Path("ml/metrics.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(model_path.read_bytes()).hexdigest() == metrics["model_sha256"]
    assert artifact["features"] == matching.FEATURES
    assert all(v >= -1e-10 for v in artifact["coef"])
    base = matching.rank(profile(skills=["Python"], score=75), need(), [])
    improved = matching.rank(profile(skills=["Python", "SQL", "Postgres"], score=100), need(), [])
    assert base["mode"] == "hybrid-v1"
    assert improved["score"] >= base["score"]
    # Irrelevant personal data cannot change the score.
    changed = matching.rank(profile(skills=["Python"], score=75, name="Другой человек", contact="private@example.org"), need(), [])
    assert changed["score"] == base["score"]


def test_corrupted_export_uses_formula(monkeypatch, tmp_path):
    import json
    path = tmp_path / "model.json"
    monkeypatch.setattr(matching, "MODEL_PATH", str(path))
    for payload in [{"features": matching.FEATURES, "coef": [float("nan")] * 6, "intercept": 0}, {"features": ["wrong"], "coef": [1], "intercept": 0}]:
        path.write_text(json.dumps(payload), encoding="utf-8")
        matching.load_model.cache_clear()
        result = matching.rank(profile(), need(), [])
        assert result["mode"] == "rules-v1" and result["learned_score"] is None
        assert 0 <= result["score"] <= 100
