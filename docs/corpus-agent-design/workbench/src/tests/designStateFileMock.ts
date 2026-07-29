import { vi } from "vitest"

let fileContents: string | null = null

export function setDesignStateFile(contents: string | null): void {
  fileContents = contents
}

export function getDesignStateFile(): string | null {
  return fileContents
}

export function installDesignStateFileMock(): void {
  fileContents = null
  vi.stubGlobal("fetch", vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    const method = init?.method ?? "GET"
    if (method === "GET") {
      if (fileContents === null) return { ok: false, status: 404, json: async () => ({}), text: async () => "" } as Response
      return { ok: true, status: 200, json: async () => JSON.parse(fileContents!), text: async () => fileContents! } as Response
    }
    if (method === "PUT") {
      fileContents = String(init?.body ?? "")
      return { ok: true, status: 204, json: async () => ({}), text: async () => "" } as Response
    }
    return { ok: false, status: 405, json: async () => ({}), text: async () => "" } as Response
  }))
}

export function removeDesignStateFileMock(): void {
  vi.unstubAllGlobals()
}
