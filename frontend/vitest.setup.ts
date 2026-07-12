import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Testing Library's auto-cleanup relies on detecting a *global* `afterEach` — we deliberately
// don't set `test.globals: true` in vitest.config.mts (see its comment), so it has to be wired
// explicitly here instead. Without this, DOM from one test's render() leaks into the next
// test in the same file, and queries like getByText start matching multiple stale elements.
afterEach(() => {
  cleanup();
});
