import { test, expect } from "@playwright/test";

test("компания создаёт и архивирует вакансию через новые элементы формы", async ({ page }) => {
  await page.goto("/auth");
  await page.getByRole("button", { name: "Кабинет работодателя", exact: true }).click();
  await page.waitForURL("**/app");
  await page.goto("/app/vacancies");
  await page.getByRole("button", { name: "+ Новая вакансия", exact: true }).click();
  const title = `Проверка формы ${Date.now()}`;
  await page.getByLabel("Название роли", { exact: true }).fill(title);
  await page.getByRole("combobox", { name: "Специализация", exact: true }).click();
  await page.getByRole("option", { name: "Фронтенд-разработка", exact: true }).click();
  await page.getByRole("combobox", { name: "Грейд", exact: true }).click();
  await page.getByRole("option", { name: "Старший (Senior)", exact: true }).click();
  await page.getByLabel("Навыки через запятую").fill("TypeScript, React, CSS");
  await page.getByRole("button", { name: "Сохранить вакансию", exact: true }).click();
  await expect(page.getByText("Вакансия сохранена", { exact: true })).toBeVisible();
  await page.getByRole("textbox", { name: "Поиск вакансий" }).fill(title);
  const row = page.locator(".rz-vacancy-row").filter({ hasText: title });
  await expect(row).toContainText("Старший");
  await page.reload();
  await page.getByRole("textbox", { name: "Поиск вакансий" }).fill(title);
  await expect(row).toContainText("TypeScript");
  await row.getByRole("button", { name: "В архив", exact: true }).click();
  await expect(row.getByText("В архиве", { exact: true })).toBeVisible();
});

test("меню сохраняет состояние, фильтры и избранное работают с клавиатуры", async ({
  page,
}) => {
  await page.goto("/auth");
  await page
    .getByRole("button", { name: "Кабинет специалиста", exact: true })
    .click();
  await page.waitForURL("**/app");
  const sidebar = page.locator(".rz-sidebar");
  const label = sidebar
    .getByRole("link", { name: "Подтвердить уровень", exact: true })
    .locator(".rz-nav-text");
  expect(
    await label.evaluate((e) => e.scrollWidth <= e.clientWidth),
  ).toBeTruthy();
  await page
    .getByRole("button", { name: "Свернуть меню", exact: true })
    .click();
  await expect(page.locator(".rz-workspace")).toHaveClass(/rz-compact/);
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Развернуть меню", exact: true }),
  ).toBeVisible();
  await sidebar.getByRole("link", { name: "Вакансии", exact: true }).click();
  await expect(page.locator(".rz-vacancy-row").first()).toBeVisible();
  await page.getByRole("combobox", { name: "Формат вакансии" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("listbox")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("combobox", { name: "Формат вакансии" })).toBeFocused();
  await page.getByRole("combobox", { name: "Формат вакансии" }).click();
  await page.getByRole("option", { name: "Удалённо", exact: true }).click();
  await expect(
    page.getByRole("combobox", { name: "Формат вакансии" }),
  ).toHaveText("Удалённо");
  await expect(page.locator(".rz-vacancy-row").first()).toContainText(
    "Удалённо",
  );
  await page
    .getByRole("button", { name: "Сохранить вакансию", exact: true })
    .first()
    .click();
  await page.getByRole("button", { name: /Избранное/ }).click();
  await expect(page.locator(".rz-vacancy-row")).toHaveCount(1);
  const title = await page.locator(".rz-vacancy-row h3").textContent();
  await page.reload();
  await page.getByRole("button", { name: /Избранное/ }).click();
  await expect(page.locator(".rz-vacancy-row h3")).toHaveText(title!);
  await page
    .getByRole("button", { name: "Развернуть меню", exact: true })
    .click();
  await expect(label).toBeVisible();
});

for (const width of [390, 1440, 1920]) {
  test(`диалог вакансии находится внутри экрана ${width}px после прокрутки`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/auth");
    await page
      .getByRole("button", { name: "Кабинет специалиста", exact: true })
      .click();
    await page.waitForURL("**/app");
    await page.goto("/app/vacancies");
    const trigger = page
      .getByRole("button", { name: "Подробнее", exact: true })
      .nth(5);
    await trigger.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    const box = (await dialog.boundingBox())!;
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.y).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(width);
    expect(box.y + box.height).toBeLessThanOrEqual(900);
    await dialog
      .getByLabel("Сопроводительное письмо")
      .fill("Проверка доступности формы");
    await dialog.getByRole("checkbox").check();
    await expect(dialog.getByRole("checkbox")).toBeChecked();
    await dialog
      .getByRole("button", { name: "Отправить отклик", exact: true })
      .scrollIntoViewIfNeeded();
    await expect(
      dialog.getByRole("button", { name: "Отправить отклик", exact: true }),
    ).toBeInViewport();
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(trigger).toBeFocused();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  });
}
