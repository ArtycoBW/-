import { test, expect, type Page } from "@playwright/test";

async function login(page: Page, role = "candidate") {
  await page.goto("/auth");
  await page.getByLabel("Электронная почта", { exact: true }).fill(`${role}@demo.razryad.ru`);
  await page.getByLabel("Пароль", { exact: true }).fill("RazryadDemo2026!");
  await page.getByRole("button", { name: "Войти →", exact: true }).click();
  await expect(page.locator(".rz-workspace")).toBeVisible();
  return (await (await page.request.get("/api/v1/auth/me")).json()).id;
}

for (const role of ["candidate", "employer"]) {
  test(`${role}: справка, логотип и публичные страницы сохраняют аккаунт`, async ({ page }) => {
    const id = await login(page, role);
    await page.getByRole("button", { name: "Узнать о методике", exact: true }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page).toHaveURL(/\/app$/);
    await page.keyboard.press("Escape");

    for (const path of ["/methodology", "/privacy-policy", "/missing-navigation-test"]) {
      await page.goto(path);
      await page.getByRole("link", { name: "← В кабинет", exact: true }).click();
      await expect(page.locator(".rz-sidebar")).toBeVisible();
      await expect(page).toHaveURL(/\/app$/);
      expect((await (await page.request.get("/api/v1/auth/me")).json()).id).toBe(id);
    }
    await page.goto(role === "candidate" ? "/app/profile" : "/app/company");
    await page.locator(".rz-sidebar .rz-brand").click();
    await expect(page).toHaveURL(/\/app$/);
    await page.goto("/");
    await page.locator("header").getByRole("link", { name: "В кабинет", exact: true }).click();
    await expect(page.locator(".rz-sidebar")).toBeVisible();
    for (const path of ["/auth", "/auth?mode=register"]) {
      await page.goto(path);
      await expect(page).toHaveURL(/\/app$/);
    }
    for (const [mode, title] of [["verify", "Подтвердите почту"], ["reset", "Новый пароль"]]) {
      await page.goto(`/auth?mode=${mode}&token=navigation-test-invalid`);
      await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
      await expect(page).toHaveURL(new RegExp(`mode=${mode}`));
    }
    expect((await (await page.request.get("/api/v1/auth/me")).json()).id).toBe(id);
  });
}

test("гость возвращается на главную; чтение политики не стирает форму и не отправляет её", async ({ page }) => {
  for (const path of ["/methodology", "/privacy-policy", "/missing-navigation-test"]) {
    await page.goto(path);
    await expect(page.getByRole("link", { name: "← На главную", exact: true })).toHaveAttribute("href", "/");
  }
  await page.goto("/auth?mode=register");
  await page.getByLabel("Ваше имя", { exact: true }).fill("Черновик регистрации");
  await page.getByLabel("Электронная почта", { exact: true }).fill("unsent@example.com");
  let submissions = 0;
  page.on("request", (request) => { if (request.method() === "POST") submissions++; });
  await page.getByRole("button", { name: "политике конфиденциальности", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByLabel("Ваше имя", { exact: true })).toHaveValue("Черновик регистрации");
  await expect(page.getByLabel("Электронная почта", { exact: true })).toHaveValue("unsent@example.com");
  await expect(page.getByRole("checkbox")).not.toBeChecked();
  expect(submissions).toBe(0);
});

test("сбой сервера и сети дают повторить проверку, не выбрасывая из кабинета", async ({ page }) => {
  const id = await login(page);
  for (const failure of ["server", "network"]) {
    await page.route("**/api/v1/auth/me", (route) => failure === "server"
      ? route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Временный сбой проверки" }) })
      : route.abort("failed"));
    await page.goto("/app");
    await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/app$/);
    await page.unroute("**/api/v1/auth/me");
    await page.getByRole("button", { name: "Повторить", exact: true }).click();
    await expect(page.locator(".rz-sidebar")).toBeVisible();
    expect((await (await page.request.get("/api/v1/auth/me")).json()).id).toBe(id);
  }
});

test("недействительная сессия возвращает форму входа", async ({ page }) => {
  await page.goto("/app");
  await expect(page).toHaveURL(/\/auth/);
  await expect(page.getByRole("button", { name: "Войти →", exact: true })).toBeVisible();
});

test("выход остаётся явным действием и удаляет сессию", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "Меню аккаунта", exact: true }).click();
  await page.getByRole("menuitem", { name: "Выйти из аккаунта", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator("header").getByRole("link", { name: "Войти ↗", exact: true })).toBeVisible();
  expect((await page.request.get("/api/v1/auth/me")).status()).toBe(401);
});

test("мобильное меню главной возвращает в действующий кабинет", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Открыть меню", exact: true }).click();
  const menu = page.getByRole("dialog", { name: "Меню", exact: true });
  await expect(menu).toBeVisible();
  await menu.getByRole("link", { name: "В кабинет", exact: true }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.locator(".rz-workspace")).toBeVisible();
});
