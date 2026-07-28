import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import App from "@/App"
import { createSeedState } from "@/workbench/seed"
import { resolveInlineSurfaceHeight } from "@/workbench/SurfacePreview"
import { LEGACY_STORAGE_KEY, STORAGE_KEY, V2_STORAGE_KEY, V3_STORAGE_KEY, V4_STORAGE_KEY } from "@/workbench/storage"
import { THEME_STORAGE_KEY } from "@/workbench/theme"

describe("Slice 1 design workbench", () => {
  it("switches between the Workspace and Agents feature stories", async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(screen.getByRole("heading", { name: "Enter the workspace" })).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Agents/ }))

    expect(screen.getByRole("heading", { name: "Create a draft agent" })).toBeInTheDocument()
  })

  it("keeps user and agent intent distinct from the user story", () => {
    render(<App />)

    expect(screen.getByLabelText("Title")).toBeInTheDocument()
    expect(screen.getByLabelText("User intent")).toHaveValue(
      "Return to my private Workspace and understand its current state.",
    )
    expect(screen.getByLabelText("Agent intent")).toHaveValue(
      "Establish the authenticated owner's Workspace as the active context and provide a truthful orientation with valid next choices.",
    )
    expect(screen.getByLabelText("User story")).toBeInTheDocument()
    expect(screen.queryByLabelText("Situation")).not.toBeInTheDocument()
    expect(screen.queryByLabelText("Expected behavior")).not.toBeInTheDocument()
  })

  it("adds and selects a blank story under the current feature", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole("button", { name: "Add story" }))

    expect(screen.getByRole("heading", { name: "New user story" })).toBeInTheDocument()
    expect(screen.getByLabelText("User intent")).toHaveValue("")
    expect(screen.getByLabelText("Agent intent")).toHaveValue("")
    expect(screen.getByLabelText("User story")).toHaveValue("")
    expect(screen.getByRole("button", { name: "Workspace 9" })).toBeInTheDocument()
    expect(localStorage.getItem(STORAGE_KEY)).toContain("New user story")
  })

  it("deletes a draft story only after explicit confirmation", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole("button", { name: "Add story" }))
    await user.click(screen.getByRole("button", { name: "Delete story" }))

    expect(screen.getByText('Delete "New user story"?')).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Confirm delete story" }))

    expect(screen.queryByRole("heading", { name: "New user story" })).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Workspace 8" })).toBeInTheDocument()
    expect(localStorage.getItem(STORAGE_KEY)).not.toContain("New user story")
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

  it("keeps actions separate from optional inline surfaces", () => {
    render(<App />)

    expect(screen.getByText("No inline surface")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Create an agent" })).toBeInTheDocument()
    expect(screen.queryByTitle("Mock surface: Enter the workspace")).not.toBeInTheDocument()
    expect(screen.getByText("Message Corpus...")).toBeInTheDocument()
  })

  it("renders a structured mock surface inline with only height-reporting scripts allowed", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole("button", { name: "Create an owner account" }))
    const frame = screen.getByTitle("Mock surface: Create an owner account")
    expect(frame).toHaveAttribute("src", "/mock-surfaces/workspace/authentication.html#register")
    expect(frame).toHaveAttribute("sandbox", "allow-scripts")
    expect(frame.getAttribute("sandbox")).not.toContain("allow-same-origin")
  })

  it("grows a surface to its content and caps it at half the chat height", () => {
    expect(resolveInlineSurfaceHeight(180, 640)).toBe(180)
    expect(resolveInlineSurfaceHeight(900, 640)).toBe(320)
  })

  it("seeds the proven owner authentication behaviors as approved Workspace stories", async () => {
    const user = userEvent.setup()
    const workspace = createSeedState().features.find((feature) => feature.id === "workspace")
    const authenticationStories = workspace?.stories.filter((story) => story.id.startsWith("owner-auth-")) ?? []

    expect(authenticationStories).toHaveLength(7)
    expect(authenticationStories.every((story) => story.status === "approved")).toBe(true)
    expect(authenticationStories.every((story) => story.userIntent.trim() && story.agentIntent.trim())).toBe(true)
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
    await user.click(screen.getByRole("button", { name: "Create an owner account" }))
    expect(screen.getByTitle("Mock surface: Create an owner account")).toHaveStyle({ colorScheme: "dark" })
    expect(screen.getByRole("button", { name: "Switch to light mode" })).toBeInTheDocument()
  })

  it("persists edits explicitly in local storage", async () => {
    const user = userEvent.setup()
    render(<App />)

    const story = screen.getByLabelText("User story")
    const userIntent = screen.getByLabelText("User intent")
    await user.clear(userIntent)
    await user.type(userIntent, "Understand where I am before choosing a next step.")
    await user.clear(story)
    await user.type(story, "As an owner, I want one clear next step.")

    const stored = localStorage.getItem(STORAGE_KEY)
    expect(stored).toContain("Understand where I am before choosing a next step.")
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

  it("migrates version 3 review text while separating actions from surfaces", () => {
    const current = createSeedState()
    localStorage.setItem(V3_STORAGE_KEY, JSON.stringify({
      version: 3,
      features: current.features.map((feature) => ({
        ...feature,
        stories: feature.stories.map(({ actions: _actions, ...story }) => story.id === "enter-workspace"
          ? { ...story, story: "My reviewed Workspace entry.", mockSurfacePath: "/mock-surfaces/workspace/enter-workspace.html" }
          : story),
      })),
    }))

    render(<App />)

    expect(screen.getByLabelText("User story")).toHaveValue("My reviewed Workspace entry.")
    expect(screen.getByText("No inline surface")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Create an agent" })).toBeInTheDocument()
    expect(localStorage.getItem(STORAGE_KEY)).toContain('"version":6')
  })

  it("migrates version 4 edits and adds intent guidance without discarding text", () => {
    const current = createSeedState()
    localStorage.setItem(V4_STORAGE_KEY, JSON.stringify({
      version: 4,
      features: current.features.map((feature) => ({
        ...feature,
        stories: feature.stories.map(({ userIntent: _userIntent, agentIntent: _agentIntent, ...story }) => story.id === "enter-workspace"
          ? { ...story, story: "My version 4 Workspace entry." }
          : story),
      })),
    }))

    render(<App />)

    expect(screen.getByLabelText("User story")).toHaveValue("My version 4 Workspace entry.")
    expect(screen.getByLabelText("User intent")).toHaveValue(
      "Return to my private Workspace and understand its current state.",
    )
    expect(screen.getByLabelText("Agent intent")).not.toHaveValue("")
    expect(localStorage.getItem(STORAGE_KEY)).toContain('"version":6')
  })

  it.each(["not-json", JSON.stringify({ version: 6, features: [] })])("shows a blocking recovery state for invalid saved data", (saved) => {
    localStorage.setItem(STORAGE_KEY, saved)
    render(<App />)

    const alert = screen.getByRole("alert")
    expect(within(alert).getByText("The saved workbench data is invalid.")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Reset local workspace" })).toBeInTheDocument()
  })
})
