/** Русскоязычное содержание демонстрационной платформы. */
export const footerMock = {
  "brand": {
    "name": "разряд.",
    "href": "/",
    "tagline": "Карьера начинается с того, что вы умеете.",
    "socialLabel": "полезные ссылки",
    "socials": [
      {
        "label": "ФСП",
        "name": "Федерация спортивного программирования",
        "href": "https://www.fsp-russia.ru/"
      },
      {
        "label": "ЛЦТ",
        "name": "Лидеры цифровой трансформации",
        "href": "https://i.moscow/lct"
      }
    ]
  },
  "cta": {
    "eyebrow": "следующий уровень",
    "title": {
      "before": "Навыки есть. ",
      "accent": "Пора",
      "after": " знакомиться."
    },
    "copy": "Создайте профиль, подтвердите уровень и начните получать предложения с понятными условиями.",
    "emailLabel": "Ваша электронная почта",
    "submit": "Начать"
  },
  "statuses": [
    {
      "label": "демонстрационная платформа",
      "short": "демоплатформа"
    },
    {
      "label": "подтверждение через тест",
      "short": "проверка навыков"
    },
    {
      "label": "контакт только с согласия",
      "short": "ваше согласие"
    }
  ],
  "company": {
    "name": "Разряд",
    "copy": "Решение специального трека ФСП на ЛЦТ 2026.",
    "compliance": "Демореестр ФСП / синтетические профили"
  },
  "columns": [
    {
      "title": "специалисту",
      "links": [
        {
          "label": "Создать профиль",
          "href": "/auth?mode=register"
        },
        {
          "label": "Подтвердить уровень",
          "href": "/app/assessment"
        },
        {
          "label": "Вакансии",
          "href": "/app/vacancies"
        },
        {
          "label": "Приглашения",
          "href": "/app/invitations"
        }
      ]
    },
    {
      "title": "компании",
      "links": [
        {
          "label": "Создать кабинет",
          "href": "/auth?mode=register&role=employer"
        },
        {
          "label": "Найти людей",
          "href": "/app/talent"
        },
        {
          "label": "Мои вакансии",
          "href": "/app/vacancies"
        },
        {
          "label": "Практика",
          "href": "/app/challenges"
        }
      ]
    },
    {
      "title": "о платформе",
      "links": [
        {
          "label": "Возможности",
          "href": "#product"
        },
        {
          "label": "Методика",
          "href": "/methodology"
        },
        {
          "label": "API",
          "href": "/api/v1/docs"
        },
        {
          "label": "ФСП",
          "href": "https://www.fsp-russia.ru/"
        }
      ]
    },
    {
      "title": "данные",
      "links": [
        {
          "label": "Приватность",
          "href": "/privacy-policy"
        },
        {
          "label": "О деморежиме",
          "href": "/methodology"
        },
        {
          "label": "Вход",
          "href": "/auth"
        }
      ]
    }
  ],
  "legal": {
    "copyright": "© 2026 Разряд",
    "origin": "навыки говорят за вас"
  }
} as const;

export type FooterContent = typeof footerMock;
