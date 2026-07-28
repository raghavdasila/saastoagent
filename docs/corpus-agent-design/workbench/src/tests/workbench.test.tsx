import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import App from "@/App"
import { createSeedState } from "@/workbench/seed"
import { LEGACY_STORAGE_KEY, STORAGE_KEY, V2_STORAGE_KEY } from "@/workbench/storage"
import { THEME_STORAGE_KEY } from "@/workbench/theme"

describe("Slice 1 design workbench", () => {
  it("switches between the Workspace and Agents feature stories", async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(screen.getByRole("heading", { name: "Enter the workspace" })).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Agents/ }))

    expect(screen.getByRole("heading", { name: "Create a draft agent" })).toBeInTheDocument()
  })

  it("uses a compact title and user-story editor", () => {
    render(<App />)

    expect(screen.getByLabelText("Title")).toBeInTheDocument()
    expect(screen.getByLabelText("User story")).toBeInTheDocument()
    expect(screen.queryByLabelText("Situation")).not.toBeInTheDocument()
    expect(screen.queryByLabelText("Expected behavior")).not.toBeInTheDocument()
  })

  it("adds and selects a blank story under the current feature", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole("button", { name: "Add story" }))

    expect(screen.getByRole("heading", { name: "New user story" })).toBeInTheDocument()
    expect(screen.getByLabelText("User story")).toHaveValue("")
    expect(screen.getByRole("button", { name: "Workspace 9" })).toBeInTheDocument()
    expect(localStorage.getItem(STORAGE_KEY)).toContain("New user story")
  })

  it("returns a reviewed story to draft when it is reopened and edited", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole("button", { name: "Approve story" }))
    expect(screen.getByText("Approved")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "Reopen draft" }))
    const story = screen.getByLabelText("User story")
    await user.clear(story)
    await user.type(story, "As an owner, I want to see the workspace before configuring anything.")

    expect(screen.getByText("Draft")).toBeInTheDocument()
  })

  it("requires and records a rejection reason", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole("button", { name: "Reject story" }))
    expect(screen.getByLabelText("Why reject this story?")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Confirm rejection" }))
    expect(screen.getByRole("alert")).toHaveTextContent("Add a reason before rejecting")

    await user.type(screen.getByLabelText("Why reject this story?"), "The entry point is unclear.")
    await user.click(screen.getByRole("button", { name: "Confirm rejection" }))

    expect(screen.getByText("Rejected")).toBeInTheDocument()
    expect(screen.getByText("The entry point is unclear.")).toBeInTheDocument()
  })

  it("renders the mock surface in a no-permissions sandbox", () => {
    render(<App />)

    const frame = screen.getByTitle("Mock surface: Enter the workspace")
    expect(frame).toHaveAttribute("src", "/mock-surfaces/workspace/enter-workspace.html")
    expect(frame).toHaveAttribute("sandbox", "")
  })

  it("seeds the proven owner authentication behaviors as approved Workspace stories", async () => {
    const user = userEvent.setup()
    const workspace = createSeedState().features.find((feature) => feature.id === "workspace")
    const authenticationStories = workspace?.stories.filter((story) => story.id.startsWith("owner-auth-")) ?? []

    expect(authenticationStories).toHaveLength(7)
    expect(authenticationStories.every((story) => story.status === "approved")).toBe(true)
    expect(authenticationStories.every((story) => story.mockSurfacePath?.startsWith("/mock-surfaces/workspace/authentication.html#"))).toBe(true)

    render(<App />)
    expect(screen.getByRole("button", { name: "Workspace 8" })).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Create an owner account" }))

    expect(screen.getByText("Approved")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Reopen draft" })).toBeInTheDocument()
    expect(screen.getByTitle("Mock surface: Create an owner account")).toHaveAttribute(
      "src",
      "/mock-surfaces/workspace/authentication.html#register",
    )
  })

  it("persists slate dark mode and applies it to the surface preview", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole("button", { name: "Switch to dark mode" }))

    expect(document.documentElement).toHaveClass("dark")
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark")
    expect(screen.getByTitle("Mock surface: Enter the workspace")).toHaveStyle({ colorScheme: "dark" })
    expect(screen.getByRole("button", { name: "Switch to light mode" })).toBeInTheDocument()
  })

  it("persists edits explicitly in local storage", async () => {
    const user = userEvent.setup()
    render(<App />)

    const story = screen.getByLabelText("User story")
    await user.clear(story)
    await user.type(story, "As an owner, I want one clear next step.")

    const stored = localStorage.getItem(STORAGE_KEY)
    expect(stored).toContain("As an owner, I want one clear next step.")
  })

  it("migrates the original five-field story without discarding its content", () => {
    localStorage.setItem(LEGACY_STORAGE_KEY, JSON.stringify({
      version: 1,
      features: [{
        id: "workspace",
        name: "Workspace",
        stories: [{
          id: "legacy-story",
          title: "Legacy story",
          situation: "An owner arrives.",
          userNeed: "They need a starting point.",
          expectedBehavior: "Corpus shows one action.",
          outcome: "They can continue.",
          messages: [],
          mockSurfacePath: null,
          status: "draft",
          rejectionReason: "",
        }],
      }],
    }))

    render(<App />)

    expect(screen.getByRole("heading", { name: "Legacy story" })).toBeInTheDocument()
    expect((screen.getByLabelText("User story") as HTMLTextAreaElement).value).toContain("They need a starting point.")
    expect(screen.getByRole("button", { name: "Workspace 9" })).toBeInTheDocument()
  })

  it("migrates version 2 edits and adds missing locked authentication stories", () => {
    const version2 = createSeedState()
    const workspace = version2.features.find((feature) => feature.id === "workspace")!
    localStorage.setItem(V2_STORAGE_KEY, JSON.stringify({
      ...version2,
      version: 2,
      features: version2.features.map((feature) => feature.id === "workspace"
        ? { ...feature, stories: [{ ...workspace.stories[0], title: "My edited entry story" }] }
        : feature),
    }))

    render(<App />)

    expect(screen.getByRole("heading", { name: "My edited entry story" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Workspace 8" })).toBeInTheDocument()
    expect(localStorage.getItem(STORAGE_KEY)).toContain("owner-auth-register")
  })

  it.each(["not-json", JSON.stringify({ version: 3, features: [] })])("shows a blocking recovery state for invalid saved data", (saved) => {
    localStorage.setItem(STORAGE_KEY, saved)
    render(<App />)

    const alert = screen.getByRole("alert")
    expect(within(alert).getByText("The saved workbench data is invalid.")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Reset local workspace" })).toBeInTheDocument()
  })
})
