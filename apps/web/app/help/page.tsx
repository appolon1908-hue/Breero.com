import { SupportPage, supportMetadata } from "@/components/marketing/SupportPage";
export const metadata = supportMetadata("help");
export default function Page() {
  return <SupportPage slug="help" />;
}
