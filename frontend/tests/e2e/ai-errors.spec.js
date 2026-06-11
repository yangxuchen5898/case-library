import { test, expect } from "@playwright/test";
import {
  ADMIN,
  USER,
  capture,
  cleanupAuditCases,
  fillCaseToAiReviewStep,
  login,
  logout,
} from "./helpers.js";

test.describe("AI review error handling", () => {
  test("AI review disabled response shows a clear author-side error", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "desktop-only AI disabled messaging regression"
    );

    await page.route("**/api/cases/*/ai-review", async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          status: "disabled",
          detail: "AI 审核功能未启用",
        }),
      });
    });

    await page.goto("/");
    await login(page, ADMIN);
    await cleanupAuditCases(page, "AI禁用提示案例 ");
    await logout(page);

    await login(page, USER);
    await fillCaseToAiReviewStep(
      page,
      `AI禁用提示案例 ${Date.now()}`,
      "本案例用于验证 AI 禁用时前端提示清晰，不误导作者。",
      "来源材料：AI 禁用提示测试。"
    );
    await page.getByRole("button", { name: "生成只读审核版本" }).click();
    await expect(page.getByText("AI 审核功能未启用")).toBeVisible();
    await expect(page.getByText(/已生成 v\d+ 只读审核版本/)).toHaveCount(0);
    await expect(page.getByText("AI 批注")).toHaveCount(0);
    await capture(page, testInfo, "create-step-4-ai-disabled");
  });

  test("AI review unavailable response keeps the author on an explicit error state", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "desktop-only AI unavailable messaging regression"
    );

    await page.route("**/api/cases/*/ai-review", async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          status: "unavailable",
          detail: "AI 服务暂不可用，请稍后重试",
        }),
      });
    });

    await page.goto("/");
    await login(page, ADMIN);
    await cleanupAuditCases(page, "AI不可用提示案例 ");
    await logout(page);

    await login(page, USER);
    await fillCaseToAiReviewStep(
      page,
      `AI不可用提示案例 ${Date.now()}`,
      "本案例用于验证 AI 服务异常时前端提示清晰，不误导作者。",
      "来源材料：AI 服务异常提示测试。"
    );
    await page.getByRole("button", { name: "生成只读审核版本" }).click();
    await expect(page.getByText("AI 服务暂不可用，请稍后重试")).toBeVisible();
    await expect(page.getByText(/已生成 v\d+ 只读审核版本/)).toHaveCount(0);
    await expect(page.getByText("AI 批注")).toHaveCount(0);
    await capture(page, testInfo, "create-step-4-ai-unavailable");
  });
});
