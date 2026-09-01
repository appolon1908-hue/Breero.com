"use client";

import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
  type ReactNode,
} from "react";
import { CalendarIcon, CheckIcon, ChevronDownIcon, SearchIcon, UploadIcon } from "./icons";
import { cx } from "./utils";

export function FormField({
  label,
  hint,
  error,
  required,
  htmlFor,
  children,
  className,
}: {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  htmlFor?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx("br-field", error && "br-field--error", className)}>
      <label className="br-label" htmlFor={htmlFor}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
      {children}
      {(error || hint) && (
        <p className="br-field__message" role={error ? "alert" : undefined}>
          {error || hint}
        </p>
      )}
    </div>
  );
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return <input ref={ref} className={cx("br-input", className)} {...props} />;
  },
);

export const SearchInput = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement> & { onClear?: () => void }
>(function SearchInput({ className, onClear, value, ...props }, ref) {
  return (
    <div className={cx("br-input-wrap", "br-search", className)}>
      <SearchIcon />
      <input ref={ref} type="search" value={value} {...props} />
      {onClear && value && (
        <button type="button" onClick={onClear} aria-label="Clear search">
          Clear
        </button>
      )}
    </div>
  );
});

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, children, ...props }, ref) {
    return (
      <span className={cx("br-select-wrap", className)}>
        <select ref={ref} className="br-select" {...props}>
          {children}
        </select>
        <ChevronDownIcon />
      </span>
    );
  },
);

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...props }, ref) {
  return <textarea ref={ref} className={cx("br-textarea", className)} {...props} />;
});

export const Checkbox = forwardRef<
  HTMLInputElement,
  Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: ReactNode; description?: string }
>(function Checkbox({ label, description, className, id: providedId, ...props }, ref) {
  const generatedId = useId();
  const id = providedId || generatedId;
  return (
    <label className={cx("br-check", className)} htmlFor={id}>
      <input ref={ref} id={id} type="checkbox" {...props} />
      <span className="br-check__control">
        <CheckIcon size={15} />
      </span>
      <span>
        <strong>{label}</strong>
        {description && <small>{description}</small>}
      </span>
    </label>
  );
});

export const Radio = forwardRef<
  HTMLInputElement,
  Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: ReactNode; description?: string }
>(function Radio({ label, description, className, id: providedId, ...props }, ref) {
  const generatedId = useId();
  const id = providedId || generatedId;
  return (
    <label className={cx("br-check", "br-radio", className)} htmlFor={id}>
      <input ref={ref} id={id} type="radio" {...props} />
      <span className="br-check__control" />
      <span>
        <strong>{label}</strong>
        {description && <small>{description}</small>}
      </span>
    </label>
  );
});

export const ChoiceCard = forwardRef<
  HTMLInputElement,
  Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
    type?: "radio" | "checkbox";
    title: string;
    description?: string;
    icon?: ReactNode;
  }
>(function ChoiceCard(
  { type = "radio", title, description, icon, className, id: providedId, ...props },
  ref,
) {
  const generatedId = useId();
  const id = providedId || generatedId;
  return (
    <label className={cx("br-choice", className)} htmlFor={id}>
      <input ref={ref} id={id} type={type} {...props} />
      <span className="br-choice__body">
        {icon && <span className="br-choice__icon">{icon}</span>}
        <span>
          <strong>{title}</strong>
          {description && <small>{description}</small>}
        </span>
        <span className="br-choice__mark">
          <CheckIcon size={14} />
        </span>
      </span>
    </label>
  );
});

export function DateSelector({
  dates,
  value,
  onChange,
  label = "Choose a date",
  name,
}: {
  dates: Array<{ value: string; day: string; date: string; note?: string; disabled?: boolean }>;
  value?: string;
  onChange?: (value: string) => void;
  label?: string;
  name?: string;
}) {
  const generatedName = useId();
  return (
    <fieldset className="br-date-selector">
      <legend className="br-sr-only">{label}</legend>
      {dates.map((item) => (
        <label key={item.value} className="br-date">
          <input
            type="radio"
            name={name || generatedName}
            value={item.value}
            checked={value === item.value}
            disabled={item.disabled}
            onChange={() => onChange?.(item.value)}
          />
          <span>
            <CalendarIcon size={18} />
            <small>{item.day}</small>
            <strong>{item.date}</strong>
            {item.note && <em>{item.note}</em>}
          </span>
        </label>
      ))}
    </fieldset>
  );
}

export function TimeSlot({
  value,
  label,
  selected,
  disabled,
  note,
  onSelect,
}: {
  value: string;
  label: string;
  selected?: boolean;
  disabled?: boolean;
  note?: string;
  onSelect?: (value: string) => void;
}) {
  return (
    <button
      type="button"
      className={cx("br-time-slot", selected && "is-selected")}
      disabled={disabled}
      aria-pressed={selected}
      onClick={() => onSelect?.(value)}
    >
      <strong>{label}</strong>
      {note && <small>{note}</small>}
    </button>
  );
}

export const AddressField = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement> & {
    status?: "idle" | "checking" | "valid" | "invalid";
    statusMessage?: string;
  }
>(function AddressField({ status = "idle", statusMessage, className, ...props }, ref) {
  return (
    <div className={cx("br-address", `br-address--${status}`, className)}>
      <Input ref={ref} autoComplete="street-address" {...props} />
      {statusMessage && (
        <span role={status === "invalid" ? "alert" : "status"}>
          {status === "valid" && <CheckIcon size={16} />}
          {status === "checking" && <span className="br-spinner" />}
          {statusMessage}
        </span>
      )}
    </div>
  );
});

export function FileUpload({
  label = "Choose a file",
  description = "PDF, DOC or image up to 10MB",
  accept,
  multiple,
  disabled,
  onChange,
}: {
  label?: string;
  description?: string;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  onChange?: InputHTMLAttributes<HTMLInputElement>["onChange"];
}) {
  const id = useId();
  return (
    <label className={cx("br-upload", disabled && "is-disabled")} htmlFor={id}>
      <input
        id={id}
        className="br-sr-only"
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        onChange={onChange}
      />
      <UploadIcon />
      <strong>{label}</strong>
      <small>{description}</small>
    </label>
  );
}

export function PhotoUpload(props: Omit<Parameters<typeof FileUpload>[0], "accept">) {
  return (
    <FileUpload
      accept="image/jpeg,image/png,image/webp"
      label="Add photos"
      description="JPG, PNG or WebP up to 10MB"
      multiple
      {...props}
    />
  );
}
