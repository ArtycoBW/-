"""Export a private expert-review kit, without claiming validated professional grades."""
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.assessment import BANK_VERSION, generate_questions
from backend.taxonomy import SPECIALIZATIONS

target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".local/assessment-review")
target.mkdir(parents=True, exist_ok=False)
items = []
for spec in SPECIALIZATIONS:
    for grade in ("junior", "middle", "senior"):
        for seed in (71, 193, 541):
            for question in generate_questions(spec, grade, seed):
                items.append({"review_id": f"{spec}-{grade}-{seed}-{question['id']}", "specialization": spec, "grade": grade, "bank_version": BANK_VERSION, **question})
(target / "questions-private.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
with (target / "reviews.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    fields = ["review_id", "expert_id", "correct_answer_0_1", "clarity_1_5", "professional_relevance_1_5", "grade_fit_1_5", "comment"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows({"review_id": item["review_id"]} for item in items)
(target / "README.txt").write_text("Материалы содержат ключи ответов: только для доверенных экспертов, не публиковать.\nНужно минимум два независимых профильных эксперта на направление. Сначала оценить независимо, затем разобрать расхождения. Зафиксировать опыт экспертов и согласие. Поля 1–5: 1 — неприемлемо, 5 — соответствует. correct_answer: 0 — ошибка, 1 — верно. Выборка трёх вариантов не доказывает покрытие профессии. После исправлений повторить проверку и пилот: трудность, различающая способность, надёжность, расхождение категорий с внешней оценкой. Не менять банк и порог по финальному test.\n", encoding="utf-8")
print(f"Prepared {len(items)} questions in {target}")
