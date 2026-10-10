/** Русскоязычное содержание демонстрационной платформы. */
export const heroMock = {
  "chip": "навыки говорят за вас",
  "title": {
    "before": "Ваш талант. ",
    "accent": "Новый разряд",
    "after": "."
  },
  "subhead": "Подтвердите навыки. Получайте предложения от команд, которым нужны именно вы.",
  "actions": {
    "primary": {
      "label": "Создать профиль",
      "href": "/auth?mode=register"
    },
    "secondary": {
      "label": "Найти специалиста ↗",
      "href": "/auth?mode=register&role=employer"
    }
  },
  "note": "подтверждённый грейд / открытая зарплата / ваш выбор",
  "noteLines": [
    "подтверждённый грейд / открытая зарплата",
    "контакты только с вашего согласия"
  ],
  "noteLines390": [
    "подтверждённый грейд / ваш выбор",
    "контакты под вашим контролем"
  ],
  "window": {
    "label": "Иллюстрация пути специалиста",
    "title": "Путь специалиста",
    "meta": "3 шага / ваш выбор",
    "status": "демосценарий",
    "zoom": "100%",
    "tools": [
      {
        "name": "выбор",
        "icon": "/assets/hero/hero-tool-select.svg"
      },
      {
        "name": "добавить",
        "icon": "/assets/hero/hero-tool-add.svg"
      },
      {
        "name": "перейти",
        "icon": "/assets/hero/hero-tool-redirect.svg"
      },
      {
        "name": "код",
        "icon": "/assets/hero/hero-tool-extra.svg"
      }
    ],
    "trigger": {
      "title": "Профиль создан",
      "source": "навыки и опыт"
    },
    "condition": {
      "title": "Грейд подтверждён",
      "source": "тест · 87 / 100"
    },
    "log": {
      "title": "Банк специалистов",
      "source": "ваша категория"
    },
    "branches": {
      "yes": "да",
      "no": "позже"
    },
    "approval": {
      "title": "Приглашение",
      "source": "180–260 тыс. ₽"
    },
    "wait": "ваш ход",
    "runsLabel": "пример событий",
    "runs": [
      {
        "time": "09:41:02",
        "name": "уровень подтверждён",
        "duration": "87 / 100",
        "live": true
      },
      {
        "time": "09:38:57",
        "name": "профиль опубликован",
        "duration": "готово",
        "live": false
      },
      {
        "time": "09:31:14",
        "name": "навыки добавлены",
        "duration": "5 навыков",
        "live": false
      }
    ],
    "runPool": [
      {
        "name": "профиль опубликован",
        "duration": "готово"
      },
      {
        "name": "уровень подтверждён",
        "duration": "87 / 100"
      },
      {
        "name": "предложение получено",
        "duration": "новое"
      },
      {
        "name": "приглашение принято",
        "duration": "контакт открыт"
      }
    ],
    "runGaps": [
      47,
      73,
      38,
      91,
      56
    ]
  }
} as const;

export type HeroContent = typeof heroMock;
