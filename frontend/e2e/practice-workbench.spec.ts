import { test, expect, type Page } from "@playwright/test";

async function openTask(page: Page) {
  await page.goto("/auth");
  await page
    .getByRole("button", { name: "Кабинет специалиста", exact: true })
    .click();
  await page.waitForURL("**/app");
  await page.goto("/app/challenges");
  await page.getByRole("button", { name: "Доступные", exact: true }).click();
  const card = page.locator(".rz-practice-card").first();
  const title = await card.locator("h2").innerText();
  await card
    .getByRole("button", { name: "Решить задачу", exact: true })
    .click();
  return title;
}

for (const width of [1440, 390]) {
  test(`мастерская ${width}px: шаблоны, предпросмотр и сохранение черновика`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 950 });
    const title = await openTask(page);
    const dialog = page.getByRole("dialog");
    const answer = page.getByLabel("Ваш подход к решению", { exact: true });
    await answer.fill("");
    await expect(
      page.getByRole("button", { name: "Проверить решение", exact: true }),
    ).toBeDisabled();
    await dialog.getByRole("button", { name: "План", exact: true }).click();
    await expect(answer).toHaveValue(/## Подход/);
    await dialog.getByRole("button", { name: "Код", exact: true }).click();
    await expect(answer).toHaveValue(/```/);
    await dialog
      .getByRole("button", { name: "Тест-кейсы", exact: true })
      .click();
    await expect(answer).toHaveValue(/Граничный случай/);
    const draft =
      "## Идея\nОчередь с повторными попытками и ключом идемпотентности.\n\n```python\nprint('<img src=x onerror=alert(1)>')\n```\n\n## Проверка\n- Повтор запроса не создаёт вторую задачу.";
    await answer.fill(draft);
    await expect(page.getByRole("status")).toHaveText(
      "Черновик сохранён на этом устройстве",
    );
    await page
      .getByRole("button", { name: "Проверить решение", exact: true })
      .click();
    await expect(
      dialog.getByRole("heading", { name: "Идея", exact: true }),
    ).toBeVisible();
    await expect(dialog.locator(".rz-solution-preview code")).toContainText(
      "<img src=x",
    );
    await expect(dialog.locator(".rz-solution-preview img")).toHaveCount(0);
    expect(
      await dialog.evaluate((el) => el.scrollWidth <= el.clientWidth + 1),
    ).toBe(true);
    const download = page.waitForEvent("download");
    await page
      .getByRole("button", { name: "Скачать решение в Markdown", exact: true })
      .click();
    expect((await download).suggestedFilename()).toBe("razryad-solution.md");
    await page.getByRole("button", { name: "Править", exact: true }).click();
    await expect(answer).toHaveValue(draft);
    await page.keyboard.press("Escape");
    await page.reload();
    await page.getByRole("textbox", { name: "Поиск заданий" }).fill(title);
    await page
      .getByRole("button", { name: "Решить задачу", exact: true })
      .first()
      .click();
    await expect(answer).toHaveValue(draft);
    await answer.fill("");
  });
}

test("отправка решения, удаление черновика и просмотр работодателем", async ({
  page,
  baseURL,
}) => {
  test.skip(
    !baseURL?.startsWith("http://localhost:"),
    "Отправляем решение только в изолированную тестовую базу",
  );
  const title = await openTask(page);
  const draft =
    "## Подход\nИспользуем очередь с уникальным ключом для каждого события.\n\n```python\nassert retry(event) == first_result\n```\n\n## Проверка\n- Повторное событие\n- Отмена устаревшей задачи";
  await page.getByLabel("Ваш подход к решению", { exact: true }).fill(draft);
  // A failed delivery must keep the draft and allow a retry.
  await page.route("**/challenges/*/submissions", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Отправка временно недоступна" }),
    }),
  );
  await page
    .getByRole("button", { name: "Проверить решение", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Отправить решение", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toHaveText(
    "Отправка временно недоступна",
  );
  await page.unroute("**/challenges/*/submissions");
  await page
    .getByRole("button", { name: "Отправить решение", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByText("Решение отправлено на проверку работодателю", {
      exact: true,
    }),
  ).toBeVisible();
  const me = await (await page.request.get("/api/v1/auth/me")).json();
  const tasks = await (await page.request.get("/api/v1/challenges")).json();
  const task = tasks.find((item: { title: string }) => item.title === title);
  expect(task.submissions[0].answer).toBe(draft);
  expect(
    await page.evaluate(
      (key) => localStorage.getItem(key),
      `razryad.practice.${me.id}.${task.id}`,
    ),
  ).toBeNull();
  await page.request.post("/api/v1/auth/logout", {
    headers: { Origin: baseURL! },
  });
  await page.goto("/auth");
  await page
    .getByRole("button", { name: "Кабинет работодателя", exact: true })
    .click();
  await page.waitForURL("**/app");
  await page.goto("/app/challenges");
  await page.getByRole("textbox", { name: "Поиск заданий" }).fill(title);
  await page.getByRole("button", { name: "Посмотреть", exact: true }).click();
  await expect(
    page.getByRole("dialog").locator(".rz-solution-preview code"),
  ).toHaveText("assert retry(event) == first_result");
});
