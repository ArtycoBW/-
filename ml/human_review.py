"""Blind review packs and held-out evaluation; never fabricates human labels."""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import random
import time

import numpy as np
from scipy.special import expit
from sklearn.metrics import cohen_kappa_score, ndcg_score
from sqlalchemy import select
from backend import models as m
from backend.db import SessionLocal
from backend.matching import BASE_WEIGHTS, FEATURES, features, load_model
from backend.config import MODEL_PATH


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def build_pack(directory, source, seed=20261011):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    model_path = Path(MODEL_PATH)
    artifact = load_model(str(model_path), model_path.stat().st_mtime_ns)
    rng = random.Random(seed)
    now = time.time()
    pairs, brief, counters = [], [], {}
    with SessionLocal() as db:
        candidates = list(db.scalars(select(m.Candidate).where(m.Candidate.published.is_(True), m.Candidate.consent.is_(True), m.Candidate.grade.is_not(None)).order_by(m.Candidate.id)))
        # Split people before constructing query groups: no person appears in two splits.
        rng.shuffle(candidates)
        partitions = {c.id: ("train" if i % 10 < 6 else "validation" if i % 10 < 8 else "test") for i, c in enumerate(candidates)}
        aliases = {c.id: f"person-{i+1:04d}" for i, c in enumerate(candidates)}
        needs = list(db.scalars(select(m.Need).order_by(m.Need.id)))
        rng.shuffle(needs)
        for index, need in enumerate(needs):
            split = ("train", "validation", "test")[index % 3]
            eligible = [c for c in candidates if partitions[c.id] == split and c.specialization == need.specialization and c.grade == need.grade]
            rng.shuffle(eligible)
            eligible = eligible[:10]
            if len(eligible) < 5:
                continue
            query = f"query-{index+1:04d}"
            # Exclude free text, names, company IDs, salary and all contact fields.
            brief.append({"query_id": query, "specialization": need.specialization, "grade": need.grade, "skills": need.skills, "work_format": need.work_format, "candidates": []})
            for candidate in eligible:
                achievements = list(db.scalars(select(m.Achievement).where(m.Achievement.candidate_id == candidate.id)))
                x = features(candidate, need, achievements, now=now)
                pair = {"query_id": query, "candidate_id": aliases[candidate.id], "split": split, "specialization": need.specialization, "features": x}
                pairs.append(pair)
                brief[-1]["candidates"].append({"candidate_id": pair["candidate_id"], "skills": candidate.skills, "assessment_score": candidate.score, "grade": candidate.grade, "work_format": candidate.work_format, "activity_days_ago": round((now - candidate.active_at) / 86400), "demo_achievements": len(achievements)})
            counters[split] = counters.get(split, 0) + 1
    manifest = {"version": 1, "created_at": now, "seed": seed, "source": source, "features": FEATURES, "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(), "model": artifact, "pairs": pairs, "queries": counters}
    write_json(directory / "manifest-private.json", manifest)
    write_json(directory / "review-pack.json", {"source": source, "rubric": {"0": "Не подходит по обязательным навыкам", "1": "Существенные пробелы, нужна подготовка", "2": "Подходит с отдельными пробелами", "3": "Хорошо подходит по доступным доказательствам"}, "instructions": "Оценивайте независимо. Не смотрите оценки модели и других экспертов. 0–3, не вероятность найма. Достижения демонстрационные. Передавайте только обезличенные ID экспертов.", "queries": brief})
    with (directory / "labels-template.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["query_id", "candidate_id", "reviewer_id", "relevance"])
        writer.writeheader()
        for pair in pairs:
            writer.writerow({key: pair[key] for key in ["query_id", "candidate_id"]})
    return {"pairs": len(pairs), "queries": counters, "status": "awaiting_independent_human_ratings"}


def evaluate_pack(manifest, labels):
    if manifest.get("features") != FEATURES:
        raise ValueError("Несовместимая схема признаков")
    pairs = manifest["pairs"]
    by_key, people, queries = {}, {}, {}
    for pair in pairs:
        key = (pair["query_id"], pair["candidate_id"])
        if key in by_key:
            raise ValueError("Повтор пары в наборе")
        if pair["split"] not in {"train", "validation", "test"}:
            raise ValueError("Неизвестное разбиение")
        for registry, identifier in [(people, pair["candidate_id"]), (queries, pair["query_id"])]:
            if identifier in registry and registry[identifier] != pair["split"]:
                raise ValueError("Утечка между разбиениями")
            registry[identifier] = pair["split"]
        x = pair["features"]
        if len(x) != len(FEATURES) or not all(isinstance(v, (float, int)) and np.isfinite(v) and 0 <= v <= 1 for v in x):
            raise ValueError("Некорректные признаки")
        by_key[key] = pair
    ratings = {}
    for row in labels:
        key = (row["query_id"], row["candidate_id"])
        if key not in by_key:
            raise ValueError("Оценка неизвестной пары")
        reviewer = row["reviewer_id"].strip()
        if not reviewer or row["relevance"] not in {"0", "1", "2", "3"}:
            raise ValueError("Нужны ID эксперта и целая оценка 0–3; пустые оценки запрещены")
        bucket = ratings.setdefault(key, {})
        if reviewer in bucket:
            raise ValueError("Повтор оценки одного эксперта")
        bucket[reviewer] = int(row["relevance"])
    test_pairs = [p for p in pairs if p["split"] == "test"]
    if not test_pairs or any(len(ratings.get((p["query_id"], p["candidate_id"]), {})) < 2 for p in test_pairs):
        raise ValueError("Для каждой пары test нужны минимум две независимые оценки")
    artifact = manifest["model"]
    results = []
    for query_id in sorted({p["query_id"] for p in test_pairs}):
        group = [p for p in test_pairs if p["query_id"] == query_id]
        if len(group) < 5:
            raise ValueError("В каждой test-потребности нужно минимум пять кандидатов")
        relevance = np.array([np.mean(list(ratings[(p["query_id"], p["candidate_id"])].values())) for p in group])
        matrix = np.array([p["features"] for p in group])
        baseline = matrix @ BASE_WEIGHTS
        hybrid = .7 * baseline + .3 * expit(matrix @ artifact["coef"] + artifact["intercept"])
        results.append({"query_id": query_id, "specialization": group[0]["specialization"], "baseline_ndcg5": float(ndcg_score([relevance], [baseline], k=5)), "hybrid_ndcg5": float(ndcg_score([relevance], [hybrid], k=5))})
    reviewers = sorted({r for p in test_pairs for r in ratings[(p["query_id"], p["candidate_id"])]})
    agreement = []
    for left, right in itertools.combinations(reviewers, 2):
        common = [ratings[(p["query_id"], p["candidate_id"])] for p in test_pairs if left in ratings[(p["query_id"], p["candidate_id"])] and right in ratings[(p["query_id"], p["candidate_id"])]]
        if common:
            a, b = [x[left] for x in common], [x[right] for x in common]
            kappa = cohen_kappa_score(a, b, weights="linear") if len(set(a + b)) > 1 else None
            agreement.append({"reviewers": [left, right], "pairs": len(common), "weighted_kappa": float(kappa) if kappa is not None and np.isfinite(kappa) else None})
    deltas = np.array([r["hybrid_ndcg5"] - r["baseline_ndcg5"] for r in results])
    interval = np.quantile(np.random.default_rng(20261011).choice(deltas, size=(2000, len(deltas))).mean(axis=1), [.025, .975]).tolist() if len(results) >= 2 else None
    segments = {spec: {"queries": len(group), "hybrid_ndcg5": float(np.mean([r["hybrid_ndcg5"] for r in group]))} for spec in sorted({r["specialization"] for r in results}) if (group := [r for r in results if r["specialization"] == spec])}
    return {"source": manifest["source"], "model_sha256": manifest["model_sha256"], "test_queries": len(results), "test_pairs": len(test_pairs), "baseline_ndcg5": float(np.mean([r["baseline_ndcg5"] for r in results])), "hybrid_ndcg5": float(np.mean([r["hybrid_ndcg5"] for r in results])), "delta_bootstrap_95": interval, "segments": segments, "agreement": agreement, "per_query": results, "limitations": "ID экспертов не доказывают их независимость: организатор фиксирует происхождение и согласие. Оценки синтетических профилей не заменяют реальные резюме и исходы найма. Это пилотная оценка, не сертификация качества. Test нельзя использовать для подбора весов."}


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("pack")
    pack.add_argument("directory", type=Path)
    pack.add_argument("--source", choices=["synthetic_profiles", "consented_real_profiles"], required=True)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("directory", type=Path)
    evaluate.add_argument("labels", type=Path)
    args = parser.parse_args()
    if args.command == "pack":
        result = build_pack(args.directory, args.source)
    else:
        manifest = json.loads((args.directory / "manifest-private.json").read_text(encoding="utf-8"))
        with args.labels.open(encoding="utf-8-sig", newline="") as stream:
            result = evaluate_pack(manifest, list(csv.DictReader(stream)))
        write_json(args.directory / "evaluation.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
