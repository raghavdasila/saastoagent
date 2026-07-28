import "@testing-library/jest-dom/vitest"

beforeEach(() => {
  localStorage.clear()
  document.documentElement.classList.remove("dark")
})
