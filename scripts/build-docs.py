"""Сборка русской сопроводительной документации из актуальных Markdown-файлов."""
from pathlib import Path
import html
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                               Spacer, PageBreak, Table, TableStyle, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf"
OUT.mkdir(parents=True, exist_ok=True)
FONT_PATHS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
font_dir = next((p for p in FONT_PATHS if p.exists()), None)
if font_dir is None:
    raise RuntimeError("Установите Arial или DejaVu Sans для кириллицы")
windows = (font_dir / "arial.ttf").exists()
for name, filename in [("Body", "arial.ttf" if windows else "DejaVuSans.ttf"),
                       ("BodyBold", "arialbd.ttf" if windows else "DejaVuSans-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")
purple, ink = colors.HexColor("#402FFF"), colors.HexColor("#1B1C21")
styles = getSampleStyleSheet()
for name, size, leading in [("BodyText", 10, 15), ("Heading1", 25, 31), ("Heading2", 16, 22), ("Heading3", 12, 17)]:
    styles[name].fontName = "BodyBold" if name.startswith("Heading") else "Body"
    styles[name].fontSize, styles[name].leading = size, leading
    styles[name].textColor = purple if name.startswith("Heading") else ink
    styles[name].spaceAfter = 10
    styles[name].spaceBefore = 14 if name.startswith("Heading") else 0
styles.add(ParagraphStyle("Cell", fontName="Body", fontSize=8.3, leading=11.5, textColor=ink, spaceAfter=0))
styles.add(ParagraphStyle("CellHead", parent=styles["Cell"], fontName="BodyBold", textColor=colors.white))
styles.add(ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=colors.HexColor("#686675")))
styles.add(ParagraphStyle("CodeLine", parent=styles["Small"], backColor=colors.HexColor("#F0EEF9"), borderPadding=7, spaceAfter=2, wordWrap="CJK"))
styles.add(ParagraphStyle("CoverBrand", fontName="BodyBold", fontSize=62, leading=70, textColor=purple, spaceAfter=28))
styles.add(ParagraphStyle("CoverTitle", fontName="BodyBold", fontSize=25, leading=34, textColor=ink, spaceAfter=20))
styles.add(ParagraphStyle("BulletText", parent=styles["BodyText"], leftIndent=14, firstLineIndent=-11))


def inline(value):
    value = value.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r'<font color="#402FFF">\1</font>', value)
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1", value)
    return value


class Documentation(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=48, rightMargin=48,
                         topMargin=57, bottomMargin=48, title="Разряд: техническое задание и документация",
                         author="ArtycoBW", subject="ЛЦТ 2026. Специальный трек ФСП")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="all", frames=frame, onPage=self.header))

    def header(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9D5EA"))
        canvas.line(48, A4[1]-39, A4[0]-48, A4[1]-39)
        canvas.setFont("BodyBold", 8)
        canvas.setFillColor(purple)
        canvas.drawString(48, A4[1]-29, "РАЗРЯД / ЛЦТ 2026")
        canvas.setFont("Body", 8)
        canvas.setFillColor(colors.HexColor("#686675"))
        canvas.drawRightString(A4[0]-48, A4[1]-29, "ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ · 1.2")
        canvas.drawString(48, 27, "Демонстрационные данные. Фактические границы описаны в методике.")
        canvas.drawRightString(A4[0]-48, 27, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in {"Heading1", "Heading2"} and flowable.getPlainText() != "Содержание":
            text = flowable.getPlainText()
            key = "h" + str(id(flowable))
            self.canv.bookmarkPage(key)
            level = 0 if flowable.style.name == "Heading1" else 1
            self.notify("TOCEntry", (level, text, self.page, key))


def markdown(source):
    lines = source.splitlines()
    flow, i, code = [], 0, False
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("```"):
            code = not code
            i += 1
            continue
        if code:
            if line:
                flow.append(Paragraph(inline(line), styles["CodeLine"]))
            i += 1
            continue
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", c) for c in cells):
                    rows.append(cells)
                i += 1
            count = max(map(len, rows))
            ratios = {2: [0.34, 0.66], 3: [0.23, 0.43, 0.34], 4: [0.15, 0.31, 0.28, 0.26]}.get(count, [1/count]*count)
            if rows[0] == ["Аккаунт", "Назначение", "Пароль"]:
                ratios = [0.31, 0.44, 0.25]
            if rows[0] == ["Аккаунт", "Роль и назначение"]:
                ratios = [0.46, 0.54]
            data = [[Paragraph(inline(cell), styles["CellHead" if r == 0 else "Cell"]) for cell in row] for r, row in enumerate(rows)]
            table = Table(data, colWidths=[(A4[0]-96)*v for v in ratios], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), purple), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F5F3FB"), colors.white]), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LINEBELOW", (0, -1), (-1, -1), .5, colors.HexColor("#D9D5EA"))]))
            flow.extend([table, Spacer(1, 12)])
            continue
        heading = re.match(r"^(#{1,3}) (.*)", line)
        if heading:
            flow.append(Paragraph(inline(heading[2]), styles["Heading" + str(len(heading[1]))]))
        elif line.startswith("- "):
            flow.append(Paragraph("• " + inline(line[2:]), styles["BulletText"]))
        else:
            flow.append(Paragraph(inline(line), styles["BodyText"]))
        i += 1
    return flow


def main():
    flow = [Spacer(1, 100), Paragraph("разряд.", styles["CoverBrand"]),
            Paragraph("Навыки говорят за вас", styles["CoverTitle"]),
            Paragraph("Цифровая платформа прямого найма с подтверждённой категорией специалиста и профилем достижений ФСП", styles["BodyText"]),
            Spacer(1, 45), Paragraph("Техническое задание · Архитектура · API<br/>Тестирование · Машинное обучение · Эксплуатация", styles["Heading3"]),
            Spacer(1, 65), Paragraph("Специальный трек Федерации спортивного программирования<br/>Лидеры цифровой трансформации 2026<br/>Версия 1.2 / 11 октября 2026", styles["Small"]),
            PageBreak(), Paragraph("Содержание", styles["Heading1"])]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOC0", fontName="BodyBold", fontSize=10, leading=14, spaceBefore=6, textColor=purple), ParagraphStyle("TOC1", fontName="Body", fontSize=9, leading=12, leftIndent=14, textColor=ink)]
    flow.extend([toc, PageBreak()])
    docs = ["01-Техническое-задание.md", "02-Реализация.md", "03-Методика-и-проверка.md", "04-Сдача.md", "05-Проверка-стенда.md", "06-Готовность-и-эксплуатация.md", "07-Архитектура-и-аудит-кейса.md", "08-Функции-и-аккаунты-комиссии.md", "09-Валидация-релиза.md"]
    for n, filename in enumerate(docs):
        if n:
            flow.append(PageBreak())
        flow.extend(markdown((ROOT / "docs" / filename).read_text(encoding="utf-8")))
    target = OUT / "Разряд-документация.pdf"
    Documentation(str(target)).multiBuild(flow)
    print(target)


if __name__ == "__main__":
    main()
