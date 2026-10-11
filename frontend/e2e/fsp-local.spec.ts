import { test, expect } from "@playwright/test";

test("локальный OIDC: история, отвязка и профиль без истории", async ({ page }) => {
  test.skip(process.env.FSP_LOCAL_E2E !== "true", "Requires compose.fsp-local.yml on loopback");
  const password = "LocalApplication2026!";
  const response = await page.request.post("/api/v1/auth/register", { data: {
    email: `fsp-${Date.now()}@example.org`, password, role: "candidate", name: "Проверка ФСП", consent: true,
  } });
  expect(response.status()).toBe(201);
  for (const username of ["fsp-history", "fsp-empty"]) {
    await page.goto("/app/profile");
    await page.getByRole("button", { name: "Войти в локальный ФСП ID" }).click();
    await page.waitForURL("http://localhost:8089/**");
    if (username === "fsp-empty") {
      await page.getByRole("button", { name: "Restart login", exact: true }).click();
    }
    await page.locator("#username").fill(username);
    await page.locator("#password").fill("LocalFsp2026!");
    await page.locator("#kc-login").click();
    await page.waitForURL("**/app/profile?fsp=linked");
    await expect(page.getByText("ФСП ID связан с профилем", { exact: true })).toBeVisible();
    const profile = await (await page.request.get("/api/v1/profile")).json();
    expect(profile.fsp_id).toMatch(/^oidc:/);
    expect(profile.achievements).toHaveLength(username === "fsp-history" ? 1 : 0);
    if (username === "fsp-history") {
      await expect(page.getByText("Учебный турнир локального стенда", { exact: true })).toBeVisible();
      await page.screenshot({ path: "../.local/fsp-linked-desktop.png", fullPage: true });
      await page.setViewportSize({ width: 390, height: 844 });
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.screenshot({ path: "../.local/fsp-linked-mobile.png", fullPage: true });
    }
    await page.getByRole("button", { name: "Отвязать", exact: true }).click();
    await expect(page.getByText("Профиль ФСП отвязан.", { exact: true })).toBeVisible();
  }
  expect((await page.request.delete("/api/v1/account", { data: { password, confirmation: "УДАЛИТЬ" } })).ok()).toBe(true);
});
