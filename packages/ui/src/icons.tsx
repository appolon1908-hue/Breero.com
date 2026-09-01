import type { SVGProps } from "react";

type Props = SVGProps<SVGSVGElement> & { size?: number };

function IconBase({ size = 20, children, ...props }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const SearchIcon = (props: Props) => (
  <IconBase {...props}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-4-4" />
  </IconBase>
);
export const MenuIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </IconBase>
);
export const CloseIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="m6 6 12 12M18 6 6 18" />
  </IconBase>
);
export const ArrowRightIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="M5 12h14m-5-5 5 5-5 5" />
  </IconBase>
);
export const ChevronDownIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="m7 10 5 5 5-5" />
  </IconBase>
);
export const ChevronRightIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="m9 18 6-6-6-6" />
  </IconBase>
);
export const CheckIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="m5 12 4 4L19 6" />
  </IconBase>
);
export const AlertIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="M12 8v5m0 3h.01" />
    <path d="M10.3 3.7 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z" />
  </IconBase>
);
export const UploadIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="M12 16V4m-4 4 4-4 4 4M5 20h14" />
  </IconBase>
);
export const CalendarIcon = (props: Props) => (
  <IconBase {...props}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M16 3v4M8 3v4M3 10h18" />
  </IconBase>
);
export const UserIcon = (props: Props) => (
  <IconBase {...props}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21a8 8 0 0 1 16 0" />
  </IconBase>
);
export const HomeIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="m3 11 9-8 9 8M5 10v10h14V10M9 20v-6h6v6" />
  </IconBase>
);
export const ShieldIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
    <path d="m9 12 2 2 4-4" />
  </IconBase>
);
export const StarIcon = (props: Props) => (
  <IconBase {...props}>
    <path d="m12 2 3 6 6.5 1-4.7 4.6 1.1 6.4-5.9-3-5.9 3 1.1-6.4L2.5 9 9 8l3-6Z" />
  </IconBase>
);
export const ClockIcon = (props: Props) => (
  <IconBase {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </IconBase>
);
