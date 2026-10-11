"""Воспроизводимый CPU-бенчмарк на синтетике; не оценка реального найма.

Запуск: python -m ml.train. Все разбиения создаются до генерации пар.
Идентификаторы потребностей и кандидатов между train/validation/test не пересекаются.
"""
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
from scipy.special import expit
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, cohen_kappa_score, ndcg_score, roc_auc_score

from backend.assessment import generate_questions
from backend.taxonomy import SPECIALIZATIONS
from backend.matching import BASE_WEIGHTS, FEATURES

SEED = 20261010
ROOT = Path(__file__).resolve().parent


def dataset(seed, queries):
    rng = np.random.default_rng(seed)
    rows, labels, relevance, groups = [], [], [], []
    for query in range(queries):
        # Каждый query содержит собственных 32 кандидатов одной категории.
        x = np.column_stack([
            rng.binomial(5, rng.uniform(.3, .8), 32) / 5,
            rng.uniform(.7, 1, 32), np.ones(32), rng.uniform(.1, 1, 32),
            rng.binomial(3, .18, 32) / 3, rng.binomial(1, .65, 32),
        ])
        # Синтетический «эксперт» задаётся до обучения, со случайным шумом.
        utility = (2.4 * x[:, 0] + .9 * x[:, 1] + .2 * x[:, 3] + .3 * x[:, 4]
                   + .5 * x[:, 5] + .35 * x[:, 0] * x[:, 5] + rng.normal(0, .12, 32))
        probability = expit((utility - 2.55) * 2)
        y = rng.binomial(1, probability)
        rel = np.digitize(utility, [1.7, 2.5, 3.1])
        rows.extend(x.tolist()); labels.extend(y.tolist()); relevance.extend(rel.tolist())
        groups.extend([query] * 32)
    return np.array(rows), np.array(labels), np.array(relevance), np.array(groups)


def ranking_metrics(scores, relevance, groups):
    ndcg, precision = [], []
    for group in np.unique(groups):
        mask = groups == group
        s, r = scores[mask], relevance[mask]
        ndcg.append(ndcg_score([r], [s], k=5))
        precision.append(float(np.mean(r[np.argsort(-s)[:5]] >= 2)))
    return {"ndcg_at_5": round(float(np.mean(ndcg)), 4),
            "precision_at_5": round(float(np.mean(precision)), 4),
            "queries": len(ndcg)}


def assessment_benchmark():
    rng = np.random.default_rng(SEED + 9)
    # 1 200 виртуальных участников; ответы генерирует заданная IRT-модель.
    ability = rng.normal(0, 1.4, 1200)
    difficulty = np.array([-.8, -.4, 0, .2, -.8, -.4, 0, .2])
    probabilities = expit(1.65 * (ability[:, None] - difficulty))
    first = rng.binomial(1, probabilities)
    second = rng.binomial(1, probabilities)
    score1, score2 = first.mean(axis=1), second.mean(axis=1)
    item_total = [float(spearmanr(first[:, i], np.delete(first, i, axis=1).sum(axis=1)).statistic) for i in range(8)]
    passing1, passing2 = score1 >= .7, score2 >= .7
    blueprint_equal = 0
    forms = set()
    for spec in SPECIALIZATIONS:
        for grade in ["junior", "middle", "senior"]:
            reference = None
            for seed in range(100):
                q = generate_questions(spec, grade, seed)
                blueprint = sorted((x["family"], x["difficulty"]) for x in q)
                if reference is None: reference = blueprint
                blueprint_equal += int(blueprint == reference)
                forms.add(hashlib.sha256(json.dumps(q, sort_keys=True, ensure_ascii=False).encode()).hexdigest())
    return {"source": "Симуляция IRT, не эмпирическая психометрическая валидация", "virtual_participants":1200,
            "forms_generated":len(SPECIALIZATIONS)*300, "unique_forms":len(forms), "equal_blueprints":blueprint_equal,
            "test_retest_spearman": round(float(spearmanr(score1, score2).statistic),4),
            "pass_agreement":round(float(accuracy_score(passing1,passing2)),4),
            "pass_kappa":round(float(cohen_kappa_score(passing1,passing2)),4),
            "item_total_correlations":[round(x,4) for x in item_total],
            "mean_absolute_retest_difference_points":round(float(np.mean(abs(score1-score2))*100),2),
            "limitation":"Короткий тест чувствителен к случайной ошибке. Порог 70% — продуктовая гипотеза; требуется пилот, экспертная разметка и калибровка по каждому грейду."}


def main():
    started = time.perf_counter()
    train = dataset(SEED, 160)
    validation = dataset(SEED + 1, 40)
    test = dataset(SEED + 2, 60)
    model = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED).fit(train[0],train[1])
    # Один заранее заданный набор гиперпараметров; test не используется для выбора.
    predicted = model.predict_proba(test[0])[:, 1]
    baseline = test[0] @ np.array(BASE_WEIGHTS)
    hybrid = .7 * baseline + .3 * predicted
    artifact = {"version":"1.0.0", "seed":SEED, "features":FEATURES,
                "coef":model.coef_[0].tolist(),"intercept":float(model.intercept_[0]),
                "training_source":"synthetic-v1", "training_pairs":len(train[0]),
                "limits":"Только синтетическая проверка. Не использовать для автоматического отказа в найме."}
    ROOT.mkdir(exist_ok=True)
    model_bytes=(json.dumps(artifact,ensure_ascii=False,indent=2)+"\n").encode()
    (ROOT/'model.json').write_bytes(model_bytes)
    metrics = {"seed":SEED,"dataset":"synthetic-v1","split_unit":"Непересекающиеся потребности и кандидаты",
               "train_pairs":len(train[0]),"validation_pairs":len(validation[0]),"test_pairs":len(test[0]),
               "test_queries":60,"model_sha256":hashlib.sha256(model_bytes).hexdigest(),
               "model":"LogisticRegression(C=1.0), 6 признаков, CPU",
               "validation_auc":round(float(roc_auc_score(validation[1],model.predict_proba(validation[0])[:,1])),4),
               "test_auc":round(float(roc_auc_score(test[1],predicted)),4),
               "test_brier":round(float(brier_score_loss(test[1],predicted)),4),
               "baseline":ranking_metrics(baseline,test[2],test[3]),
               "learned":ranking_metrics(predicted,test[2],test[3]),
               "hybrid":ranking_metrics(hybrid,test[2],test[3]),
               "without_fsp":ranking_metrics(.7*(baseline-.08*test[0][:,4])+.3*model.predict_proba(test[0]*np.array([1,1,1,1,0,1]))[:,1],test[2],test[3]),
               "assessment":assessment_benchmark(),
               "limitations":["Метки созданы программным генератором, не работодателями.","Валидация подтверждает воспроизводимость и соответствие синтетическому сценарию, не эффективность реального найма.","Защищённые признаки и контакты не поступают в модель; отсутствие признаков само по себе не доказывает отсутствие смещения."]}
    (ROOT/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({"elapsed_seconds":round(time.perf_counter()-started,2),"python":platform.python_version(),"metrics":metrics},ensure_ascii=False,indent=2))


if __name__ == "__main__": main()
