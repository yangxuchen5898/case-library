import { expect } from "@playwright/test";

export const USER = {
  username: "e2e_user",
  password: "E2eUserPass123!",
  nickname: "E2E作者",
};

export const ADMIN = {
  username: "e2e_admin",
  password: "E2eAdminPass123!",
  nickname: "E2E管理员",
};

export async function login(page, account) {
  await page.getByRole("button", { name: "登录" }).click();
  await page.getByLabel("用户名").fill(account.username);
  await page.getByLabel("密码").fill(account.password);
  await page.locator(".modal-panel").getByRole("button", { name: "登录" }).click();
  await expect(page.locator(".user-name")).toContainText(account.nickname);
}

export async function logout(page) {
  await page.getByRole("button", { name: "退出" }).click();
  await expect(page.getByRole("button", { name: "登录" })).toBeVisible();
}

export async function capture(page, testInfo, name) {
  await expect(page.locator(".toast")).toHaveCount(0, { timeout: 4000 });
  await page.screenshot({
    path: testInfo.outputPath(`${name}-${testInfo.project.name}.png`),
    fullPage: true,
  });
}

export async function cleanupAuditCases(page, titlePrefix = "Audit案例 ") {
  const token = await page.evaluate(() => localStorage.getItem("case_library_auth_token"));
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await page.request.get("/api/cases?status=all&limit=100", { headers });
  if (!response.ok()) return;
  const payload = await response.json();
  const cases = Array.isArray(payload.data) ? payload.data : [];
  for (const item of cases.filter((c) => c.title?.startsWith(titlePrefix))) {
    await page.request.delete(`/api/cases/${item.id}`, { headers });
  }
}

export async function fillCaseToAiReviewStep(page, title, content, sourceMaterial) {
  await page.getByRole("link", { name: "创建案例" }).click();
  await page.getByLabel(/案例标题/).fill(title);
  await page.getByLabel(/所属部门\/学院/).fill("马克思主义学院");
  await page.getByRole("button", { name: "继续" }).click();

  await page.locator("#ccf-content").fill(content);
  await page.locator("#ccf-source").fill(sourceMaterial);
  await page.getByRole("button", { name: "继续" }).click();

  await page.locator("#ccf-type").selectOption("TYPE_A");
  await page.locator("#ccf-theme").selectOption("铸魂育人");
  await page.getByRole("button", { name: "继续" }).click();

  await expect(page.getByRole("heading", { name: "提交前自查" })).toBeVisible();
}
