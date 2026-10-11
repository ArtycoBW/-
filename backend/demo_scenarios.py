"""Prepare explicit, fictional review accounts without resetting other users."""
import time
from sqlalchemy import select
from backend import config
from backend.db import SessionLocal
from backend.models import User, Candidate, Company, Achievement
from backend.security import password_hasher
from backend.seed import seed


def prepare():
    if not config.DEMO_MODE:
        raise RuntimeError("Подготовка разрешена только при DEMO_MODE=true")
    seed()
    with SessionLocal() as db:
        specs = [
            ("candidate@demo.razryad.ru", "Александр Волков", "Ростов-на-Дону", "backend", "middle", 4, 190000,
             ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "SQL"],
             "Демонстрационный профиль. Разрабатываю API для B2B-сервисов: очереди задач, интеграции и обработка платежных событий. В учебном проекте спроектировал идемпотентную обработку вебхуков и нагрузочные проверки. Ищу продуктовую команду, где можно отвечать за сервис от схемы данных до эксплуатации."),
            ("frontend@demo.razryad.ru", "Анна Соколова", "Казань", "frontend", "middle", 3, 175000,
             ["TypeScript", "React", "Next.js", "CSS", "JavaScript", "Git"],
             "Демонстрационный профиль. Создаю доступные интерфейсы, дизайн-системы и кабинеты с большим количеством данных. В портфолио: интерактивная карта и панель аналитики. Уделяю внимание клавиатурной навигации, тестам и скорости загрузки. Хочу развивать сложный продукт вместе с дизайнерами и аналитиками."),
            ("starter@demo.razryad.ru", "Илья Новиков", "Новосибирск", "backend", None, 1, 85000,
             ["Python", "SQL", "Git", "Docker"],
             "Демонстрационный профиль начинающего специалиста. Написал сервис учёта тренировок на Python и PostgreSQL, добавил Docker и тесты API. Изучаю транзакции и сетевые протоколы. Ищу первую продуктовую команду с код-ревью. Грейд ещё не подтверждён: этот аккаунт предназначен для прохождения теста."),
        ]
        for email, name, city, specialization, grade, experience, salary, skills, bio in specs:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(email=email, role="candidate", password_hash=password_hasher.hash("RazryadDemo2026!"), verified=True)
                db.add(user); db.flush()
            profile = db.get(Candidate, user.id)
            if profile is not None:
                continue
            if profile is None:
                profile = Candidate(id=user.id); db.add(profile)
            for key, value in dict(name=name, city=city, specialization=specialization, desired_grade=grade or "junior", experience=experience, salary_min=salary, skills=skills, bio=bio, contact=email, work_format="remote", published=True, consent=True).items():
                setattr(profile, key, value)
            if grade and not profile.grade:
                profile.grade, profile.score, profile.verified_at = grade, 87.5, time.time() - 86400 * 7
            profile.active_at = time.time()
            if email.startswith("frontend") and not db.scalar(select(Achievement).where(Achievement.candidate_id == user.id, Achievement.external_id == "demo-pixipod-frontend")):
                db.add(Achievement(candidate_id=user.id, external_id="demo-pixipod-frontend", title="Командный кубок по продуктовому программированию · демо", discipline="Продуктовое программирование", date="2026-09-20", place=3, participants=64))
        first = db.scalar(select(User).where(User.email == "employer@demo.razryad.ru"))
        second = db.scalar(select(User).where(User.email == "team@demo.razryad.ru"))
        for user, description, industry in [
            (first, "Демонстрационная команда B2B-продуктов. Разрабатываем сервисы документооборота и кабинеты для малого бизнеса. 24 инженера, небольшие продуктовые группы, удалённая работа, код-ревью и автоматические проверки перед выпуском.", "B2B-сервисы и документооборот"),
            (second, "Демонстрационная команда, которая создаёт инструменты для логистики: маршрутизация, статусы заказов и интеграции с перевозчиками. Ищем разработчиков, которым интересны надёжные API и работа с событиями.", "Логистика и интеграции"),
        ]:
            company = db.get(Company, user.id)
            if not company.description:
                company.description, company.industry = description, industry
        db.commit()
        return {"status": "Готово", "review_accounts": 5, "data": "fictional"}


if __name__ == "__main__":
    print(prepare())
