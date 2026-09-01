import Image from "next/image";
export function BrandMark({ size = 40 }: { size?: number }) {
  return <Image src="/brand/breero-symbol-primary.svg" alt="" width={size} height={size} />;
}
