import { Container, LoadingState, Section } from "@breero/ui";
export default function Loading() {
  return (
    <Section>
      <Container size="md">
        <LoadingState label="Getting things ready" rows={4} />
      </Container>
    </Section>
  );
}
