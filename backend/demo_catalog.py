"""Idempotent fictional catalog. Never rewrites existing users or their activity."""
import random
import time
from uuid import NAMESPACE_URL, uuid5
from sqlalchemy import select, func
from backend import config
from backend.db import SessionLocal
from backend.models import User, Candidate, Company, Achievement, Vacancy, Need, Challenge, Application, ContactGrant, Invitation
from backend.security import password_hasher
from backend.seed import seed


def key(kind, index):
    return uuid5(NAMESPACE_URL, f"razryad/fictional-catalog/v1/{kind}/{index}").hex


COMPANIES = [
    ("Меридиан", "Логистика", "Казань", "планирование маршрутов и отслеживание грузов"),
    ("Листва", "Образование", "Москва", "образовательная платформа с интерактивными заданиями"),
    ("Точка сборки", "Инструменты разработки", "Санкт-Петербург", "инструменты командной разработки и анализа кода"),
    ("Берег", "Городские сервисы", "Ростов-на-Дону", "сервисы для управления городскими пространствами"),
    ("Квантум Софт", "Промышленность", "Екатеринбург", "мониторинг оборудования и планирование обслуживания"),
    ("Полка", "Электронная торговля", "Новосибирск", "каталог товаров и управление заказами магазинов"),
    ("Спектр данных", "Аналитика", "Томск", "обработка событий и продуктовая аналитика"),
    ("Мастерская систем", "B2B-продукты", "Самара", "документооборот и автоматизация рабочих процессов"),
    ("Смена", "HR-технологии", "Краснодар", "планирование команд и развитие сотрудников"),
    ("Атлас медиа", "Медиа", "Нижний Новгород", "платформа публикаций и персональных подписок"),
    ("Открытый маршрут", "Путешествия", "Пермь", "сервисы бронирования и планирования поездок"),
    ("Ритм", "Спорт", "Воронеж", "управление соревнованиями и тренировочными программами"),
]
BACKEND_ROLES = [
    ("Python-разработчик API", ["Python", "FastAPI", "PostgreSQL", "Docker"], "Разрабатывать REST API, описывать контракты и поддерживать интеграционные тесты."),
    ("Разработчик сервисов обработки событий", ["Python", "Redis", "SQL", "Kafka"], "Проектировать обработку событий, повторы запросов и идемпотентные операции."),
    ("Бэкенд-разработчик продуктовой команды", ["Python", "Django", "PostgreSQL", "Git"], "Развивать доменную модель, оптимизировать запросы и участвовать в проектировании новых функций."),
    ("Инженер платформенных сервисов", ["Python", "Docker", "SQL", "Linux"], "Поддерживать внутренние сервисы, измерять задержки и улучшать наблюдаемость приложений."),
]
FRONTEND_ROLES = [
    ("Разработчик интерфейсов React", ["TypeScript", "React", "CSS", "Git"], "Создавать кабинеты пользователей, продумывать состояния загрузки и писать компонентные тесты."),
    ("Frontend-разработчик Next.js", ["TypeScript", "Next.js", "React", "Tailwind CSS"], "Развивать веб-приложение, оптимизировать загрузку страниц и поддерживать дизайн-систему."),
    ("Инженер дизайн-системы", ["TypeScript", "React", "CSS", "Accessibility"], "Проектировать переиспользуемые компоненты, проверять доступность и документировать варианты использования."),
    ("Фронтенд-разработчик аналитических интерфейсов", ["TypeScript", "React", "JavaScript", "D3.js"], "Создавать таблицы и визуализации, управлять сложными фильтрами и синхронизировать состояние интерфейса."),
]

BACKEND_TASKS = [
    ("Маршрут с ограничениями", "Спроектируйте API маршрутов с окнами доставки и ограничением грузоподъёмности. Опишите модель остановок, валидацию конфликтов и тесты изменения маршрута."),
    ("Прогресс учебного курса", "Предложите модель прогресса курса с повторными попытками заданий. Опишите транзакции, правила зачёта и обработку одновременных ответов с двух устройств."),
    ("Очередь анализа репозиториев", "Спроектируйте очередь анализа коммитов: приоритеты, повторные попытки, отмена устаревших работ. Покажите схему данных и проверки идемпотентности."),
    ("Бронирование городского пространства", "Опишите API бронирования площадки по времени. Исключите пересекающиеся брони при одновременных запросах. Приведите ограничения БД и интеграционные тесты."),
    ("Телеметрия оборудования", "Предложите обработку потока измерений с пропусками и дубликатами. Опишите хранение, агрегацию по минутам и оповещение при превышении порога."),
    ("Остатки и резервирование товара", "Спроектируйте резерв товара с истечением срока. Покажите обработку конкурирующих заказов, отмены платежа и повторных уведомлений от платёжной системы."),
    ("Воронка событий", "Опишите расчёт продуктовой воронки по событиям, приходящим с задержкой. Покажите дедупликацию, пересчёт исторических периодов и тесты границ сессии."),
    ("Версии документов", "Спроектируйте хранение версий документа и оптимистическую блокировку. Опишите API конфликтов, восстановление прошлой версии и аудит изменений."),
    ("Расписание команды", "Предложите модель смен с часовыми поясами, перерывами и ограничением часов. Опишите поиск конфликтов, изменение расписания и права доступа."),
    ("Подписка на публикации", "Спроектируйте рассылку новых публикаций подписчикам. Учтите отписку во время отправки, повторы очереди, лимиты и доставку без дубликатов."),
    ("Удержание брони", "Опишите бронирование поездки с временным удержанием места и подтверждением оплаты. Приведите состояния заказа, компенсации и тесты сбоев."),
    ("Турнирная таблица", "Предложите расчёт мест при равенстве очков, штрафах и отменённых матчах. Опишите воспроизводимый пересчёт и журнал решений судей."),
    ("Согласование документов", "Спроектируйте маршрут согласования с последовательными и параллельными этапами. Учтите отзыв документа, делегирование и повторную отправку."),
]
FRONTEND_TASKS = [
    ("Панель диспетчера", "Спроектируйте интерфейс списка доставок с группировкой по статусу. Опишите фильтры в URL, доступность клавиатуры и обновления без скачков прокрутки."),
    ("Редактор учебного ответа", "Разработайте подход к редактору ответа с автосохранением. Учтите потерю сети, конфликт вкладок, восстановление черновика и доступную индикацию статуса."),
    ("Просмотр изменений кода", "Предложите интерфейс сравнения версий файла с комментариями. Опишите виртуализацию длинных файлов, навигацию клавиатурой и фокус при раскрытии строк."),
    ("Календарь бронирования", "Спроектируйте доступный календарь выбора времени и площадки. Учтите занятые интервалы, часовые пояса, мобильный экран и ошибки сервера."),
    ("Графики измерений", "Опишите компонент графика телеметрии с масштабированием и пропусками данных. Предусмотрите текстовую альтернативу, экономную перерисовку и проверки."),
    ("Корзина с изменением цены", "Предложите интерфейс корзины с серверной проверкой цены и наличия. Учтите оптимистическое обновление количества, откат ошибки и доступные уведомления."),
    ("Конструктор отчёта", "Спроектируйте таблицу аналитики с группировками, сортировкой и экспортом. Опишите сохранение конфигурации, загрузку больших данных и пустые состояния."),
    ("История версий документа", "Предложите интерфейс сравнения и восстановления версии документа. Учтите доступность диалога подтверждения, конфликт прав и отмену действия."),
    ("Планировщик смен", "Спроектируйте недельный планировщик с перемещением смен мышью и клавиатурой. Опишите конфликты, откат сохранения и представление на телефоне."),
    ("Лента публикаций", "Предложите ленту с фильтрами и восстановлением позиции после возврата из статьи. Учтите отложенную загрузку медиа, доступность и медленное соединение."),
    ("Форма бронирования поездки", "Спроектируйте многошаговую форму с пассажирами, датами и оплатой. Опишите валидацию, возвращение к шагу, истечение брони и обработку повторного нажатия."),
    ("Живая таблица соревнования", "Предложите интерфейс обновляющейся турнирной таблицы. Предусмотрите устойчивую сортировку, выделение изменений и отключение движения пользователем."),
    ("Рабочий стол согласований", "Спроектируйте список документов с массовыми действиями. Учтите частичные ошибки, ограничения прав, подтверждение выбора и сохранение фильтров."),
]


def populate():
    if not config.DEMO_MODE:
        raise RuntimeError("Каталог разрешён только в демонстрационном окружении")
    seed()
    rng = random.Random(20261011)
    now = time.time()
    password = password_hasher.hash("RazryadDemo2026!")
    with SessionLocal() as db:
        existing = {model: set(db.scalars(select(model.id))) for model in [User, Candidate, Company, Vacancy, Need, Challenge, Achievement, Application, ContactGrant, Invitation]}
        def add(model, index, **values):
            identity = key(model.__tablename__, index)
            if identity not in existing[model]:
                db.add(model(id=identity, **values)); existing[model].add(identity)
            return identity

        company_ids = []
        for i, (name, industry, city, product) in enumerate(COMPANIES):
            identity = key("users", f"company-{i}")
            if identity not in existing[User]:
                db.add(User(id=identity, email=f"catalog.company{i+1}@demo.razryad.ru", role="employer", password_hash=password, verified=False))
                existing[User].add(identity)
            db.flush()
            if identity not in existing[Company]:
                db.add(Company(id=identity, name=name, industry=industry, city=city, contact=f"catalog.company{i+1}@demo.razryad.ru", description=f"Создаём {product}. Продуктовая команда из {12+i*3} человек. Работаем короткими итерациями, обсуждаем решения на ревью и выделяем время на обучение. Учебная компания каталога «Разряд»."))
            company_ids.append(identity)
        db.flush()
        employer = db.scalar(select(User).where(User.email == "employer@demo.razryad.ru"))
        company_ids.append(employer.id)
        vacancy_ids = []
        for i in range(78):
            company_id = company_ids[i % len(company_ids)]
            spec = "backend" if (i // len(company_ids)) % 2 == 0 else "frontend"
            title, skills, tasks = (BACKEND_ROLES if spec == "backend" else FRONTEND_ROLES)[i % 4]
            grade = ["junior", "middle", "senior"][(i//3) % 3]
            work = ["remote", "hybrid", "office"][i % 3]
            low = {"junior":75000,"middle":165000,"senior":265000}[grade] + (i%7)*5000
            company = COMPANIES[i % len(company_ids)] if i % len(company_ids) < 12 else ("Контур Лаб", "B2B", "Москва", "документооборот")
            description = f"Команда: {company[0]}. Наш продукт — {company[3]}.\n\nЗадачи\n{tasks} Участвовать в планировании и обсуждать решения с продуктовой командой.\n\nОжидания\n{', '.join(skills)}; умение объяснять технические решения и работать с обратной связью. Уровень позиции: {grade}.\n\nУсловия\nОфициальное оформление, гибкое начало дня, бюджет на обучение. На собеседовании обсудим проект из вашего портфолио и разберём рабочую задачу."
            values=dict(company_id=company_id,title=title,specialization=spec,grade=grade,skills=skills,work_format=work,salary_min=low,salary_max=low+45000+(i%4)*10000,description=description,created_at=now-3600*(i*7+1))
            vacancy_ids.append(add(Vacancy,i,**values))
            if company_id == employer.id:
                add(Need, i, **values)
        db.flush()
        first = ["Дмитрий", "Максим", "Андрей", "Сергей", "Кирилл", "Алексей", "Михаил", "Иван", "Роман", "Павел", "Егор", "Денис", "Артём", "Владислав", "Глеб"]
        last = ["Лазарев", "Ковалёв", "Смирнов", "Белов", "Титов", "Комаров", "Савельев", "Мельников", "Зайцев", "Панов", "Лебедев", "Соловьёв"]
        female = ["Виктория", "Мария", "Полина", "Дарья", "Екатерина", "Ксения", "Валерия", "Елена", "Анастасия", "Софья", "Алина", "Юлия", "Вероника", "Татьяна", "Ольга"]
        candidates = []
        for i in range(180):
            identity = key("users", f"candidate-{i}")
            email = f"catalog.specialist{i+1}@demo.razryad.ru"
            if identity not in existing[User]:
                db.add(User(id=identity,email=email,role="candidate",password_hash=password,verified=False));existing[User].add(identity)
            db.flush()
            spec = "backend" if i % 2 == 0 else "frontend"
            title, skills, task = (BACKEND_ROLES if spec == "backend" else FRONTEND_ROLES)[(i//2)%4]
            grade = ["junior","middle","senior"][(i//4)%3]
            experience = {"junior":1,"middle":3,"senior":6}[grade] + rng.randrange(2)
            city = COMPANIES[i%12][2]
            woman = i % 3 == 1
            name = (female if woman else first)[i%15] + " " + last[(i//15)%12] + ("а" if woman else "")
            if identity not in existing[Candidate]:
                db.add(Candidate(id=identity,name=name,city=city,bio=f"{title}. Опыт: {experience} лет. В последнем учебном проекте работал{'а' if woman else ''} над продуктом в сфере «{COMPANIES[i%12][1]}». {task} Интересуют задачи с понятной ответственностью за результат, регулярным ревью и общением с пользователями. Профиль создан для демонстрации каталога.",contact=email,specialization=spec,desired_grade=grade,grade=grade,skills=skills+(["SQL"] if spec=="backend" and "SQL" not in skills else []),experience=experience,work_format=["remote","hybrid","office"][i%3],salary_min={"junior":70000,"middle":160000,"senior":255000}[grade]+rng.randrange(9)*5000,score=rng.choice([75,87.5,100]),verified_at=now-86400*rng.randint(3,75),active_at=now-86400*rng.randint(0,24),published=True,consent=True))
            candidates.append(identity)
            db.flush()
            if i % 4 == 0:
                add(Achievement,i,candidate_id=identity,external_id=f"catalog-demo-result-{i}",title=["Командный кубок регионов", "Турнир по алгоритмическому программированию", "Открытый продуктовый хакатон"][i%3]+" · учебный реестр",discipline="Алгоритмическое программирование" if spec=="backend" else "Продуктовое программирование",date="2026-09-12",place=1+i%12,participants=64+i%5*16,source="demo_registry")
        db.flush()
        for i, company_id in enumerate(company_ids):
            for spec, (title, task) in [("backend", BACKEND_TASKS[i]), ("frontend", FRONTEND_TASKS[i])]:
                add(Challenge, f"{i}-{spec}",company_id=company_id,title=title,description=task,specialization=spec,rubric="Корректность — 40; граничные случаи — 25; тестирование — 20; ясность решения — 15. Результат проверяет работодатель.")
        for i, vacancy_id in enumerate(vacancy_ids):
            if i % len(company_ids) != 12:
                continue
            candidate_id = candidates[i]
            new_application = key("applications", i) not in existing[Application]
            add(Application,i,candidate_id=candidate_id,vacancy_id=vacancy_id,status=["sent","reviewing","interview"][i%3],letter="Интересны задачи вашей команды. В профиле указаны используемые технологии и результат теста. Готов обсудить подход к реализации и показать учебный проект.")
            if new_application and not db.scalar(select(ContactGrant).where(ContactGrant.company_id==employer.id,ContactGrant.candidate_id==candidate_id)):
                add(ContactGrant,i,company_id=employer.id,candidate_id=candidate_id,reason="application")
        candidate = db.scalar(select(User).where(User.email=="candidate@demo.razryad.ru"))
        for i in range(3):
            add(Invitation,i,company_id=company_ids[i],candidate_id=candidate.id,title=BACKEND_ROLES[i][0],message=f"Нам интересен ваш опыт с Python и API. В команде «{COMPANIES[i][0]}» предстоит работать над продуктом: {COMPANIES[i][3]}. Предлагаем обсудить задачи и ожидания на короткой встрече.",contact=f"catalog.company{i+1}@demo.razryad.ru",salary_min=195000+i*15000,salary_max=255000+i*15000)
        db.commit()
        return {model.__tablename__:db.scalar(select(func.count()).select_from(model)) for model in [Candidate,Company,Vacancy,Challenge,Achievement]}


if __name__ == "__main__":
    print(populate())
