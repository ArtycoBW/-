// Запись реальной браузерной проверки на локальном Docker-стенде.
const { chromium, expect } = require('../frontend/node_modules/@playwright/test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true, slowMo: 220 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', recordVideo: { dir: path.join(root, '.local/video'), size: { width: 1440, height: 1000 } } });
  const page = await context.newPage();
  const video = page.video();
  const visit = url => page.goto('http://localhost:3000' + url);
  const pause = () => page.waitForTimeout(2200);
  const key = `demo${Date.now()}`, email = `${key}@example.org`, password = 'DemoRecord2026!';
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    await visit('/'); await pause();
    await page.getByRole('link', { name: 'Создать профиль', exact: true }).first().click();
    await page.getByLabel('Ваше имя').fill('Демонстрационный специалист');
    await page.getByLabel('Электронная почта').fill(email);
    await page.getByLabel('Пароль', { exact: true }).fill(password);
    await page.getByRole('checkbox').check();
    await page.getByRole('button', { name: 'Создать аккаунт →', exact: true }).click();
    await page.getByRole('link', { name: 'открыть одноразовую ссылку' }).click();
    await page.getByRole('button', { name: 'Подтвердить и войти →' }).click();
    await page.waitForURL('**/app'); await pause();
    await page.getByRole('link', { name: 'Мой профиль', exact: true }).click();
    await page.getByLabel('Навыки через запятую').fill(`Python, SQL, ${key}`);
    await page.getByLabel('Контакт для связи').fill(`${key}.contact@example.org`);
    await page.getByRole('checkbox', { name: 'Согласен на обработку данных профиля' }).check();
    await page.getByRole('checkbox', { name: 'Показывать мой профиль' }).check();
    await page.getByRole('button', { name: 'Сохранить профиль', exact: true }).click();
    await expect(page.getByText('Профиль сохранён', { exact: true })).toBeVisible(); await pause();
    await page.getByRole('link', { name: 'Подтвердить уровень', exact: true }).click();
    await page.getByRole('button', { name: 'Начать тест →' }).click();
    await expect(page.getByLabel('Ответ на вопрос 1', { exact: true })).toBeVisible(); await pause();
    // Доверенная фикстура проверяет интеграцию. Правильные ответы не доступны пользователю API.
    const questions = JSON.parse(execFileSync('docker', ['compose', 'exec', '-T', 'api', 'python', '-c', 'import json,sys; from sqlalchemy import select; from backend.db import SessionLocal; from backend.models import Attempt,User; db=SessionLocal(); q=db.scalar(select(Attempt.questions).join(User,User.id==Attempt.candidate_id).where(User.email==sys.argv[1]).order_by(Attempt.started_at.desc())); print(json.dumps(q,ensure_ascii=False))', email], { cwd: root, encoding: 'utf8' }));
    const attempts = await (await page.request.get('http://localhost:3000/api/v1/assessments')).json();
    for (let i = 0; i < attempts[0].questions.length; i++) {
      await page.getByLabel(`Ответ на вопрос ${i + 1}`, { exact: true }).fill(questions.find(q => q.id === attempts[0].questions[i].id).answer);
    }
    await page.getByRole('button', { name: 'Сохранить черновик' }).click();
    await page.reload();
    await expect(page.getByLabel('Ответ на вопрос 1', { exact: true })).not.toHaveValue('');
    await page.getByRole('button', { name: 'Завершить и проверить' }).click();
    await expect(page.getByText('Уровень подтверждён', { exact: true })).toBeVisible(); await pause();
    await visit('/auth');
    await page.getByRole('button', { name: 'Кабинет работодателя', exact: true }).click();
    await page.waitForURL('**/app'); await pause();
    await page.getByRole('link', { name: 'Найти специалистов', exact: true }).click();
    await page.getByRole('textbox', { name: 'Поиск по навыку' }).fill(key);
    await expect(page.locator('.rz-talent-card')).toHaveCount(1);
    await page.locator('.rz-explanation summary').click(); await pause();
    await page.getByRole('button', { name: 'Пригласить', exact: true }).click();
    await page.getByRole('dialog').getByLabel('Зарплата от, ₽').fill('180000');
    await page.getByRole('dialog').getByLabel('Зарплата до, ₽').fill('240000'); await pause();
    await page.getByRole('button', { name: /Отправить приглашение/ }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await page.getByRole('link', { name: 'Приглашения', exact: true }).first().click(); await pause();
    await expect(page.getByText(`${key}.contact@example.org`, { exact: false })).toHaveCount(0);
    await visit('/auth');
    await page.getByLabel('Электронная почта').fill(email);
    await page.getByLabel('Пароль', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Войти →', exact: true }).click();
    await page.waitForURL('**/app');
    await page.getByRole('link', { name: 'Приглашения', exact: true }).first().click(); await pause();
    await page.getByRole('button', { name: /Принять/ }).click(); await pause();
    await visit('/auth');
    await page.getByRole('button', { name: 'Кабинет работодателя', exact: true }).click();
    await page.waitForURL('**/app');
    await page.getByRole('link', { name: 'Приглашения', exact: true }).first().click();
    await expect(page.getByText(`${key}.contact@example.org`, { exact: false })).toBeVisible(); await pause();
    if (errors.length) throw new Error(errors.join('; '));
    await context.close();
    const output = path.join(root, '.local/demo.webm');
    await video.saveAs(output);
    console.log(output);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });


