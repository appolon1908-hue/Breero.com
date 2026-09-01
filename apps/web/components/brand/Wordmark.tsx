import Image from "next/image";
export function Wordmark({ light = false }: { light?: boolean }) {
  return (
    <Image
      src={light ? "/brand/breero-wordmark-white.svg" : "/brand/breero-wordmark-dark.svg"}
      alt="BREERO"
      width={129}
      height={32}
    />
  );
}
