import { ArrowRightIcon, Container, Section } from "@breero/ui";
import Link from "next/link";
export default function NotFound() {
  return (
    <Section spacing="xl">
      <Container size="sm">
        <div className="not-found">
          <span>404</span>
          <h1>This room looks empty</h1>
          <p>The page may have moved, but we can help you find your way home.</p>
          <Link className="br-button br-button--primary br-button--md" href="/services">
            <span>Explore services</span>
            <ArrowRightIcon />
          </Link>
          <Link className="not-found__link" href="/">
            Return to home
          </Link>
        </div>
      </Container>
    </Section>
  );
}
