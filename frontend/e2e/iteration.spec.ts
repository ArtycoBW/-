import { test, expect } from "@playwright/test";

test("профиль из целой карточки аккаунта и справочные окна сохраняют контекст", async ({page}) => {
  await page.goto("/auth");
  await page.getByRole("button",{name:"Кабинет специалиста",exact:true}).click();
  await page.waitForURL("**/app");
  const sidebar=page.locator(".rz-sidebar");
  await expect(sidebar.getByRole("link",{name:"Мой профиль",exact:true})).toHaveCount(0);
  await sidebar.getByRole("button",{name:"Меню аккаунта",exact:true}).getByText("Личный кабинет").click();
  await page.getByRole("menuitem",{name:"Мой профиль",exact:true}).click();
  await expect(page).toHaveURL(/\/app\/profile$/);
  await expect(page.getByRole("heading",{name:"Мой профиль",exact:true})).toBeVisible();
  await page.getByRole("combobox",{name:"Специализация",exact:true}).click();
  await expect(page.getByRole("option")).toHaveCount(10);
  await page.keyboard.press("Escape");
  const field=page.getByLabel("Город",{exact:true});
  await field.fill("Несохранённый город");
  for(const title of ["Приватность данных","Как работает подбор"]){
    await sidebar.getByRole("button",{name:title,exact:true}).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page).toHaveURL(/\/app\/profile$/);
    await page.keyboard.press("Escape");
    await expect(field).toHaveValue("Несохранённый город");
  }
  await sidebar.getByRole("link",{name:"Подтвердить уровень",exact:true}).hover();
  await expect(page.getByRole("tooltip")).toHaveCount(0);
  await page.getByRole("button",{name:"Свернуть меню",exact:true}).click();
  await sidebar.getByRole("link",{name:"Подтвердить уровень",exact:true}).hover();
  await expect(page.getByRole("tooltip")).toBeVisible();
  await expect(page.getByRole("tooltip").locator("svg")).toHaveCount(0);
});

test("широкая вакансия помещается на рабочем столе, практика сохраняет черновик", async({page}) => {
  await page.setViewportSize({width:1440,height:1000});
  await page.goto("/auth");
  await page.getByRole("button",{name:"Кабинет специалиста",exact:true}).click();
  await page.waitForURL("**/app");
  await page.goto("/app/vacancies");
  await page.getByRole("button",{name:"Подробнее",exact:true}).first().click();
  const bounds=await page.getByRole("dialog").boundingBox();
  expect(bounds!.width).toBeGreaterThan(950);
  expect(await page.locator(".rz-dialog-body").evaluate(e=>e.scrollHeight<=e.clientHeight+1)).toBeTruthy();
  await page.keyboard.press("Escape");
  await page.goto("/app/challenges");
  await page.getByRole("button",{name:"Доступные",exact:true}).click();
  await expect(page.locator(".rz-practice-card").first()).toBeVisible();
  const card=page.locator(".rz-practice-card").first();
  const title=await card.locator("h2").innerText();
  await card.getByRole("button",{name:"Решить задачу",exact:true}).click();
  await page.getByLabel("Ваш подход к решению").fill("Черновик проверки: начинаю с ограничений и описания граничных случаев.");
  await page.keyboard.press("Escape");
  await page.reload();
  await page.getByRole("textbox",{name:"Поиск заданий"}).fill(title);
  await page.getByRole("button",{name:"Решить задачу",exact:true}).first().click();
  await expect(page.getByLabel("Ваш подход к решению")).toHaveValue(/Черновик проверки/);
  await page.getByLabel("Ваш подход к решению").fill("");
});
