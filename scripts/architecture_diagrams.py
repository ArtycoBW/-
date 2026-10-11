"""Reproducible vector architecture figures; no external rendering service."""
from pathlib import Path
from math import atan2, cos, sin
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderSVG
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/assets/diagrams'
INK, ACCENT, MUTED = '#192334', '#4934CC', '#64748B'
if 'Diagram' not in pdfmetrics.getRegisteredFontNames():
    windows = Path('C:/Windows/Fonts/arial.ttf')
    pdfmetrics.registerFont(TTFont('Diagram', str(windows if windows.exists() else Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))))


class Figure:
    def __init__(self, number, title, subtitle, height=660):
        self.h = height
        self.d = Drawing(1000, height)
        self.d.add(Rect(0, 0, 1000, height, fillColor=HexColor('#FFFFFF'), strokeColor=None))
        self.text(30, 36, f'{number:02d} / {title}', 27, ACCENT)
        self.text(30, 67, subtitle, 16, MUTED)

    def text(self, x, y, text, size=18, color=INK, anchor='start'):
        self.d.add(String(x, self.h-y, text, fontName='Diagram', fontSize=size, fillColor=HexColor(color), textAnchor=anchor))

    def group(self, x, y, w, h, label):
        self.d.add(Rect(x, self.h-y-h, w, h, rx=12, fillColor=HexColor('#F8FAFC'), strokeColor=HexColor('#CBD5E1'), strokeDashArray=[6, 4]))
        self.text(x+14, y+25, label, 17, MUTED)

    def box(self, x, y, w, h, title, *lines, kind='app'):
        fill, border = {'app':('#F0EDFF',ACCENT),'data':('#EAF6F1','#23866E'),'external':('#F1F5F9','#64748B'),'pending':('#FFF7E5','#B87C12')}[kind]
        self.d.add(Rect(x, self.h-y-h, w, h, rx=10, fillColor=HexColor(fill), strokeColor=HexColor(border), strokeWidth=1.6))
        self.text(x+w/2,y+28,title,19,border,'middle')
        for i,line in enumerate(lines): self.text(x+w/2,y+55+i*24,line,16,INK,'middle')

    def arrow(self, points, label='', lx=None, ly=None, dashed=False):
        for a,b in zip(points,points[1:]):
            self.d.add(Line(a[0],self.h-a[1],b[0],self.h-b[1],strokeColor=HexColor(MUTED),strokeWidth=1.5,strokeDashArray=[5,4] if dashed else None))
        a,b=points[-2:]; angle=atan2(b[1]-a[1],b[0]-a[0])
        coords=[b[0],self.h-b[1]]
        for offset in [-0.45,0.45]:
            coords.extend([b[0]-10*cos(angle+offset),self.h-(b[1]-10*sin(angle+offset))])
        self.d.add(Polygon(coords,fillColor=HexColor(MUTED),strokeColor=None))
        if label: self.text(lx if lx is not None else (a[0]+b[0])/2, ly if ly is not None else (a[1]+b[1])/2-9,label,15,MUTED,'middle')


def figures():
    result=[]
    def save(slug,f): result.append((slug,f.d))
    f=Figure(1,'Контекст системы / C4 L1','Роли, граница продукта и внешние системы')
    f.box(30,135,245,105,'Кандидат','Профиль, тест, отклики','Согласия и приглашения',kind='external')
    f.box(30,330,245,105,'Работодатель','Потребности и вакансии','Оценка практики',kind='external')
    f.group(325,112,340,390,'Граница продукта')
    f.box(355,235,280,140,'Разряд','Подтверждённая категория','Объяснимый подбор','Адресное открытие контактов')
    f.box(730,120,245,100,'Почта Timeweb','SMTP / STARTTLS','Доставка ссылок',kind='external')
    f.box(730,330,245,145,'ФСП / OIDC','Официальный доступ','не предоставлен','Локальный стенд отдельно',kind='pending')
    f.arrow([(275,187),(310,187),(310,280),(355,280)],'HTTPS',310,158)
    f.arrow([(275,383),(310,383),(310,330),(355,330)])
    f.arrow([(635,275),(690,275),(690,170),(730,170)],'SMTP',690,145)
    f.arrow([(635,335),(695,335),(695,400),(730,400)],dashed=True)
    f.text(30,570,'Сплошные связи: реализованы. Пунктир к ФСП: будущая официальная интеграция.',17)
    f.text(30,603,'Демонстрационные достижения не являются верификацией Федерации.',17,MUTED)
    save('01-context',f)

    f=Figure(2,'Контейнеры и модули / C4 L2','Модульный монолит: границы ответственности, а не отдельные микросервисы')
    f.box(30,125,230,115,'Браузер','Кабинеты двух ролей','HttpOnly cookie',kind='external')
    f.box(355,125,280,115,'Next.js','React / TypeScript','/api/v1 → API:8000')
    f.arrow([(260,180),(355,180)],'HTTPS',307,161)
    f.group(30,300,665,265,'FastAPI / Python — единый процесс API')
    f.box(50,350,195,88,'Доступ','Сессии, роли, лимиты')
    f.box(265,350,195,88,'Найм','Профили, согласия')
    f.box(480,350,195,88,'Оценка','Тесты и подбор')
    f.text(55,490,'SQLAlchemy / транзакции / Alembic / журнал запросов',18)
    f.text(55,525,'API возвращает контакты только при наличии ContactGrant.',16)
    f.arrow([(490,240),(490,300)],'HTTP / JSON',570,279)
    f.box(740,320,230,100,'PostgreSQL 17','Данные и rate_limits','Хеши сессий и токенов',kind='data')
    f.box(740,465,230,100,'Модель JSON','6 признаков','Без внешнего ML API',kind='data')
    f.arrow([(695,385),(740,385)])
    f.arrow([(675,420),(710,420),(710,515),(740,515)])
    f.text(30,613,'Пароли: Argon2. Одноразовые ссылки: SHA-256 в БД; срок действия 1 час.',17,MUTED)
    save('02-containers',f)

    f=Figure(3,'Развёртывание и сети','Два независимых входа, общая БД; переход сохраняет работающий адрес',720)
    f.box(30,110,440,85,'Временный HTTPS-адрес','trycloudflare.com / стенд комиссии',kind='external')
    f.box(530,110,440,85,'Постоянный HTTPS-адрес','razryad.agropulseai.ru / работает',kind='data')
    f.group(30,245,440,235,'Docker project: razryad')
    f.group(530,245,440,235,'Docker project: razryad-domain')
    f.box(55,300,160,80,'QuickTunnel','cloudflared')
    f.box(265,300,180,80,'web','Next.js :3000')
    f.box(265,395,180,65,'api','FastAPI :8000')
    f.box(555,300,160,80,'Named tunnel','cloudflared')
    f.box(765,300,180,80,'domain-web','Next.js :3000')
    f.box(765,395,180,65,'domain-api','FastAPI 1.3')
    f.arrow([(135,195),(135,300)])
    f.arrow([(635,195),(635,300)])
    f.arrow([(215,340),(265,340)])
    f.arrow([(715,340),(765,340)])
    f.arrow([(355,380),(355,395)])
    f.arrow([(855,380),(855,395)])
    f.box(375,555,250,100,'Общая PostgreSQL','razryad-db-1','Сеть razryad_default',kind='data')
    f.arrow([(355,460),(355,600),(375,600)])
    f.arrow([(855,460),(855,600),(625,600)])
    f.box(30,555,250,100,'Operations','Проверки /ready','Резервные копии',kind='data')
    f.text(30,693,'ПК, Docker и интернет должны работать. Локальные порты привязаны к 127.0.0.1.',17,MUTED)
    save('03-deployment',f)

    f=Figure(4,'Модель данных / ER','Ключевые связи; списки полей сокращены. Стрелка направлена к дочерней записи.',730)
    f.box(355,105,290,94,'User','id PK · email UNIQUE','role · password_hash · verified',kind='data')
    f.box(30,265,280,102,'Candidate','id PK / FK → User','category · skills · fsp_id',kind='data')
    f.box(690,265,280,102,'Company','id PK / FK → User','name · contact',kind='data')
    f.arrow([(355,150),(170,150),(170,265)],'1 : 0..1',250,141)
    f.arrow([(645,150),(830,150),(830,265)],'1 : 0..1',750,141)
    f.box(355,265,290,102,'Session / Token','user_id FK → User','token_hash PK · expires_at',kind='data')
    f.arrow([(500,199),(500,265)],'1 : N',548,239)
    f.box(30,435,280,115,'Attempt / Achievement','candidate_id FK','Тесты / достижения','1 кандидат : N записей',kind='data')
    f.arrow([(170,367),(170,435)])
    f.box(355,435,290,115,'Invitation / ContactGrant','candidate_id + company_id','Приглашение / согласие','Grant UNIQUE по паре',kind='data')
    f.arrow([(310,340),(332,340),(332,473),(355,473)])
    f.arrow([(690,340),(668,340),(668,473),(645,473)])
    f.box(690,435,280,115,'Vacancy / Challenge','company_id FK','Вакансии / практика','1 компания : N записей',kind='data')
    f.arrow([(830,367),(830,435)])
    f.box(255,603,490,90,'Application / Submission','Кандидат + вакансия / задача: уникальная пара','Отклик / решение связывают две стороны',kind='data')
    f.arrow([(30,315),(12,315),(12,648),(255,648)])
    f.arrow([(830,550),(830,648),(745,648)])
    save('04-data-model',f)

    f=Figure(5,'Подтверждение почты / sequence','Включено на постоянном домене; доставка и одноразовость проверены',760)
    xs=[110,370,630,890]
    for x,title in zip(xs,['Браузер','FastAPI','PostgreSQL','Почта']):
        f.box(x-95,100,190,62,title)
        f.d.add(Line(x,f.h-170,x,f.h-690,strokeColor=HexColor('#CBD5E1'),strokeDashArray=[4,4]))
    steps=[(0,1,'1. Регистрация + согласие'),(1,2,'2. User + SHA-256 токена'),(1,3,'3. SMTP STARTTLS: ссылка, TTL 1 ч'),(1,0,'4. «Проверьте почту», без сессии'),(3,0,'5. Пользователь открывает письмо'),(0,1,'6. POST /auth/verify + токен'),(1,2,'7. Проверка срока / блокировка строки'),(1,2,'8. verified=true; удалить токен'),(1,0,'9. Secure + HttpOnly cookie'),(0,1,'10. Повтор токена'),(1,0,'11. 400: ссылка уже использована')]
    for n,(a,b,label) in enumerate(steps):
        y=205+n*43
        f.arrow([(xs[a],y),(xs[b],y)],label,(xs[a]+xs[b])/2,y-9)
    f.text(30,735,'Сброс пароля использует отдельный kind=reset и завершает все прежние сессии.',17,MUTED)
    save('05-email-sequence',f)

    f=Figure(6,'Приглашения и доступ к контактам','Бизнес-процесс: решение кандидата определяет доступ конкретной компании')
    f.box(30,130,270,110,'Компания приглашает','Условия + диапазон зарплаты','Контакты кандидата скрыты')
    f.box(365,130,270,110,'Кандидат решает','Принять или отклонить','Управление в своём кабинете')
    f.box(700,130,270,110,'Отклонено / отозвано','Приглашение закрыто','Нового доступа нет',kind='external')
    f.arrow([(300,185),(365,185)])
    f.arrow([(635,185),(700,185)],'нет',669,166)
    f.box(365,330,270,110,'Принято','ContactGrant для пары','Компания + кандидат',kind='data')
    f.arrow([(500,240),(500,330)],'да',526,290)
    f.box(30,330,270,110,'Другая компания','Своего согласия нет','Контакты скрыты',kind='external')
    f.box(700,330,270,110,'Пригласившая компания','Согласие проверяется API','Контакты доступны',kind='data')
    f.arrow([(635,385),(700,385)])
    f.box(365,515,270,95,'Отзыв согласия','Удалить ContactGrant','Контакты снова скрыты')
    f.arrow([(500,440),(500,515)])
    f.text(30,642,'Сохранённые ранее копии контактов вне системы сервис удалить не может.',17,MUTED)
    save('06-consent-flow',f)

    f=Figure(7,'Поток данных подбора / ML','Рабочая модель и эксперимент на человеческой разметке разделены',710)
    f.box(30,115,290,95,'Профиль + потребность','Навыки, уровень, тест','Активность, ФСП, формат')
    f.box(365,115,270,95,'6 признаков','Нормализация навыков','Контакты не используются')
    f.box(700,115,270,95,'Базовая формула','Веса заданы явно','Работает без модели')
    f.arrow([(320,160),(365,160)]); f.arrow([(635,160),(700,160)])
    f.box(365,290,270,100,'model.json','Обучение на синтетике','Проверка схемы и чисел',kind='data')
    f.arrow([(500,210),(500,290)])
    f.box(700,290,270,100,'Гибридный балл','70% формула + 30% модель','Без файла: 100% формула')
    f.arrow([(835,210),(835,290)]); f.arrow([(635,340),(700,340)])
    f.box(700,450,270,100,'Выдача и объяснение','Совпавшие навыки','Пробелы и вклад признаков')
    f.arrow([(835,390),(835,450)])
    f.group(30,445,605,155,'Отдельный исследовательский контур / не в рабочем подборе')
    f.text(50,502,'Человеческая разметка → 18 train / 10 test резюме',19)
    f.text(50,534,'Текстовая модель: NDCG@3 = 0,8031 на малой выборке',17)
    f.text(50,566,'Преимущество над TF-IDF статистически не установлено.',16,MUTED)
    f.text(30,655,'Баллы соответствия не являются вероятностью трудоустройства.',18,ACCENT)
    f.text(30,685,'Полная продуктовая модель требует независимой проверки на реальных оценках.',16,MUTED)
    save('07-matching-pipeline',f)

    f=Figure(8,'Эксплуатация и безопасный выпуск','Контроль готовности, восстановление и условия включения почты',700)
    boxes=[(30,120,'Проверка DNS','Проверено при выпуске','NS + A/AAAA'),(365,120,'Публичный HTTPS','/health и /ready','Проверка сертификата'),(700,120,'Почтовые записи','MX / SPF / DKIM','SMTP + IMAP')]
    for x,y,t,a,b in boxes: f.box(x,y,270,100,t,a,b)
    f.arrow([(300,170),(365,170)]); f.arrow([(635,170),(700,170)])
    f.box(700,320,270,110,'Включение флагов','Только domain-api','Исходный туннель сохранён')
    f.arrow([(835,220),(835,320)])
    f.box(365,320,270,110,'Сквозная проверка','Регистрация → письмо → вход','Сброс и одноразовость')
    f.arrow([(700,375),(635,375)])
    f.box(30,320,270,110,'Уведомление владельца','Только после успеха','Ссылка + проверенные факты',kind='data')
    f.arrow([(365,375),(300,375)])
    f.box(365,520,270,100,'Если проверка не прошла','Вернуть прежние флаги','Записать ошибку',kind='pending')
    f.arrow([(500,430),(500,520)])
    f.text(30,662,'Ежедневно: pg_dump → восстановление в отдельную БД → проверка → 7 дней хранения.',16,MUTED)
    save('08-operations',f)
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for slug,drawing in figures():
        target = OUT/(slug+'.svg')
        renderSVG.drawToFile(drawing,str(target))
        # Standard browser fonts; PDF embeds the corresponding TrueType font directly.
        target.write_text(target.read_text(encoding='utf-8').replace('font-family: Diagram;', 'font-family: Arial, DejaVu Sans, sans-serif;'),encoding='utf-8')
    print(f'Generated {len(figures())} SVG diagrams in {OUT}')


if __name__=='__main__': main()
