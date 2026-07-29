import "@testing-library/jest-dom/vitest"

import { installDesignStateFileMock, removeDesignStateFileMock } from "@/tests/designStateFileMock"

beforeEach(() => {
  installDesignStateFileMock()
  localStorage.clear()
  document.documentElement.classList.remove("dark")
})

afterEach(() => removeDesignStateFileMock())
