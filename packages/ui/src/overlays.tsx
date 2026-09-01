"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { CloseIcon } from "./icons";
import { IconButton } from "./primitives";
import { cx } from "./utils";

type OverlayProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
};

function Overlay({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
  kind,
}: OverlayProps & { kind: "dialog" | "drawer" | "sheet" }) {
  const titleId = useId();
  const descriptionId = useId();
  const panel = useRef<HTMLDivElement>(null);
  const close = useCallback(() => onOpenChange(false), [onOpenChange]);
  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const frame = requestAnimationFrame(() => {
      const firstFocusable = panel.current?.querySelector<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      (firstFocusable || panel.current)?.focus();
    });
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
      if (event.key !== "Tab" || !panel.current) return;
      const focusable = Array.from(
        panel.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (!focusable.length) {
        event.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      cancelAnimationFrame(frame);
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", keydown);
      previous?.focus();
    };
  }, [open, close]);
  if (!open || typeof document === "undefined") return null;
  return createPortal(
    <div
      className={cx("br-overlay", `br-overlay--${kind}`)}
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div
        ref={panel}
        className={cx("br-overlay__panel", className)}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
      >
        <header className="br-overlay__header">
          <div>
            <h2 id={titleId}>{title}</h2>
            {description && <p id={descriptionId}>{description}</p>}
          </div>
          <IconButton label="Close" onClick={close}>
            <CloseIcon />
          </IconButton>
        </header>
        <div className="br-overlay__content">{children}</div>
        {footer && <footer className="br-overlay__footer">{footer}</footer>}
      </div>
    </div>,
    document.body,
  );
}

export const Dialog = (props: OverlayProps) => <Overlay kind="dialog" {...props} />;
export const Modal = Dialog;
export const Drawer = (props: OverlayProps) => <Overlay kind="drawer" {...props} />;
export const Sheet = (props: OverlayProps) => <Overlay kind="sheet" {...props} />;

type ToastItem = {
  id: number;
  title: string;
  description?: string;
  variant?: "info" | "success" | "warning" | "error";
};
const ToastContext = createContext<{ toast: (toast: Omit<ToastItem, "id">) => void } | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const toast = useCallback((item: Omit<ToastItem, "id">) => {
    const id = Date.now();
    setItems((current) => [...current, { ...item, id }]);
    window.setTimeout(
      () => setItems((current) => current.filter((toastItem) => toastItem.id !== id)),
      5000,
    );
  }, []);
  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="br-toasts" aria-live="polite" aria-atomic="true">
        {items.map((item) => (
          <div className={cx("br-toast", `br-toast--${item.variant || "info"}`)} key={item.id}>
            <div>
              <strong>{item.title}</strong>
              {item.description && <p>{item.description}</p>}
            </div>
            <IconButton
              size="sm"
              label="Dismiss notification"
              onClick={() =>
                setItems((current) => current.filter((toastItem) => toastItem.id !== item.id))
              }
            >
              <CloseIcon size={16} />
            </IconButton>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside ToastProvider");
  return context;
}
