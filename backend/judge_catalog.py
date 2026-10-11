"""Сценарный набор комиссии. Только вымышленные данные, только DEMO_MODE.

Идемпотентно: не меняет заполненные профили, статусы и отозванные согласия.
Новые связи согласия создаются лишь вместе с новым исходным действием.
"""
import time
from uuid import NAMESPACE_URL, uuid5
from sqlalchemy import select, func
from backend import config, models as m
from backend.db import SessionLocal
from backend.taxonomy import SPECIALIZATIONS
from backend.security import password_hasher
from backend.assessment import generate_questions, evaluate, BANK_VERSION
from backend.demo_catalog import populate as base_catalog
from backend.demo_scenarios import prepare as demo_scenarios

TASKS = {
    "backend": [("Доставка событий", "Спроектируйте outbox для платежей: транзакция, повторная доставка, дедупликация и восстановление после сбоя."), ("Поиск по каталогу", "Предложите API поиска по каталогу с курсорной пагинацией. Учтите изменение данных между страницами и план индексов."), ("Лимиты клиента", "Реализуйте распределённый лимит запросов с разными квотами клиентов. Объясните поведение при недоступности Redis.")],
    "frontend": [("Доступный мастер", "Спроектируйте многошаговую форму с клавиатурной навигацией, серверной валидацией и сохранением черновика."), ("Лента событий", "Разработайте виртуализированную ленту событий с сохранением позиции при появлении новых записей."), ("Конфликт правок", "Предложите интерфейс разрешения конфликта параллельного редактирования документа: сравнение версий и явное подтверждение.")],
    "fullstack": [("Бронирование мест", "Спроектируйте путь от выбора места до оплаты. Учтите гонку двух покупателей, TTL брони и повтор callback оплаты."), ("Совместный документ", "Опишите серверный контракт и клиентский интерфейс совместного редактирования. Учтите офлайн-режим и конфликты."), ("Импорт данных", "Создайте дизайн API и экрана пакетного импорта CSV с предварительной проверкой, отчётом об ошибках и безопасным повтором.")],
    "mobile": [("Офлайн-доставка", "Опишите очередь изменений курьера при потере сети: порядок доставки, разрешение конфликтов и восстановление после закрытия приложения."), ("Экономия батареи", "Спроектируйте сбор координат с учётом разрешений, фоновых ограничений ОС, расхода батареи и удаления истории."), ("Доступный экран", "Предложите мобильный экран оплаты, доступный со скринридером и большим системным шрифтом. Учтите повторное нажатие и обрыв сети.")],
    "qa": [("План проверки платежа", "Составьте тест-план платежного API: идемпотентность, сумма, валюта, callback, сетевые сбои. Выделите приоритеты автоматизации."), ("Нестабильный тест", "Разберите стратегию поиска flaky-теста в браузере: ожидания, изоляция состояния, часы и диагностика без увеличения timeout."), ("Матрица доступа", "Составьте негативные проверки разграничения прав кандидата и работодателя, включая подмену ID и отзыв ранее выданного согласия.")],
    "devops": [("Восстановление БД", "Подготовьте план проверки восстановления PostgreSQL из резервной копии. Зафиксируйте RPO, RTO, контроль целостности и переключение."), ("Безостановочный релиз", "Спроектируйте rolling deployment с миграцией схемы: совместимость версий, readiness, откат и наблюдаемость."), ("Бюджет ошибок", "Предложите SLO для API подбора: сигналы, окна расчёта error budget, алерты и порядок реакции дежурного.")],
    "data_engineering": [("Поздние события", "Спроектируйте pipeline аналитики заказов с опоздавшими событиями. Объясните watermark, повторный расчёт и дедупликацию."), ("Контроль качества", "Предложите проверки качества витрины: свежесть, уникальность, полнота, контроль дрейфа схемы и карантин строк."), ("Смена схемы", "Опишите совместимую эволюцию Kafka-события и миграцию потребителей без потери данных.")],
    "data_science": [("Честная валидация", "Спроектируйте разбиение для модели ранжирования кандидатов без утечки между компаниями и кандидатами. Выберите baseline и метрики."), ("Дрейф модели", "Предложите мониторинг модели после запуска: дрейф признаков, доступность меток, сегменты качества и правило отката."), ("Несбалансированные классы", "Опишите обучение модели редких событий: выбор метрики, настройка порога на validation, калибровка и проверка стоимости ошибок.")],
    "cybersecurity": [("Модель угроз", "Составьте модель угроз для сервиса найма: активы, границы доверия, IDOR, сессии, файлы резюме и приоритетные меры защиты."), ("Ротация секретов", "Опишите безопасную ротацию ключа интеграции без простоя: два ключа, ограничение прав, аудит, отзыв и проверка потребителей."), ("Расследование входа", "Предложите план расследования подозрительных входов: минимальный набор журналов, сохранение доказательств и защита персональных данных.")],
    "systems_analysis": [("Контракт согласия", "Опишите состояния адресного согласия на контакты, переходы и API. Разделите согласие на публикацию и передачу конкретной компании."), ("Согласование требований", "Подготовьте критерии приёмки для поиска специалистов: фильтры, пустые результаты, объяснение ранга и производительность."), ("Интеграция реестра", "Спроектируйте контракт получения достижений: стабильные идентификаторы, версия схемы, пагинация, повторы и удалённые записи.")],
}

def identity(kind, key):
    return uuid5(NAMESPACE_URL, f"razryad/judge-catalog/v2/{kind}/{key}").hex

def populate():
    if not config.DEMO_MODE:
        raise RuntimeError("Сценарии комиссии разрешены только в DEMO_MODE")
    base_catalog()
    demo_scenarios()
    now = time.time()
    password = password_hasher.hash("RazryadDemo2026!")
    with SessionLocal() as db:
        def add(model, key, **values):
            uid = identity("users" if model is m.Candidate else model.__tablename__, key)
            row = db.get(model, uid)
            if row: return row, False
            row = model(id=uid, **values); db.add(row); db.flush()
            return row, True

        companies = list(db.scalars(select(m.Company).order_by(m.Company.name)))
        owners = [db.scalar(select(m.User).where(m.User.email == email)).id for email in ["employer@demo.razryad.ru", "team@demo.razryad.ru"]]
        vacancies, tasks, people = {}, {}, []
        cities = ["Ростов-на-Дону", "Москва", "Казань", "Томск", "Санкт-Петербург", "Екатеринбург"]
        names = ["Алексей Громов", "Мария Ветрова", "Никита Лукин", "Елена Миронова", "Павел Елисеев", "Анна Корнеева", "Денис Белов", "Полина Жукова", "Роман Тихонов", "Дарья Савина"]
        for index, (spec, (label, skills)) in enumerate(SPECIALIZATIONS.items()):
            tasks[spec], vacancies[spec] = [], []
            for n in range(12):
                owner = owners[n % 2] if n < 6 else companies[(index+n) % len(companies)].id
                company = db.get(m.Company, owner)
                grade = ["junior", "middle", "senior"][n % 3]
                low = [85000, 175000, 275000][n % 3] + (index % 4)*5000
                title = f"{label} · {['старт карьеры', 'продуктовая команда', 'ведущая роль'][n % 3]}"
                values = dict(company_id=owner, title=title, specialization=spec, grade=grade, skills=skills, work_format=["remote", "hybrid", "office"][(n//3)%3], salary_min=low, salary_max=low+60000, description=f"{company.name}: развиваем продукт для команд и их клиентов.\n\nЗадачи\n{TASKS[spec][n%3][1]} Работать в паре с инженерами и владельцем продукта.\n\nОжидания\n{', '.join(skills)}. Умение обосновать решение и проверить его на граничных случаях.\n\nУсловия\nГибкое начало дня, наставник, бюджет на обучение, прозрачные цели на испытательный срок.", created_at=now-(index*12+n)*3600)
                vacancy, _ = add(m.Vacancy, f"{spec}-{n}", **values); vacancies[spec].append(vacancy)
                if n < 6: add(m.Need, f"{spec}-{n}", **values)
            for n in range(6):
                title, task = TASKS[spec][n%3]
                row,_ = add(m.Challenge, f"{spec}-{n}", company_id=owners[n//3], title=f"{title} · {['платформа', 'сервис'][n//3]}", description=task+" Укажите предположения, опишите хотя бы два граничных случая и приложите план проверок. Можно использовать псевдокод.", specialization=spec, rubric="Корректность — 40; граничные случаи — 25; проверяемость — 20; ясность — 15. Оценку и комментарий даёт команда.")
                tasks[spec].append(row)
            for n in range(24):
                key=f"{spec}-{n}"
                email = f"judge.{spec}@demo.razryad.ru" if n==0 else f"track.{spec}{n}@demo.razryad.ru"
                user,_=add(m.User,key,email=email,password_hash=password,role="candidate",verified=True)
                grade=["middle","junior","senior"][n%3]
                person,created=add(m.Candidate,key,name=names[index] if n==0 else names[(index+n)%10]+f" · {n+1}",city=cities[(n+index)%6],bio=f"Специализация: {label}. Развиваю {TASKS[spec][n%3][0].lower()}. Работаю с {', '.join(skills[:3])}. Ценю ревью, проверяемые решения и ответственность за результат. Учебный профиль комиссии; история и достижения вымышленные.",contact=email,specialization=spec,desired_grade=grade,grade=grade,skills=skills[:3]+([skills[3]] if n%4 else []),experience={"junior":1,"middle":4,"senior":8}[grade],work_format=["remote","hybrid","office"][n%3],salary_min={"junior":80000,"middle":170000,"senior":265000}[grade],score=[75,87.5,100][n%3],verified_at=now-86400*(10+n),active_at=now-86400*(n%12),published=True,consent=True)
                if created:
                    questions=generate_questions(spec,grade,10000+index*24+n)
                    correct_count=[6,7,8][n%3]
                    answers={q['id']:q['answer'] if i<correct_count else "-99999" for i,q in enumerate(questions)}
                    score,_=evaluate(questions,answers)
                    add(m.Attempt,key,candidate_id=person.id,specialization=spec,grade=grade,seed=10000+index*24+n,bank_version=BANK_VERSION,questions=questions,answers=answers,started_at=person.verified_at-900,expires_at=person.verified_at+900,submitted_at=person.verified_at,score=score,passed=True)
                    if n%4==0:
                        add(m.Achievement,key,candidate_id=person.id,external_id=f"judge-result-{key}",title="Учебный командный кубок",discipline="Продуктовое программирование",date="2026-09-12",place=2+n,participants=128,source="demo_registry")
                if n==0: people.append(person)
        # Наполненные сценарии только для явно перечисленных учебных аккаунтов.
        for email in ["candidate@demo.razryad.ru","frontend@demo.razryad.ru","starter@demo.razryad.ru"]:
            user=db.scalar(select(m.User).where(m.User.email==email))
            if user: people.append(db.get(m.Candidate,user.id))
        for person in people:
            spec=person.specialization
            for i,task in enumerate(tasks[spec][:4]):
                score=[None,85,65,95][i]
                add(m.Submission,f"{person.id}-{i}",candidate_id=person.id,challenge_id=task.id,answer=f"Учебный разбор: «{task.title}». Сначала фиксирую входные данные и инварианты. {TASKS[spec][i%3][1]} Отдельно проверяю пустой набор, повторный запрос и частичный отказ. Для каждого случая фиксирую ожидаемый результат; интеграционные проверки запускаю на изолированных данных. Ограничения и компромиссы документирую рядом с решением.",score=score,feedback="" if score is None else "Структура решения понятна. Хорошо выделены границы ответственности. Добавьте конкретный пример входных данных и измеримый критерий успешного восстановления." ,created_at=now-86400*(i+1))
            for i,vacancy in enumerate(vacancies[spec][:6]):
                row,created=add(m.Application,f"{person.id}-{i}",candidate_id=person.id,vacancy_id=vacancy.id,status=["sent","reviewing","interview","rejected","withdrawn","reviewing"][i],letter=f"Здравствуйте! Мне интересна {vacancy.title.lower()}. Работаю с {', '.join(person.skills)}. Готов обсудить задачу из практики и показать, как проверяю граничные случаи. Учебный отклик для проверки сценария.",created_at=now-3600*(i+1))
                if created and i not in [3,4] and not db.scalar(select(m.ContactGrant).where(m.ContactGrant.company_id==vacancy.company_id,m.ContactGrant.candidate_id==person.id)):
                    db.add(m.ContactGrant(company_id=vacancy.company_id,candidate_id=person.id,reason="application"));db.flush()
            if person.grade:
                for i,company in enumerate(companies[:8]):
                    status=["sent","viewed","accepted","declined","withdrawn","sent","viewed","sent"][i]
                    # Не создаём два активных приглашения одной компании одному человеку.
                    prior=db.scalar(select(m.Invitation).where(m.Invitation.company_id==company.id,m.Invitation.candidate_id==person.id))
                    if prior: continue
                    row,created=add(m.Invitation,f"{person.id}-{i}",company_id=company.id,candidate_id=person.id,title=f"{SPECIALIZATIONS[spec][0]} в {company.name}",message=f"Здравствуйте, {person.name.split()[0]}! Нас заинтересовали ваши навыки: {', '.join(person.skills)}. Предлагаем обсудить работу над продуктом и вашу задачу из практики. Расскажем о команде, процессе ревью и целях первых месяцев.",contact=company.contact,salary_min=person.salary_min+15000,salary_max=person.salary_min+85000,status=status,created_at=now-3600*(i+2),updated_at=now-3600*i)
                    if created and status=="accepted" and not db.scalar(select(m.ContactGrant).where(m.ContactGrant.company_id==company.id,m.ContactGrant.candidate_id==person.id)):
                        db.add(m.ContactGrant(company_id=company.id,candidate_id=person.id,reason="invitation"));db.flush()
        db.commit()
        return {model.__tablename__:db.scalar(select(func.count()).select_from(model)) for model in [m.Candidate,m.Company,m.Vacancy,m.Challenge,m.Achievement,m.Submission,m.Application,m.Invitation]}

if __name__ == "__main__": print(populate())
