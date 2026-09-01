import { faqs } from "@/content/faqs";
export function FAQ({ limit }: { limit?: number }) {
  return (
    <div className="mk-faq">
      {faqs.slice(0, limit).map((item) => (
        <details key={item.question}>
          <summary>{item.question}</summary>
          <p>{item.answer}</p>
        </details>
      ))}
    </div>
  );
}
