import { test, expect } from "@playwright/test";

test("настройки: смена пароля, выгрузка и удаление своего аккаунта", async ({ page }) => {
  const email = `account-${Date.now()}@example.org`;
  const password = "InitialPassword2026!";
  const next = "UpdatedPassword2026!";
  const response = await page.request.post("/api/v1/auth/register", {
    data: { email, password, role: "candidate", name: "Проверка настроек", consent: true },
  });
  expect(response.status()).toBe(201);
  await page.goto("/app");
  await page.getByRole("button", { name: "Меню аккаунта" }).click();
  await page.getByRole("menuitem", { name: "Настройки аккаунта" }).click();
  await expect(page.getByRole("heading", { name: "Настройки аккаунта" })).toBeVisible();
  await page.getByLabel("Текущий пароль", { exact: true }).fill(password);
  await page.getByLabel("Новый пароль", { exact: true }).fill(next);
  await page.getByLabel("Повторите новый пароль", { exact: true }).fill(next);
  await page.getByRole("button", { name: "Изменить пароль", exact: true }).click();
  await expect(page.getByText("Пароль изменён. Остальные сеансы завершены")).toBeVisible();
  await page.getByLabel("Текущий пароль", { exact: true }).fill(next);
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Скачать мои данные" }).click();
  expect((await download).suggestedFilename()).toBe("razryad-account.json");
  await expect(page.getByText("Выгрузка скачана.", { exact: false })).toBeVisible();
  await page.screenshot({ path: "../.local/account-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "../.local/account-mobile.png", fullPage: true });
  await page.getByLabel("Текущий пароль", { exact: true }).fill(next);
  await page.getByRole("button", { name: "Удалить аккаунт…", exact: true }).click();
  await expect(page.getByRole("button", { name: "Удалить аккаунт навсегда" })).toBeDisabled();
  await page.getByLabel("Введите УДАЛИТЬ").fill("УДАЛИТЬ");
  await page.getByRole("button", { name: "Удалить аккаунт навсегда" }).click();
  await page.waitForURL("**/auth?deleted=1");
  expect((await page.request.get("/api/v1/auth/me")).status()).toBe(401);
  expect((await page.request.post("/api/v1/auth/login", { data: { email, password: next } })).status()).toBe(401);
});
