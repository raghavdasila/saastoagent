import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it } from "vitest";

const surfaceStyles = readFileSync(resolve(process.cwd(), "src/styles.css"), "utf8");

it("keeps dock spacing outside the vertical surface scrollport", () => {
  expect(surfaceStyles).toContain(
    "[data-agent-surface-dock] { width: min(860px, 100%);",
  );
  expect(surfaceStyles).toContain("overflow-y: auto; margin: 10px auto 0;");
  expect(surfaceStyles).not.toContain(
    "[data-agent-surface-dock] { width: min(860px, 100%); max-width: 100%; max-height: min(46dvh, 520px); min-width: 0; overflow-x: clip; overflow-y: auto; margin: 0 auto; padding-top:",
  );
});

it("keeps maximized surface spacing at zero", () => {
  expect(surfaceStyles).toContain(
    '[data-agent-shell][data-surface-layout="split"] > [data-agent-surface-dock] { grid-area: surface; width: 100%; max-height: none; height: 100%; margin: 0; padding: 0;',
  );
});
