import { expect, test } from "@playwright/test";

const viewports = [
  { width: 375, height: 812 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1024, height: 768 },
  { width: 1280, height: 900 },
  { width: 1440, height: 1000 },
  { width: 1920, height: 1080 },
];

for (const viewport of viewports) {
  test(`shell is responsive at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
    if (viewport.width <= 900) {
      await expect(page.getByRole("button", { name: "Open menu" })).toBeVisible();
      await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeHidden();
      await page.getByRole("button", { name: "Open menu" }).click();
      await expect(page.getByRole("navigation", { name: "Mobile navigation" })).toBeVisible();
    } else {
      await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeVisible();
    }
    await page.screenshot({ path: `test-results/home-${viewport.width}.png`, fullPage: true });
  });
}

test("keyboard focus is visible and skip navigation works", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to main content" })).toBeFocused();
  await expect(page.getByRole("link", { name: "Skip to main content" })).toHaveCSS(
    "transform",
    "none",
  );
});
