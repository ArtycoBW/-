"""Frozen external pilot on Vanetik & Kogan (2023), no raw CV redistribution.

Run: python -m ml.external_benchmark --data .local/external/vanetik2023
Fixed split/model specification. Five known vacancies; held-out resumes, not held-out jobs.
"""
import argparse
import ast
import csv
import hashlib
import itertools
import json
from pathlib import Path
import platform
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
import joblib

import numpy as np
from scipy.stats import kendalltau
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ndcg_score
from backend.matching import normalize
from backend.resume import extract_resume

SEED = 20261011
COMMIT = "7ee8f043c6e31ee94cb67f5e60b069901b533adf"
FEATURE_NAMES = ["word_tfidf_cosine", "char_tfidf_cosine", "production_skill_coverage", "skill_jaccard"]


def docx_text(path):
    with zipfile.ZipFile(path) as archive:
        entry = archive.getinfo("word/document.xml")
        if entry.file_size > 5_000_000:
            raise ValueError("Document exceeds the extraction limit")
        root = ET.fromstring(archive.read(entry))
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    return "\n".join("".join(node.itertext()) for node in root.iter(ns + "t"))


def load_annotations(path):
    content = path.read_text(encoding="utf-8-sig")
    start = re.search(r"^ANNOTATOR_1_RANKINGS\s*=", content, re.M)
    if not start:
        raise ValueError("Annotation assignments missing")
    result = {}
    for statement in ast.parse(content[start.start():]).body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            raise ValueError("Unexpected annotation syntax")
        name = statement.targets[0].id
        if name not in {"ANNOTATOR_1_RANKINGS", "ANNOTATOR_2_RANKINGS"}:
            raise ValueError("Unknown annotation field")
        result[name] = ast.literal_eval(statement.value)
    if len(result) != 2 or any(len(rows) != 30 for rows in result.values()):
        raise ValueError("Expected two annotators and thirty resumes")
    return result


def relevance(order):
    if sorted(order) != [1, 2, 3, 4, 5]:
        raise ValueError("Ranking must be a permutation of five vacancy positions")
    result = np.zeros(5)
    for position, vacancy in enumerate(order):
        result[vacancy - 1] = 4 - position
    return result


def skills(text):
    return {normalize(item) for item in extract_resume(text)["skills"]}


def feature_matrix(resumes, jobs, train_indices=None, vectorizers=None):
    matrices = []
    # The five jobs are fixed and known at inference; held-out CV text never fits IDF.
    if vectorizers is None:
        if not train_indices:
            raise ValueError("Training indices required to fit IDF")
        fit_texts = [resumes[i] for i in train_indices] + jobs
        vectorizers = [TfidfVectorizer(sublinear_tf=True, **kwargs).fit(fit_texts) for kwargs in ({"analyzer": "word", "ngram_range": (1, 2), "stop_words": "english"}, {"analyzer": "char_wb", "ngram_range": (3, 5), "max_features": 30000})]
    for vectorizer in vectorizers:
        matrices.append((vectorizer.transform(resumes) @ vectorizer.transform(jobs).T).toarray())
    cv_skills, job_skills = list(map(skills, resumes)), list(map(skills, jobs))
    coverage = np.array([[len(cv & job) / max(1, len(job)) for job in job_skills] for cv in cv_skills])
    jaccard = np.array([[len(cv & job) / max(1, len(cv | job)) for job in job_skills] for cv in cv_skills])
    return np.stack([*matrices, coverage, jaccard], axis=2), vectorizers


def train_pairwise(matrix, judgments, train_indices):
    x, y = [], []
    for i in train_indices:
        for left, right in itertools.combinations(range(5), 2):
            delta = judgments[i, left] - judgments[i, right]
            if delta == 0:
                continue
            difference = matrix[i, left] - matrix[i, right]
            x.extend([difference, -difference]); y.extend([int(delta > 0), int(delta < 0)])
    estimator = LogisticRegression(C=1.0, fit_intercept=False, max_iter=1000, random_state=SEED).fit(np.array(x), y)
    return estimator, len(y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(".local/external-benchmark"))
    args = parser.parse_args()
    root = args.data
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if commit != COMMIT:
        raise ValueError("Dataset version changed; review the source before rerunning")
    if "GNU GENERAL PUBLIC LICENSE" not in (root / "LICENSE").read_text(encoding="utf-8"):
        raise ValueError("Expected dataset license missing")
    raw = load_annotations(root / "annotations-for-the-first-30-vacancies.txt")
    excluded, ids, resumes, judgments, individual = [], [], [], [], []
    seen = set()
    for i in range(30):
        orders = [rows[i] for rows in raw.values()]
        try:
            annotated = np.array([relevance(order) for order in orders])
        except ValueError:
            excluded.append({"resume_id": i + 1, "reason": "invalid_permutation", "original_orders": orders})
            continue
        cv = docx_text(root / "CV" / f"{i+1}.docx")
        fingerprint = hashlib.sha256(" ".join(cv.lower().split()).encode()).hexdigest()
        if fingerprint in seen:
            excluded.append({"resume_id": i + 1, "reason": "duplicate_text"}); continue
        seen.add(fingerprint)
        ids.append(i + 1); resumes.append(cv); judgments.append(annotated.mean(axis=0)); individual.append(annotated)
    with (root / "5_vacancies.csv").open(encoding="utf-8-sig", newline="") as stream:
        jobs = list(csv.DictReader(stream))
    if len(jobs) != 5:
        raise ValueError("Exactly five vacancies required")
    judgments = np.array(judgments)
    rng = np.random.default_rng(SEED)
    shuffled = rng.permutation(len(ids))
    test = sorted(shuffled[:10].tolist()); train = sorted(shuffled[10:].tolist())
    job_texts = [job["job_title"] + "\n" + job["job_description"] for job in jobs]
    matrix, vectorizers = feature_matrix(resumes, job_texts, train)
    estimator, training_pairs = train_pairwise(matrix, judgments, train)
    scores = {"production_skills_only": matrix[:, :, 2], "tfidf_mean": matrix[:, :, :2].mean(axis=2), "pairwise_text_model": matrix @ estimator.coef_[0]}
    metrics, per_resume = {}, {}
    for method, values in scores.items():
        rows = [{"resume_id": ids[i], "ndcg_at_3": float(ndcg_score([judgments[i]], [values[i]], k=3)), "kendall_tau": float(kendalltau(judgments[i], values[i]).statistic) if len(set(values[i])) > 1 else None} for i in test]
        per_resume[method] = rows
        metrics[method] = {"ndcg_at_3": float(np.mean([r["ndcg_at_3"] for r in rows])), "kendall_tau": float(np.mean([r["kendall_tau"] for r in rows if r["kendall_tau"] is not None])) if any(r["kendall_tau"] is not None for r in rows) else None}
    delta = np.array([r["ndcg_at_3"] for r in per_resume["pairwise_text_model"]]) - np.array([r["ndcg_at_3"] for r in per_resume["tfidf_mean"]])
    bootstrap = np.random.default_rng(SEED).choice(delta, size=(5000, len(test))).mean(axis=1)
    permutations = np.array(list(itertools.permutations(range(5))))
    random_ndcg = float(np.mean([ndcg_score(np.repeat(judgments[[i]], len(permutations), axis=0), permutations, k=3) for i in test]))
    files = [root / "LICENSE", root / "5_vacancies.csv", root / "annotations-for-the-first-30-vacancies.txt", root / "annotation_instructions.docx", *[root / "CV" / f"{i}.docx" for i in range(1, 31)]]
    provenance = {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report = {"source": "https://github.com/NataliaVanetik/vacancy-resume-matching-dataset", "citation": "Vanetik N., Kogan G. (2023). Job Vacancy Ranking with Sentence Embeddings, Keywords, and Named Entities. Information 14(8),468. doi:10.3390/info14080468", "license": "GPL-3.0 (repository LICENSE)", "dataset_commit": commit, "seed": SEED, "python": platform.python_version(), "feature_specification": FEATURE_NAMES, "valid_resumes": len(ids), "excluded": excluded, "train_resume_ids": [ids[i] for i in train], "test_resume_ids": [ids[i] for i in test], "known_jobs": 5, "training_pairwise_examples": training_pairs, "test_cv_job_pairs": len(test) * 5, "annotators": 2, "annotator_mean_kendall_tau": float(np.mean([kendalltau(a[0], a[1]).statistic for a in individual])), "metrics": metrics, "random_permutation_expected_ndcg3": random_ndcg, "model_minus_tfidf_bootstrap95": np.quantile(bootstrap, [.025, .975]).tolist(), "per_resume": per_resume, "source_sha256": provenance, "production_model_changed": False, "limitations": ["Small pilot: only ten held-out CVs and five shared jobs; not a cold-job evaluation.", "Direction: rank jobs for a CV, not candidates for an employer need.", "Human ordinal preferences, not outcomes of hiring or job performance.", "Only the production skill component can be measured; verified assessments, FSP, activity and format are missing. Full six-feature model is not externally validated.", "No tuning on test. Experimental text model is not automatically deployed."]}
    args.output.mkdir(parents=True, exist_ok=True)
    artifact = args.output / "text-model.joblib"
    joblib.dump({"vectorizers": vectorizers, "estimator": estimator, "features": FEATURE_NAMES, "dataset_commit": commit, "status": "experimental_not_deployed"}, artifact)
    restored = joblib.load(artifact)  # Only this locally generated artifact; never load untrusted pickle files.
    replay, _ = feature_matrix(resumes, job_texts, vectorizers=restored["vectorizers"])
    np.testing.assert_allclose(replay @ restored["estimator"].coef_[0], scores["pairwise_text_model"], rtol=1e-12)
    report["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    report["artifact_reload_verified"] = True
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    (args.output / "text-model.json").write_text(json.dumps({"status": "experimental_not_deployed", "features": FEATURE_NAMES, "coef": estimator.coef_[0].tolist(), "intercept": 0, "seed": SEED, "dataset_commit": commit, "train_resume_ids": report["train_resume_ids"]}, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("valid_resumes", "excluded", "metrics", "random_permutation_expected_ndcg3", "model_minus_tfidf_bootstrap95", "annotator_mean_kendall_tau")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
