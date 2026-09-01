"use client";
import { Container, ErrorState, Section } from "@breero/ui";
export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <Section>
      <Container size="md">
        <ErrorState
          title="We hit a snag"
          description="Your information is safe. Try loading this page again."
          onRetry={reset}
        />
      </Container>
    </Section>
  );
}
