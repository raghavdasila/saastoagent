import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import App from "@/App"
import { createSeedState } from "@/workbench/seed"
import { resolveInlineSurfaceHeight } from "@/workbench/SurfacePreview"
import { getDesignStateFile, setDesignStateFile } from "@/tests/designStateFileMock"
import { THEME_STORAGE_KEY } from "@/workbench/theme"

async function renderWorkbench(): Promise<void> {
  render(<App />)
  await screen.findByRole("heading", { name: "Corpus agent design" })
}

describe("Corpus behavior design workbench", () => {
  it("switches across the behavior sections 0-4", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    expect(screen.getByRole("heading", { name: "Arrive in the Lounge" })).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: /Agents/ }))
    expect(screen.getByRole("heading", { name: "View agents" })).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: /API Source/ }))
    expect(screen.getByRole("heading", { name: "Upload an API YAML file" })).toBeInTheDocument()
  })

  it("keeps user and agent intent distinct from the user story", async () => {
    await renderWorkbench()

    expect(screen.getByLabelText("User intent")).toHaveValue(
      "Understand where I am and what I can do before signing in.",
    )
    expect(screen.getByLabelText("Agent intent")).toHaveValue(
      "Establish the public Lounge and keep every valid public or account path available.",
    )
    expect(screen.getByLabelText("User story")).toBeInTheDocument()
  })

  it("seeds Lounge as a separate unauthenticated feature with account paths and product help", async () => {
    const user = userEvent.setup()
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!

    expect(lounge.stories.map((story) => story.id)).toEqual([
      "lounge-arrival",
      "lounge-product-help",
      "owner-auth-register",
      "owner-auth-sign-in",
      "owner-auth-request-reset",
      "owner-auth-confirm-reset",
      "owner-auth-request-verification",
      "owner-auth-confirm-verification",
    ])
    expect(lounge.stories.slice(0, 2).every((story) => story.status === "draft")).toBe(true)
    expect(lounge.stories.slice(2).every((story) => story.status === "approved")).toBe(true)

    await renderWorkbench()
    expect(screen.getByRole("button", { name: "Lounge 8" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Workspace 6" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Agents 9" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Source Hub 5" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "API Source 9" })).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Ask Lounge for product help" }))
    expect((screen.getByLabelText("User story") as HTMLTextAreaElement).value).toContain(
      "Corpus answers from current product knowledge",
    )
  })

  it("adds, selects, and autosaves a blank story to design-state.json", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Add story" }))

    expect(screen.getByRole("heading", { name: "New user story" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Lounge 9" })).toBeInTheDocument()
    await waitFor(() => expect(getDesignStateFile()).toContain("New user story"))
    expect(screen.getByText("Saved to file")).toBeInTheDocument()
  })

  it("deletes a draft story only after confirmation and autosaves the deletion", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Add story" }))
    await user.click(screen.getByRole("button", { name: "Delete story" }))
    await user.click(screen.getByRole("button", { name: "Confirm delete story" }))

    expect(screen.queryByRole("heading", { name: "New user story" })).not.toBeInTheDocument()
    await waitFor(() => expect(getDesignStateFile()).not.toContain("New user story"))
  })

  it("returns a reviewed story to draft when it is reopened and edited", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Approve story" }))
    await user.click(screen.getByRole("button", { name: "Reopen draft" }))
    await user.clear(screen.getByLabelText("User story"))
    await user.type(screen.getByLabelText("User story"), "The Lounge remains the guest starting point.")

    expect(screen.getByText("Draft")).toBeInTheDocument()
  })

  it("requires and records a rejection reason", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Reject story" }))
    await user.click(screen.getByRole("button", { name: "Confirm rejection" }))
    expect(screen.getByRole("alert")).toHaveTextContent("Add a reason before rejecting")

    await user.type(screen.getByLabelText("Why reject this story?"), "The entry point is unclear.")
    await user.click(screen.getByRole("button", { name: "Confirm rejection" }))
    expect(screen.getByText("Rejected")).toBeInTheDocument()
  })

  it("keeps Lounge account actions separate from inline surfaces", async () => {
    await renderWorkbench()

    expect(screen.getByRole("heading", { name: "Surface path" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Chat path" })).toBeInTheDocument()
    expect(screen.getByText("No surface path designed for this behavior.")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Ask about Corpus" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Sign up" })).toBeInTheDocument()
    expect(screen.getAllByRole("button", { name: "Sign in" })).toHaveLength(2)
    expect(screen.getByRole("button", { name: "Forgot password" })).toBeInTheDocument()
  })

  it("renders an authentication surface with only height-reporting scripts allowed", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Create an owner account" }))
    const frame = screen.getByTitle("Mock surface: Create an owner account")
    expect(frame).toHaveAttribute("src", "/mock-surfaces/workspace/authentication.html#register")
    expect(frame).toHaveAttribute("sandbox", "allow-scripts")
  })

  it("grows a surface to its content and caps it at half the chat height", () => {
    expect(resolveInlineSurfaceHeight(180, 640)).toBe(180)
    expect(resolveInlineSurfaceHeight(900, 640)).toBe(320)
  })

  it("places proven entry authentication in Lounge and sign-out in Workspace", async () => {
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!
    const workspace = createSeedState().features.find((feature) => feature.id === "workspace")!
    const loungeAuthentication = lounge.stories.filter((story) => story.id.startsWith("owner-auth-"))

    expect(loungeAuthentication).toHaveLength(6)
    expect(loungeAuthentication.every((story) => story.status === "approved")).toBe(true)
    expect(workspace.stories.find((story) => story.id === "owner-auth-sign-out")?.status).toBe("approved")

    await renderWorkbench()
    expect(screen.getByRole("button", { name: "Workspace 6" })).toBeInTheDocument()
  })

  it("creates agents without a product-level draft-agent concept", () => {
    const agents = createSeedState().features.find((feature) => feature.id === "agents")!
    const serializedAgents = JSON.stringify(agents).toLowerCase()

    expect(agents.stories).toHaveLength(9)
    expect(agents.stories.map((item) => item.id)).toContain("agents-create")
    expect(serializedAgents).not.toContain("draft agent")
    expect(serializedAgents).not.toContain("agent draft")
  })

  it("persists slate dark mode as a browser-only preference", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Switch to dark mode" }))
    expect(document.documentElement).toHaveClass("dark")
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark")
  })

  it("autosaves story edits to design-state.json", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.clear(screen.getByLabelText("User intent"))
    await user.type(screen.getByLabelText("User intent"), "Understand the guest starting point.")

    await waitFor(() => expect(getDesignStateFile()).toContain("Understand the guest starting point."))
    expect(localStorage.getItem("corpus.feature-design-workbench.v7")).toBeNull()
  })

  it("blocks on an invalid design-state.json and can explicitly replace it with the seed", async () => {
    const user = userEvent.setup()
    setDesignStateFile(JSON.stringify({ version: 10, features: [] }))
    render(<App />)

    const alert = await screen.findByRole("alert")
    expect(within(alert).getByText("The saved workbench data is invalid.")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Replace file with seed" }))
    await screen.findByRole("heading", { name: "Corpus agent design" })
    expect(getDesignStateFile()).toContain("lounge-arrival")
  })
})
