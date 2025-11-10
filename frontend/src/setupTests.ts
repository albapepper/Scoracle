// jest-dom adds custom jest matchers for asserting on DOM nodes.
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Polyfill ResizeObserver for Mantine components in jsdom
class MockResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

declare global {
  interface Window { ResizeObserver: typeof MockResizeObserver }
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace NodeJS { interface Global { ResizeObserver: typeof MockResizeObserver } }
}

if (typeof window !== 'undefined') {
  (window as any).ResizeObserver = MockResizeObserver as any;
}
if (typeof global !== 'undefined') {
  (global as any).ResizeObserver = MockResizeObserver as any;
}
