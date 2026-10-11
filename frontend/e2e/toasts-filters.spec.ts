import { test, expect, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/auth");
  await page
    .getByRole("button", { name: "Кабинет специалиста", exact: true })
    .click();
  await page.waitForURL("**/app");
}

for (const width of [1440, 390]) {
  test(`приглашения ${width}: поиск, статус, сортировка и тост без сдвига`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 950 });
    await login(page);
    const items = [
      {
        id: "ui-a",
        title: "Python-разработчик",
        company_name: "Север",
        candidate_name: "Александр",
        message: "Удалённая команда",
        status: "sent",
        salary_min: 100000,
        salary_max: 200000,
        created_at: 100,
      },
      {
        id: "ui-b",
        title: "Инженер API",
        company_name: "Контур",
        candidate_name: "Александр",
        message: "Разработка сервисов",
        status: "viewed",
        salary_min: 200000,
        salary_max: 300000,
        created_at: 200,
      },
      {
        id: "ui-c",
        title: "Разработчик данных",
        company_name: "Север",
        candidate_name: "Александр",
        message: "SQL и Python",
        status: "declined",
        salary_min: 300000,
        salary_max: 400000,
        created_at: 300,
      },
    ];
    await page.route("**/api/v1/invitations", (route) =>
      route.fulfill({ json: items }),
    );
    let fail = true;
    await page.route("**/api/v1/invitations/ui-a", (route) => {
      if (fail)
        return route.fulfill({
          status: 503,
          json: { detail: "Не удалось сохранить статус" },
        });
      items[0].status = route.request().postDataJSON().status;
      return route.fulfill({ json: items[0] });
    });
    await page.goto("/app/invitations");
    const cards = page.locator("article.rz-panel");
    await expect(cards).toHaveCount(3);
    await expect(cards.first()).toContainText("Разработчик данных");
    await page
      .getByRole("searchbox", { name: "Поиск приглашений" })
      .fill("СЕВЕР удаленная");
    await expect(cards).toHaveCount(1);
    await expect(cards).toContainText("Python-разработчик");
    await page.getByRole("button", { name: "Сбросить фильтры" }).click();
    await page.getByRole("combobox", { name: "Сортировка" }).click();
    await page.getByRole("option", { name: "Сначала старые" }).click();
    await expect(cards.first()).toContainText("Python-разработчик");
    await page.getByRole("combobox", { name: "Сортировка" }).click();
    await page.getByRole("option", { name: "По зарплате ↓" }).click();
    await expect(cards.first()).toContainText("Разработчик данных");
    await page.getByRole("combobox", { name: "Статус", exact: true }).click();
    await page
      .getByRole("option", { name: "Отправлено · 1", exact: true })
      .click();
    await expect(cards).toHaveCount(1);
    await page.getByRole("button", { name: "Отметить просмотренным" }).click();
    await expect(page.locator(".rz-notice.error")).toContainText(
      "Не удалось сохранить статус",
    );
    await expect(page.locator(".rz-toast")).toHaveCount(0);
    fail = false;
    // Clear status filter so the changed card remains visible for the layout assertion.
    await page.getByRole("button", { name: "Сбросить фильтры" }).click();
    const card = cards.filter({ hasText: "Python-разработчик" });
    const before = await card.boundingBox();
    await page.getByRole("button", { name: "Отметить просмотренным" }).click();
    await expect(page.locator(".rz-toast")).toContainText(
      "Приглашение отмечено просмотренным",
    );
    await expect(page.locator(".rz-notice.error")).toHaveCount(0);
    await expect(card).toContainText("Просмотрено");
    // The previous error disappears; compare after success with toast dismissed below.
    expect(before).not.toBeNull();
    const during = await card.boundingBox();
    await page.getByRole("button", { name: "Закрыть уведомление" }).click();
    await expect(page.locator(".rz-toast")).toHaveCount(0);
    expect((await card.boundingBox())?.y).toBe(during?.y);
    await page.getByRole("searchbox").fill("несуществующая вакансия");
    await expect(
      page.getByRole("heading", { name: "Ничего не найдено" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Сбросить фильтры" }).click();
    await expect(cards).toHaveCount(3);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  });
}

test("отклики: комбинированные фильтры, обновление и время жизни тоста", async ({
  page,
}) => {
  await login(page);
  const items = [
    {
      id: "app-a",
      vacancy_title: "Python API",
      company_name: "Север",
      candidate_name: "Александр",
      letter: "Хочу развивать API",
      status: "sent",
      created_at: 100,
    },
    {
      id: "app-b",
      vacancy_title: "Инженер данных",
      company_name: "Контур",
      candidate_name: "Александр",
      letter: "Опыт SQL",
      status: "interview",
      created_at: 200,
    },
  ];
  await page.route("**/api/v1/applications", (route) =>
    route.fulfill({ json: items }),
  );
  await page.route("**/api/v1/applications/app-a", (route) => {
    items[0].status = "withdrawn";
    return route.fulfill({ json: items[0] });
  });
  await page.goto("/app/applications");
  const cards = page.locator("section.rz-panel");
  await expect(cards).toHaveCount(2);
  await page
    .getByRole("searchbox", { name: "Поиск откликов" })
    .fill("SQL контур");
  await expect(cards).toHaveCount(1);
  await page.getByRole("combobox", { name: "Статус", exact: true }).click();
  await page
    .getByRole("option", { name: "Отправлено · 1", exact: true })
    .click();
  await expect(cards).toHaveCount(0);
  await page.getByRole("button", { name: "Сбросить фильтры" }).click();
  await cards
    .filter({ hasText: "Python API" })
    .getByRole("button", { name: "Отозвано" })
    .click();
  await expect(page.locator(".rz-toast")).toHaveText("Отклик отозван");
  await expect(cards.filter({ hasText: "Python API" })).toContainText(
    "Отозвано",
  );
  await page
    .getByRole("navigation", { name: "Разделы кабинета" })
    .getByRole("link", { name: "Приглашения", exact: true })
    .click();
  await expect(page.locator(".rz-toast")).toHaveText("Отклик отозван");
  await page
    .getByRole("heading", { name: "Приглашения для вас", exact: true })
    .hover();
  await expect(page.locator(".rz-toast")).toHaveCount(0, { timeout: 10000 });
});

test("настоящий переход статуса приглашения в изолированной базе", async ({
  page,
  baseURL,
}) => {
  test.skip(
    !baseURL?.startsWith("http://localhost:"),
    "Не меняем публичные аккаунты",
  );
  await login(page);
  await page.goto("/app/invitations");
  const card = page.locator("article.rz-panel").first();
  await card.getByRole("button", { name: "Отметить просмотренным" }).click();
  await expect(page.locator(".rz-toast")).toContainText(
    "Приглашение отмечено просмотренным",
  );
  await page.reload();
  await expect(card).toContainText("Просмотрено");
  await expect(
    card.getByRole("button", { name: "Отметить просмотренным" }),
  ).toHaveCount(0);
});
