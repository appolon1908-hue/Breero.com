import type { ReactNode } from "react";

export function AuthCard({
  eyebrow,
  title,
  description,
  children,
  footer,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="auth-wrap">
      <div className="auth-card">
        {eyebrow && <span className="auth-card__eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        <p>{description}</p>
        {children}
        {footer && <footer>{footer}</footer>}
      </div>
      <aside className="auth-promise">
        <span>BREERO protected</span>
        <blockquote>“Everything for your home, with one trusted team behind you.”</blockquote>
        <ul>
          <li>Vetted local professionals</li>
          <li>Protected, transparent payments</li>
          <li>Real support when you need it</li>
        </ul>
      </aside>
    </div>
  );
}
