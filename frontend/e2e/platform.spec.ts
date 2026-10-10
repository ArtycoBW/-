import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";

test("регистрация → подтверждение грейда → приглашение → адресный контакт", async ({
  page,
  browser,
}) => {
  const key = `e2e${Date.now()}`,
    email = `${key}@example.org`;
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/auth?mode=register");
  await page.getByLabel("Ваше имя").fill("Тестовый Специалист");
  await page.getByLabel("Электронная почта").fill(email);
  await page.getByLabel("Пароль", { exact: true }).fill("TestPassword2026!");
  await page.getByRole("checkbox").check();
  await page
    .getByRole("button", { name: "Создать аккаунт →", exact: true })
    .click();
  await page.waitForURL("**/app");
  await page.getByRole("link", { name: "Мой профиль", exact: true }).click();
  await page.getByLabel("Навыки через запятую").fill(`Python, SQL, ${key}`);
  await page.getByLabel("Контакт для связи").fill(`${key}.private@example.org`);
  await page
    .getByRole("checkbox", { name: "Согласен на обработку данных профиля" })
    .check();
  await page.getByRole("checkbox", { name: "Показывать мой профиль" }).check();
  await page
    .getByRole("button", { name: "Сохранить профиль", exact: true })
    .click();
  await expect(
    page.getByText("Профиль сохранён", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Подтвердить уровень", exact: true })
    .click();
  await page.getByRole("button", { name: "Начать тест →" }).click();
  await expect(
    page.getByLabel("Ответ на вопрос 1", { exact: true }),
  ).toBeVisible();
  // Доверенная тестовая фикстура читает серверные ответы, публичный API их не выдаёт.
  const python = path.resolve("../.venv/Scripts/python.exe");
  const raw =
    process.env.E2E_DATABASE === "postgres"
      ? execFileSync(
          "docker",
          [
            "compose",
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            "import json,sys; from sqlalchemy import select; from backend.db import SessionLocal; from backend.models import Attempt,User; db=SessionLocal(); q=db.scalar(select(Attempt.questions).join(User,User.id==Attempt.candidate_id).where(User.email==sys.argv[1]).order_by(Attempt.started_at.desc())); print(json.dumps(q,ensure_ascii=False))",
            email,
          ],
          { cwd: path.resolve(".."), encoding: "utf8" },
        )
      : execFileSync(
          python,
          [
            "-c",
            "import sqlite3,json,sys; c=sqlite3.connect('.local/razryad.db'); r=c.execute('select questions from attempts join users on users.id=attempts.candidate_id where email=? order by started_at desc limit 1',(sys.argv[1],)).fetchone(); print(r[0])",
            email,
          ],
          { cwd: path.resolve(".."), encoding: "utf8" },
        );
  const questions: { id: string; answer: string }[] = JSON.parse(raw);
  const attempt = await (await page.request.get("/api/v1/assessments")).json();
  for (let i = 0; i < attempt[0].questions.length; i++) {
    const q = questions.find((q) => q.id === attempt[0].questions[i].id)!;
    await page
      .getByLabel(`Ответ на вопрос ${i + 1}`, { exact: true })
      .fill(q.answer);
  }
  await page.getByRole("button", { name: "Сохранить черновик" }).click();
  await expect(page.getByText("Черновик сохранён", { exact: true })).toBeVisible();
  await page.reload();
  await expect(
    page.getByLabel("Ответ на вопрос 1", { exact: true }),
  ).not.toHaveValue("");
  await page.getByRole("button", { name: "Завершить и проверить" }).click();
  await expect(
    page.getByText("Уровень подтверждён", { exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: "../.local/qa/assessment-result.png" });
  const employer = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "reduce",
  });
  const ep = await employer.newPage();
  await ep.goto("/auth");
  await ep
    .getByRole("button", { name: "Кабинет работодателя", exact: true })
    .click();
  await ep.waitForURL("**/app");
  await ep.goto("/app/talent");
  await ep.getByRole("textbox", { name: "Поиск по навыку" }).fill(key);
  await expect(ep.locator(".rz-talent-card")).toHaveCount(1);
  await ep.getByRole("button", { name: "Пригласить", exact: true }).click();
  const dialog = ep.getByRole("dialog");
  await dialog.getByLabel("Зарплата от, ₽").fill("180000");
  await dialog.getByLabel("Зарплата до, ₽").fill("240000");
  await dialog.getByRole("button", { name: /Отправить приглашение/ }).click();
  await expect(ep.getByRole("dialog")).toHaveCount(0);
  await ep.goto("/app/invitations");
  await expect(
    ep.getByText(`${key}.private@example.org`, { exact: false }),
  ).toHaveCount(0);
  await page.goto("/app/invitations");
  await page.getByRole("button", { name: /Принять/ }).click();
  await expect(page.getByText("Предложение принято. Только эта компания получила доступ к вашим контактам.", { exact: true })).toBeVisible();
  await ep.reload();
  await expect(
    ep.getByText(`${key}.private@example.org`, { exact: false }),
  ).toBeVisible();
  await ep.screenshot({ path: "../.local/qa/invitation-accepted.png" });
  await employer.close();
  expect(errors).toEqual([]);
});

test("мобильный кабинет и доступность модального окна", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/auth");
  await page
    .getByRole("button", { name: "Кабинет работодателя", exact: true })
    .click();
  await page.waitForURL("**/app");
  await page.getByRole("button", { name: "Открыть меню" }).click();
  await page
    .getByRole("link", { name: "Найти специалистов", exact: true })
    .click();
  await expect(page.locator(".rz-talent-card").first()).toBeVisible();
  await page.screenshot({ path: "../.local/qa/mobile-talent.png" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page
    .getByRole("button", { name: "Пригласить", exact: true })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Shift+Tab");
  expect(
    await page.evaluate(
      () => !!document.activeElement?.closest('[role="dialog"]'),
    ),
  ).toBeTruthy();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("лендинг на телефоне: русский интерфейс и рабочие переходы", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Ваш талант",
  );
  await page.screenshot({ path: "../.local/qa/mobile-home.png" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page
    .getByRole("link", { name: "Создать профиль", exact: true })
    .first()
    .click();
  await expect(page.getByLabel("Ваше имя")).toBeVisible();
});
