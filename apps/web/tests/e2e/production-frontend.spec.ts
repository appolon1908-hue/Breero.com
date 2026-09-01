import { expect, test } from "@playwright/test";
import publicRoutes from "../../content/public-routes.json";

for (const route of publicRoutes.filter((path) => path !== "/book")) {
  test(`production frontend serves ${route}`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBe(200);
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page).toHaveTitle(/\S/);
    await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /\S/);
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
      "href",
      /^https:\/\/breero\.com(?:\/|$)/,
    );
  });
}

test("book enters the request-only manual-dispatch journey", async ({ page }) => {
  await page.goto("/book");
  await expect(page).toHaveURL(/\/request-service$/);
  await expect(page.locator("main")).toBeVisible();
  await expect(
    page.getByText(/not a confirmed booking, provider assignment, price or appointment/i),
  ).toBeVisible();
});

test("policy and contact surfaces expose the approved operator identity", async ({ page }) => {
  for (const route of [
    "/contact",
    "/terms",
    "/privacy",
    "/refund-policy",
    "/cancellation-policy",
    "/service-fulfillment-policy",
    "/professional-lead-policy",
  ]) {
    await page.goto(route);
    await expect(
      page.getByText("BREERO, operated by Codestra LLC", { exact: false }).first(),
    ).toBeVisible();
    await expect(page.getByText("support@breero.com", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("20633 Longenbaugh Rd", { exact: false }).first()).toBeVisible();
  }
});
