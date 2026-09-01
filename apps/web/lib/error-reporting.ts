export interface FrontendErrorContext {
  route?: string;
  requestId?: string;
  tags?: Record<string, string>;
}
export interface ErrorReporter {
  capture(error: unknown, context?: FrontendErrorContext): void | Promise<void>;
}
const noop: ErrorReporter = { capture: () => undefined };
let reporter: ErrorReporter = noop;

export function configureErrorReporter(next: ErrorReporter): () => void {
  reporter = next;
  return () => {
    reporter = noop;
  };
}
export function reportFrontendError(error: unknown, context?: FrontendErrorContext): void {
  void reporter.capture(error, context);
}
