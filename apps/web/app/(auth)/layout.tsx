import type { ReactNode } from "react";
import "../account/account.css";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return <section className="auth-route">{children}</section>;
}
