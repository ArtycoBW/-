/** Русскоязычное содержание демонстрационной платформы. */
export const statementMock = {
  "kicker": "[ работа находит ваши навыки ]",
  "title": {
    "lead": "Сначала покажите, что умеете.",
    "accent": "Потом выбирайте",
    "tail": " свою команду."
  },
  "caption": "каждый шаг имеет значение",
  "now": "сейчас",
  "hours": [
    "09:00",
    "11:00",
    "13:00",
    "15:00",
    "17:00",
    "19:00"
  ]
} as const;

export type StatementContent = typeof statementMock;
