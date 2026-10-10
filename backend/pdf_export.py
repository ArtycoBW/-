import io
import os
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def register_font():
    if "Russian" in pdfmetrics.getRegisteredFontNames():
        return
    candidates = [os.getenv("PDF_FONT", ""), "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    path = next((p for p in candidates if p and Path(p).exists()), None)
    if not path:
        raise RuntimeError("Установите шрифт DejaVu Sans или задайте PDF_FONT")
    pdfmetrics.registerFont(TTFont("Russian", path))

def profile_pdf(profile):
    register_font()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, rightMargin=22*mm, leftMargin=22*mm, topMargin=22*mm, bottomMargin=22*mm, title="Разряд — профиль специалиста", author="Разряд")
    normal = ParagraphStyle("normal", fontName="Russian", fontSize=10, leading=16, textColor=colors.HexColor("#1B1C21"))
    title = ParagraphStyle("title", parent=normal, fontSize=26, leading=32, spaceAfter=18)
    specs = {"backend": "Бэкенд-разработка", "frontend": "Фронтенд-разработка"}
    grades = {"junior": "Начальный", "middle": "Средний", "senior": "Старший"}
    lines = [Paragraph("РАЗРЯД / Профиль специалиста", normal), Spacer(1, 12*mm), Paragraph(escape(profile["name"]), title)]
    for line in [f"Специализация: {specs.get(profile['specialization'], profile['specialization'])}", f"Подтверждённый уровень: {grades.get(profile['grade'], 'Пока не подтверждён')}", f"Тест: {profile['score']:g} / 100", f"Город: {profile['city']}", f"Опыт: {profile['experience']} лет", f"Стек: {', '.join(profile['skills'])}", profile['bio'], f"Почта: {profile.get('email', 'скрыта')}", f"Контакт: {profile.get('contact', 'скрыт')}"]:
        lines += [Paragraph(escape(line), normal), Spacer(1, 3*mm)]
    lines.append(Paragraph("Достижения ФСП", title))
    for a in profile['achievements']:
        lines.append(Paragraph(escape(f"{a['title']} · {a['date']} · место {a['place']}/{a['participants']} · демонстрационный реестр"), normal))
    if not profile['achievements']:
        lines.append(Paragraph("История ФСП пока не связана. Это не ограничивает участие в подборе.", normal))
    doc.build(lines)
    return buffer.getvalue()
