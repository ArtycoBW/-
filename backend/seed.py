"""Идемпотентное заполнение только синтетическими демонстрационными данными."""
import random
import time
from sqlalchemy import select
from backend.db import SessionLocal
from backend.migrate import upgrade
from backend.models import Achievement, Candidate, Challenge, Company, Invitation, Need, User, Vacancy
from backend.security import password_hasher

def seed():
    upgrade()
    rng = random.Random(20261010)
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == "employer@demo.razryad.ru")):
            return {"status": "Демонстрационные данные уже загружены"}
        password = password_hasher.hash("RazryadDemo2026!")
        employer = User(email="employer@demo.razryad.ru", password_hash=password, role="employer", verified=True)
        employer2 = User(email="team@demo.razryad.ru", password_hash=password, role="employer", verified=True)
        db.add_all([employer, employer2])
        db.flush()
        db.add_all([Company(id=employer.id, name="Контур Лаб", description="Демонстрационная продуктовая команда. Создаём сервисы для разработчиков и бизнеса.", city="Москва", contact="hr@demo.razryad.ru"), Company(id=employer2.id, name="Север Технологии", description="Демонстрационная инженерная компания", city="Санкт-Петербург", contact="team@demo.razryad.ru")])
        db.flush()
        names = ["Александр Волков", "Анна Соколова", "Михаил Орлов", "Дарья Лебедева", "Дмитрий Морозов", "Екатерина Белова", "Илья Новиков", "Мария Кузнецова", "Артём Васильев", "Полина Макарова", "Никита Фёдоров", "Алина Попова"]
        cities = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск", "Ростов-на-Дону"]
        specs = {"backend": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "SQL"], "frontend": ["TypeScript", "React", "Next.js", "CSS", "JavaScript", "Git"]}
        for i in range(36):
            user = User(email="candidate@demo.razryad.ru" if i == 0 else f"specialist{i}@example.org", password_hash=password, role="candidate", verified=True)
            db.add(user)
            db.flush()
            spec = "backend" if i % 2 == 0 else "frontend"
            grade = ["middle", "junior", "senior"][(i//2) % 3]
            candidate = Candidate(id=user.id, name=names[i % len(names)], city=cities[i % len(cities)], bio="Демонстрационный профиль. Проектирую надёжные сервисы, разбираю сложные задачи и работаю с командой над качеством продукта.", contact=f"specialist{i}@example.org", specialization=spec, desired_grade=grade, grade=grade, skills=specs[spec][:rng.randint(3,6)], experience={"junior":1,"middle":3,"senior":7}[grade], work_format="remote", salary_min={"junior":80000,"middle":180000,"senior":280000}[grade], score=rng.choice([75,87.5,100]), verified_at=time.time()-86400*rng.randint(1,60), active_at=time.time()-86400*rng.randint(0,35), published=True, consent=True)
            db.add(candidate)
            db.flush()
            if i % 3 == 1:
                candidate.fsp_id = f"DEMO-ATHLETE-{i:04}"
                db.add(Achievement(candidate_id=user.id, external_id=f"demo-result-{i}", title="Кубок по спортивному программированию — демоданные", discipline="Продуктовое программирование" if spec == "frontend" else "Алгоритмическое программирование", date="2026-09-15", place=rng.randint(1,12), participants=128))
            if i == 0:
                db.add(Invitation(company_id=employer2.id, candidate_id=user.id, title="Python-разработчик в продуктовую команду", message="Здравствуйте! В демо-сценарии приглашаем обсудить развитие нашей платформы. Нам важны надёжность API и работа с PostgreSQL. Готовы рассказать о команде и задачах.", contact="team@demo.razryad.ru", salary_min=190000, salary_max=260000))
        for spec, title, grade, low, high in [("backend","Python-разработчик", "middle",180000,260000),("frontend","Фронтенд-разработчик React", "middle",170000,250000),("backend","Старший Python-разработчик","senior",280000,380000),("frontend","Начинающий фронтенд-разработчик","junior",80000,130000),("backend","Разработчик API","junior",90000,140000),("frontend","Ведущий разработчик интерфейсов","senior",270000,370000)]:
            values=dict(company_id=employer.id, title=title, description="Развиваем продукт для инженерных команд. Предстоит проектировать решения, писать тесты, обсуждать архитектуру и улучшать опыт пользователей. Данные вакансии демонстрационные.", specialization=spec, grade=grade, skills=specs[spec][:4], work_format="remote", salary_min=low, salary_max=high)
            db.add(Vacancy(**values))
            if grade == "middle":
                db.add(Need(**values))
        for spec in specs:
            db.add(Challenge(company_id=employer.id, title="Надёжный повтор запроса" if spec == "backend" else "Поиск без устаревших ответов", description="Пользователь выполняет действие несколько раз при нестабильной сети. Опишите, как избежать дублирования и показать корректное состояние интерфейса. Укажите граничные случаи и предложите проверки.", specialization=spec, rubric="Корректность — 40 баллов; граничные случаи — 30; стратегия тестирования — 20; ясность — 10. Проверяет работодатель."))
        db.commit()
        return {"status": "Создано", "candidates":36,"companies":2,"vacancies":6}

if __name__ == "__main__":
    print(seed())
