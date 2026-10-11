"""Локальный разбор текстового PDF. Все извлечённые поля — редактируемые гипотезы."""
import re
from backend.taxonomy import SPECIALIZATIONS

def extract_resume(text: str):
    known = sorted({skill for _, skills in SPECIALIZATIONS.values() for skill in skills} | {"Django", "Git", "JavaScript", "Redis", "SQL", "C++", "Go", "Java", "Rust"})
    skills = [skill for skill in known if re.search(r"(?<![\w])"+re.escape(skill)+r"(?![\w])",text,re.I)]
    emails=re.findall(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",text)
    phones=re.findall(r"\+7[\s(.-]*\d{3}[\s).\-]*\d{3}[\s.\-]*\d{2}[\s.\-]*\d{2}",text)
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    name=next((line for line in lines if re.fullmatch(r"[А-ЯЁA-Z][а-яёa-z-]+(?:\s+[А-ЯЁA-Z][а-яёa-z-]+){1,3}",line)),"")
    experience=re.search(r"(?:опыт|стаж)(?:\s+работы)?\s*[:—-]?\s*(\d{1,2})\s*(?:лет|год|года)",text,re.I)
    grade=next((key for key in ['senior','middle','junior'] if re.search(r'\b'+key+r'\b',text,re.I)),None)
    roles=[name for name,_ in SPECIALIZATIONS.values() if name.casefold() in text.casefold()]
    soft_skills=[label for label,pattern in [('Работа в команде',r'команд\w* работ|работ\w* в команд'),('Коммуникация',r'коммуникац'),('Наставничество',r'наставнич|ментор'),('Планирование',r'планирован') ] if re.search(pattern,text,re.I)]
    return {'name':name[:120],'bio':text[:3000],'skills':skills,'contact':emails[0] if emails else phones[0] if phones else '',
            'experience':int(experience.group(1)) if experience and int(experience.group(1))<=60 else None,
            'desired_grade':grade,'roles':roles,'soft_skills':soft_skills,
            'notice':'Это черновик распознавания. Проверьте поля перед сохранением. Роли и софт-навыки извлечены из самоописания; подтверждённый грейд меняется только после теста.'}
