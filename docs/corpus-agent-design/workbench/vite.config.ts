import { promises as fs } from "node:fs"
import type { IncomingMessage, ServerResponse } from "node:http"
import path from "node:path"
import { fileURLToPath } from "node:url"

import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig, type Plugin } from "vite"

const directory = path.dirname(fileURLToPath(import.meta.url))
const designStatePath = path.resolve(directory, "design-state.json")

function sendJson(response: ServerResponse, status: number, value: unknown): void {
  response.statusCode = status
  response.setHeader("Content-Type", "application/json; charset=utf-8")
  response.end(JSON.stringify(value))
}

async function readRequestBody(request: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = []
  let size = 0
  for await (const chunk of request) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)
    size += buffer.length
    if (size > 10 * 1024 * 1024) throw new Error("design state exceeds 10 MB")
    chunks.push(buffer)
  }
  return Buffer.concat(chunks).toString("utf8")
}

function designStatePlugin(): Plugin {
  let writeQueue: Promise<void> = Promise.resolve()
  return {
    name: "corpus-design-state-file",
    configureServer(server) {
      server.middlewares.use(async (request, response, next) => {
        const requestUrl = new URL(request.url ?? "/", "http://127.0.0.1")
        if (requestUrl.pathname !== "/__design-studio/state") {
          next()
          return
        }

        if (request.method === "GET") {
          try {
            const contents = await fs.readFile(designStatePath, "utf8")
            response.statusCode = 200
            response.setHeader("Content-Type", "application/json; charset=utf-8")
            response.end(contents)
          } catch (error) {
            if ((error as NodeJS.ErrnoException).code === "ENOENT") {
              sendJson(response, 404, { code: "design_state_not_initialized" })
              return
            }
            sendJson(response, 500, { code: "design_state_read_failed" })
          }
          return
        }

        if (request.method === "PUT") {
          try {
            const body = await readRequestBody(request)
            const parsed: unknown = JSON.parse(body)
            if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
              sendJson(response, 400, { code: "invalid_design_state" })
              return
            }
            const candidate = parsed as Record<string, unknown>
            if (typeof candidate.version !== "number" || !Array.isArray(candidate.features) || candidate.features.length === 0) {
              sendJson(response, 400, { code: "invalid_design_state" })
              return
            }

            const serialized = `${JSON.stringify(parsed, null, 2)}\n`
            writeQueue = writeQueue.then(async () => {
              const temporaryPath = `${designStatePath}.tmp`
              await fs.writeFile(temporaryPath, serialized, "utf8")
              await fs.rename(temporaryPath, designStatePath)
            })
            await writeQueue
            response.statusCode = 204
            response.end()
          } catch {
            sendJson(response, 500, { code: "design_state_write_failed" })
          }
          return
        }

        response.setHeader("Allow", "GET, PUT")
        sendJson(response, 405, { code: "method_not_allowed" })
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), designStatePlugin()],
  server: { watch: { ignored: [designStatePath] } },
  resolve: {
    alias: { "@": path.resolve(directory, "src") },
    dedupe: ["react", "react-dom"],
  },
})
