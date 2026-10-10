"""Семейства эквивалентных задач: параметры меняют ответ, чертёж сохраняется."""
import math
import random

BANK_VERSION = "1.0"
GRADES = {"junior": 1, "middle": 2, "senior": 3}

def generate_questions(specialization: str, grade: str, seed: int) -> list[dict]:
    rng = random.Random(seed)
    level = GRADES[grade]
    questions = []

    def add(family, skill, text, answer, explanation):
        questions.append({"id": f"q{len(questions)+1}", "family": family,
                          "skill": skill, "text": text, "answer": str(answer),
                          "explanation": explanation, "difficulty": level})

    for repeat in range(2):
        n, step = rng.randint(8, 22) * level, rng.randint(2, 5)
        if level == 1:
            add(f"loop-{repeat}", "Алгоритмы", f"Цикл обрабатывает индексы от 0 до {n-1} включительно с шагом {step}. Сколько итераций выполнится? Ответ — целое число.", math.ceil(n / step), "Количество итераций равно округлению n/шага вверх.")
        elif level == 2:
            add(f"loop-{repeat}", "Алгоритмы", f"Внешний цикл: i от 1 до {n}. Внутренний: j от 1 до i. Сколько всего раз выполнится тело внутреннего цикла?", n * (n + 1) // 2, "Сумма 1 + 2 + … + n равна n(n+1)/2.")
        else:
            power = rng.randint(5, 12)
            add(f"loop-{repeat}", "Алгоритмы", f"Бинарный поиск в отсортированном массиве из {2**power-1} элементов. Каково максимальное число сравнений с центральным элементом до нахождения ключа или исчерпания диапазона?", power, "Для 2^k−1 элементов максимальная глубина дерева поиска равна k.")

        values = [rng.randint(1, 10 * level) for _ in range(7 + level)]
        threshold = rng.randint(3, 8 * level)
        if specialization == "backend":
            add(f"data-{repeat}", "Python", f"Дан список Python: {values}. Чему равно sum(x for x in values if x > {threshold})?", sum(x for x in values if x > threshold), "Отбираем значения строго больше порога, затем суммируем.")
            a, b = rng.randint(3, 15), rng.randint(2, 8)
            if level == 1:
                add(f"storage-{repeat}", "SQL", f"В таблице {a} групп, в каждой по {b} строки. Запрос SELECT DISTINCT group_id FROM items вернул все группы. Сколько строк в результате?", a, "DISTINCT оставляет один экземпляр каждого group_id.")
            elif level == 2:
                add(f"storage-{repeat}", "SQL", f"В A есть {a} строк с key=1, в B — {b} строк с key=1. Других строк нет. Сколько строк вернёт INNER JOIN A JOIN B ON A.key=B.key?", a * b, "Все a строк соединяются со всеми b строками: a×b.")
            else:
                add(f"storage-{repeat}", "Надёжность", f"Сервис использует transactional outbox и дедупликацию по event_id. {a} уникальных событий доставлены по {b} раза каждое. Сколько бизнес-операций выполнится при атомарной дедупликации и успешной обработке?", a, "При атомарной дедупликации каждое уникальное событие выполняется один раз.")
        else:
            add(f"data-{repeat}", "JavaScript", f"Массив JavaScript: {values}. Чему равен результат values.filter(x => x > {threshold}).length?", len([x for x in values if x > threshold]), "filter оставляет значения строго больше порога; length считает их.")
            n, delta = rng.randint(2, 20), rng.randint(2, 6)
            if level == 1:
                add(f"state-{repeat}", "CSS", f"Контейнер width: {n*20}px, box-sizing: border-box, padding: {delta}px с каждой стороны, border: 1px. Какова ширина области содержимого?", n * 20 - 2 * delta - 2, "Из общей ширины border-box вычитаются два padding и две границы.")
            elif level == 2:
                add(f"state-{repeat}", "React", f"В React state count={n}. В одном обработчике трижды вызывается setCount(c => c + {delta}). Чему будет равен count после пакетного обновления?", n + delta * 3, "Функциональные обновления последовательно используют предыдущий результат.")
            else:
                add(f"state-{repeat}", "Надёжность", f"Клиент принимает ответы запросов только с текущим requestId. Запущено {n} запросов с возрастающими ID; ответы приходят в обратном порядке. Сколько ответов будет применено, если текущий ID — последний запущенный и после ответа он не меняется?", 1, "Только ответ с последним requestId проходит проверку; остальные устарели.")
        capacity, demand, seconds = rng.randint(4, 15), rng.randint(18, 30), rng.randint(2, 6)
        if level == 1:
            add(f"limits-{repeat}", "Безопасность", f"Лимит — {capacity} запросов в минуту, счётчик начинается с нуля. Пришло {demand} запросов за одну минуту. Сколько нужно отклонить?", max(0, demand - capacity), "Запросы сверх лимита отклоняются.")
        elif level == 2:
            add(f"limits-{repeat}", "Надёжность", f"Кэш записи живёт {capacity} секунд. Запись создана в t={seconds}; срок истекает при t >= created+TTL. В какой целый момент t запись впервые устареет?", capacity + seconds, "Время истечения — время записи плюс TTL.")
        else:
            attempts = rng.randint(3, 6)
            add(f"limits-{repeat}", "Надёжность", f"Паузы перед повторными запросами: {seconds}, {seconds*2}, {seconds*4}, … секунд. Сколько секунд суммарно займут {attempts} пауз без jitter и верхнего ограничения?", seconds * (2**attempts - 1), "Сумма геометрической прогрессии b(2^n−1).")
    rng.shuffle(questions)
    return questions

def public_questions(questions):
    return [{k: v for k, v in q.items() if k not in {"answer", "explanation", "family"}} for q in questions]

def evaluate(questions, answers):
    outcomes = []
    for q in questions:
        value = str(answers.get(q["id"], "")).strip().replace(",", ".")
        try:
            correct = float(value) == float(q["answer"]) and math.isfinite(float(value))
        except ValueError:
            correct = False
        outcomes.append({"id": q["id"], "skill": q["skill"], "correct": correct})
    return round(100 * sum(q["correct"] for q in outcomes) / len(questions), 2), outcomes
