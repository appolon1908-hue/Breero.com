import Image from "next/image";
import Link from "next/link";

export function Logo({ light = false, priority = false }: { light?: boolean; priority?: boolean }) {
  return (
    <Link className="brand-logo" href="/" aria-label="BREERO home">
      <Image
        src={light ? "/brand/breero-logo-white.svg" : "/brand/breero-logo-dark.svg"}
        alt="BREERO"
        width={165}
        height={32}
        priority={priority}
      />
    </Link>
  );
}
