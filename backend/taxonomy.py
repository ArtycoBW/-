"""Справочник категорий. Идентификаторы сохраняются в БД и контрактах API."""
from typing import Literal, get_args

Spec = Literal["backend", "frontend", "fullstack", "mobile", "qa", "devops", "data_engineering", "data_science", "cybersecurity", "systems_analysis"]
SPECIALIZATIONS = {
    "backend": ("Бэкенд-разработка", ["Python", "FastAPI", "PostgreSQL", "Docker"]),
    "frontend": ("Фронтенд-разработка", ["TypeScript", "React", "Next.js", "CSS"]),
    "fullstack": ("Фулстек-разработка", ["TypeScript", "React", "Python", "PostgreSQL"]),
    "mobile": ("Мобильная разработка", ["Kotlin", "Swift", "Flutter", "API"]),
    "qa": ("Тестирование и QA", ["Python", "Pytest", "Playwright", "SQL"]),
    "devops": ("DevOps и SRE", ["Linux", "Docker", "Kubernetes", "Terraform"]),
    "data_engineering": ("Инженерия данных", ["SQL", "Python", "Airflow", "Kafka"]),
    "data_science": ("Анализ данных и ML", ["Python", "Pandas", "Scikit-learn", "SQL"]),
    "cybersecurity": ("Информационная безопасность", ["Linux", "OWASP", "Python", "SIEM"]),
    "systems_analysis": ("Системная аналитика", ["SQL", "BPMN", "UML", "OpenAPI"]),
}
assert set(SPECIALIZATIONS) == set(get_args(Spec))

def catalog():
    return [{"id": key, "name": name, "skills": skills} for key, (name, skills) in SPECIALIZATIONS.items()]
