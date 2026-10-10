/** Русскоязычное содержание демонстрационной платформы. */
export const pricingMock = {
  "head": {
    "badge": "ваш следующий шаг",
    "title": {
      "before": "Начните со ",
      "accent": "своей роли",
      "after": "."
    },
    "aside": "Специалист подтверждает навыки. Компания знакомится с людьми, которые подходят её задачам."
  },
  "meter": {
    "eyebrow": "прототип",
    "question": "Выберите сторону знакомства",
    "resultEyebrow": "ваш путь",
    "period": "шагов",
    "included": "шагов",
    "cta": {
      "label": "Начать",
      "href": "/auth"
    }
  },
  "tiers": [
    {
      "name": "Специалисту",
      "price": "01",
      "runs": 3,
      "period": "ваш карьерный путь",
      "featured": false,
      "features": [
        {
          "label": "Профиль и импорт резюме",
          "size": "body"
        },
        {
          "label": "Проверка выбранного уровня",
          "size": "body"
        },
        {
          "label": "Предложения с зарплатой",
          "size": "body"
        },
        {
          "label": "Контакты под вашим контролем",
          "size": "body"
        }
      ],
      "cta": {
        "label": "Создать профиль",
        "href": "/auth?mode=register"
      }
    },
    {
      "name": "Работодателю",
      "price": "02",
      "runs": 3,
      "period": "ваша будущая команда",
      "featured": true,
      "tag": "обратный найм",
      "features": [
        {
          "label": "Поиск по категории и стеку",
          "size": "body"
        },
        {
          "label": "Объяснимый порядок выдачи",
          "size": "body"
        },
        {
          "label": "Приглашения без вакансии",
          "size": "body"
        },
        {
          "label": "Отклики и практические задания",
          "size": "body"
        }
      ],
      "cta": {
        "label": "Найти специалиста",
        "href": "/auth?mode=register&role=employer"
      }
    },
    {
      "name": "Исследователю",
      "price": "03",
      "runs": 3,
      "period": "прозрачная методика",
      "featured": false,
      "features": [
        {
          "label": "Формула и признаки подбора",
          "size": "body"
        },
        {
          "label": "Схема тестирования",
          "size": "body"
        },
        {
          "label": "Ограничения демоданных",
          "size": "body"
        },
        {
          "label": "Проверяемые решения",
          "size": "body"
        }
      ],
      "cta": {
        "label": "Как всё устроено",
        "href": "/methodology"
      }
    }
  ]
} as const;

export type PricingContent = typeof pricingMock;
