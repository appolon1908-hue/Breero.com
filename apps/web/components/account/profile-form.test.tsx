import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProfileForm } from "./profile-form";

const { profile, updateProfile } = vi.hoisted(() => ({
  profile: vi.fn().mockResolvedValue({
    id: "customer-1",
    email: "maya@example.com",
    full_name: "Maya Thompson",
    phone: "+44 7700 900123",
    email_verified: true,
  }),
  updateProfile: vi.fn().mockResolvedValue({}),
}));
vi.mock("@/lib/customer/api", () => ({ customerApi: { customer: { profile, updateProfile } } }));

describe("ProfileForm", () => {
  it("presents live customer details without allowing email edits", async () => {
    render(<ProfileForm />);
    expect(await screen.findByLabelText("Email")).toBeDisabled();
    expect(screen.getByLabelText(/Full name/)).toHaveValue("Maya Thompson");
  });
  it("submits backend-supported profile fields", async () => {
    render(<ProfileForm />);
    fireEvent.change(await screen.findByLabelText("Phone number"), {
      target: { value: "+44 7700 900999" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByRole("status")).toHaveTextContent("updated");
    expect(updateProfile).toHaveBeenCalledWith(
      expect.objectContaining({ phone: "+44 7700 900999", full_name: "Maya Thompson" }),
    );
  });
});
