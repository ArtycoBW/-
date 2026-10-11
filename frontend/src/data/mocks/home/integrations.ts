/** Русскоязычное содержание демонстрационной платформы. */
export const integrationsMock = {
  "caption": "десять направлений · три уровня · навыки, которые работают",
  "captionLines390": [
    "десять направлений · три уровня",
    "ваш следующий карьерный шаг"
  ],
  "apps": [
    {
      "name": "Python",
      "initials": "Py",
      "active": false,
      "in1024": true,
      "in390": true
    },
    {
      "name": "React",
      "initials": "Re",
      "active": true,
      "in1024": true,
      "in390": true
    },
    {
      "name": "SQL",
      "initials": "SQL",
      "active": false,
      "in1024": true,
      "in390": true
    },
    {
      "name": "Docker",
      "initials": "D",
      "active": false,
      "in1024": true,
      "in390": false
    },
    {
      "name": "TypeScript",
      "initials": "TS",
      "active": false,
      "in1024": false,
      "in390": true
    },
    {
      "name": "Git",
      "initials": "Git",
      "active": false,
      "in1024": false,
      "in390": false
    },
    {
      "name": "API",
      "initials": "{}",
      "active": false,
      "in1024": true,
      "in390": false
    },
    {
      "name": "и другие",
      "initials": "+",
      "active": false,
      "in1024": true,
      "in390": false
    }
  ]
} as const;

export type IntegrationsContent = typeof integrationsMock;
export type IntegrationsApp = IntegrationsContent["apps"][number];
