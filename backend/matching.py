"""Прозрачные признаки подбора. Контактные данные в скоринг не поступают."""
import json
import math
import time
from pathlib import Path
from backend.config import MODEL_PATH

FEATURES = ["skills", "test", "grade", "freshness", "fsp", "format"]
BASE_WEIGHTS = [0.40, 0.25, 0.15, 0.07, 0.08, 0.05]
ALIASES = {"js": "javascript", "ts": "typescript", "postgres": "postgresql", "react.js": "react", "nextjs": "next.js", "py": "python"}

def normalize(skill):
    return ALIASES.get(skill.strip().lower(), skill.strip().lower())

def features(profile, need, achievements, now=None):
    now = now or time.time()
    requested = {normalize(s) for s in need.skills}
    available = {normalize(s) for s in profile.skills}
    coverage = len(requested & available) / max(len(requested), 1)
    fsp = min(len(achievements), 3) / 3
    grade_levels = {"junior": 1, "middle": 2, "senior": 3}
    grade_fit = max(0, 1 - abs(grade_levels.get(profile.grade, 0) - grade_levels.get(need.grade, 0)) * 0.5)
    age_days = max(0, (now - profile.active_at) / 86400)
    return [coverage, profile.score / 100, grade_fit, max(0, 1 - age_days / 180), fsp, float(profile.work_format == need.work_format)]

def rank(profile, need, achievements):
    x = features(profile, need, achievements)
    baseline = sum(w * v for w, v in zip(BASE_WEIGHTS, x))
    score, mode = baseline, "rules-v1"
    try:
        model = json.loads(Path(MODEL_PATH).read_text(encoding="utf-8"))
        if model["features"] == FEATURES:
            logit = model["intercept"] + sum(w * v for w, v in zip(model["coef"], x))
            learned = 1 / (1 + math.exp(-max(-50, min(50, logit))))
            score = 0.7 * baseline + 0.3 * learned
            mode = "hybrid-v1"
    except (OSError, ValueError, KeyError, TypeError):
        pass
    requested = {normalize(s) for s in need.skills}
    available = {normalize(s) for s in profile.skills}
    return {"score": round(score * 100, 1), "mode": mode,
            "matched_skills": sorted(requested & available), "missing_skills": sorted(requested - available),
            "factors": [{"key": name, "value": round(value * 100, 1), "contribution": round(weight * value * 100, 1)} for name, value, weight in zip(FEATURES, x, BASE_WEIGHTS)],
            "explanation": [f"Совпадает {len(requested & available)} из {len(requested)} навыков", f"Подтверждённый тест: {profile.score:g} из 100", f"Достижений в демореестре ФСП: {len(achievements)}"],
            "notice": "Баллы соответствия — ориентир, а не вероятность трудоустройства. Модель обучена на синтетических данных."}
