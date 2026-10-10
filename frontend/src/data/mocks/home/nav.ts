/** Русскоязычное содержание демонстрационной платформы. */
export const navMock = {
  "brand": {
    "name": "разряд.",
    "href": "/"
  },
  "links": [
    {
      "label": "Возможности",
      "href": "#product",
      "code": "01",
      "note": "Профиль, тест и приглашения"
    },
    {
      "label": "Как это работает",
      "href": "#scale",
      "code": "02",
      "note": "От навыков к предложению"
    },
    {
      "label": "Наш подход",
      "href": "#proof",
      "code": "03",
      "note": "Прозрачная методика"
    },
    {
      "label": "Начать",
      "href": "#pricing",
      "code": "04",
      "note": "Выберите свою роль"
    }
  ],
  "status": "ФСП × ЛЦТ 2026",
  "cta": {
    "label": "Войти ↗",
    "href": "/auth"
  }
} as const;

export type NavContent = typeof navMock;
