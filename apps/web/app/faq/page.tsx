import { supportMetadata } from "@/components/marketing/SupportPage";
import { StandardPage } from "@/components/marketing/StandardPage";
import { supportPages } from "@/content/pages/support";
export const metadata = supportMetadata("faq");
export default function Page() {
  return <StandardPage content={supportPages.faq} faqLimit={null} />;
}
