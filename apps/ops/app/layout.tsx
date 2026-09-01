import type { Metadata } from "next";
import "@breero/portal/styles.css";
export const metadata: Metadata = {
  title: "BREERO Operations",
  description: "Secure BREERO operations workspace",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
