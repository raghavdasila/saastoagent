import { writeFile } from "node:fs/promises"
import { resolve } from "node:path"

import { createServer } from "vite"

const root = resolve(import.meta.dirname, "..")
const server = await createServer({ root, server: { middlewareMode: true } })

try {
  const { createSeedState } = await server.ssrLoadModule("/src/workbench/seed.ts")
  await writeFile(resolve(root, "design-state.json"), `${JSON.stringify(createSeedState(), null, 2)}\n`, "utf8")
} finally {
  await server.close()
}
