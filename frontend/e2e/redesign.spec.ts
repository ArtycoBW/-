import { test, expect } from "@playwright/test";

test("лендинг: масштаб, текстовые статусы и русская вёрстка", async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 960 });
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Создать профиль", exact: true }).first()).toBeVisible();
  const rootSize = await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).fontSize));
  expect(rootSize).toBeLessThanOrEqual(19.3);
  const invitation = page.locator(".rz-landing-invitation");
  await invitation.scrollIntoViewIfNeeded();
  await expect(invitation).toBeVisible();
  const copy = await invitation.locator(".rz-offer-copy").boundingBox();
  const fields = await invitation.locator(".rz-offer-fields").boundingBox();
  expect(fields!.y).toBeGreaterThan(copy!.y + copy!.height - 1);
  await page.getByText("Контакты открываются адресно", { exact: true }).scrollIntoViewIfNeeded();
  await page.waitForTimeout(700);
  await expect(page.locator("body")).not.toContainText("NaN");
  const caption = page.getByText("баллов из 100 · пример результата", { exact: true });
  await caption.scrollIntoViewIfNeeded();
  const box = await caption.boundingBox();
  const widget = await caption.locator("xpath=ancestor::*[@aria-labelledby='signals-hands-off']").boundingBox();
  expect(box!.y + box!.height).toBeLessThanOrEqual(widget!.y + widget!.height);
});

test("авторизация: без письма, показ пароля, уменьшение движения", async ({ page }) => {
  await page.goto("/auth");
  await expect(page.getByRole("button", { name: "Нет письма?" })).toHaveCount(0);
  const password = page.getByLabel("Пароль", { exact: true });
  await password.fill("DemoVisible2026!");
  await page.getByRole("button", { name: "Показать пароль" }).click();
  await expect(password).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Скрыть пароль" }).click();
  await expect(password).toHaveAttribute("type", "password");
  await expect(page.locator(".rz-signal-field")).toBeVisible();
});

for (const role of ["candidate", "employer"]) {
  test(`мобильные разделы: ${role}, без переполнения и ошибок`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/auth");
    await page.getByRole("button", { name: role === "candidate" ? "Кабинет специалиста" : "Кабинет работодателя", exact: true }).click();
    await page.waitForURL("**/app");
    const sections = role === "candidate" ? ["profile", "assessment", "invitations", "vacancies", "applications", "challenges"] : ["talent", "company", "invitations", "vacancies", "applications", "challenges"];
    for (const section of sections) {
      await page.goto(`/app/${section}`);
      await expect(page.locator(".rz-pagehead h1")).toBeVisible();
      await expect(page.locator("body")).not.toContainText("NaN");
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), section).toBeTruthy();
    }
    await page.getByRole("button", { name: "Открыть меню" }).click();
    await expect(page.locator(".rz-sidebar")).toHaveClass(/open/);
    await page.getByRole("button", { name: "Закрыть меню", exact: true }).click({ position: { x: 330, y: 300 } });
    await expect(page.locator(".rz-sidebar")).not.toHaveClass(/open/);
    expect(errors).toEqual([]);
  });
}
