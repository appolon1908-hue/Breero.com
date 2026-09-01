import { expect, test } from "@playwright/test";

const widths = [375, 430, 768, 1024, 1280, 1440];
for (const width of widths) {
  test(`account dashboard is responsive at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/account");
    await expect(page.getByRole("heading", { name: /Hello, Maya/ })).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
    ).toBeLessThanOrEqual(0);
    if (width <= 900) await expect(page.getByLabel("Account section")).toBeVisible();
    else await expect(page.getByRole("navigation", { name: "Account navigation" })).toBeVisible();
    if ([375, 768, 1440].includes(width))
      await page.screenshot({ path: `test-results/account-${width}.png`, fullPage: true });
  });
}

test("booking detail exposes only customer-safe backend fields", async ({ page }) => {
  await page.goto("/account/bookings/BR-240817");
  await expect(page.getByRole("heading", { name: "BREERO home service", level: 1 })).toBeVisible();
  await expect(page.getByText("Booking BR-240817")).toBeVisible();
  await expect(page.getByText(/Provider secrets, internal pricing/)).toBeVisible();
});

test("customer can approve a quote without an online payment", async ({ page }) => {
  await page.goto("/account/quotes/QT-1048");
  await expect(
    page.getByText("Replace the worn mixer tap cartridge and test the seals."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Approve quote" }).click();
  await expect(page.getByText("Quote response saved")).toBeVisible();
  await expect(page.getByText(/does not collect online payment/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /payment/i })).toHaveCount(0);
});

test("session expiry gives a clear recovery path", async ({ page }) => {
  await page.goto("/account/session-expired");
  await expect(page.getByRole("heading", { name: "Your session has expired" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign in again" })).toHaveAttribute(
    "href",
    "/account/login",
  );
});

test("unknown customer resources use a recoverable error state", async ({ page }) => {
  await page.goto("/account/bookings/not-a-booking");
  await expect(page.getByRole("heading", { name: "Booking not available" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});
