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

  it("keeps user and agent intent distinct from expected behavior", async () => {
    await renderWorkbench()

    expect(screen.getByLabelText("User intent")).toHaveValue(
      "Understand where I am and what I can do before signing in.",
    )
    expect(screen.getByLabelText("Agent intent")).toHaveValue(
      "Establish the public Lounge and keep every valid public or account path available.",
    )
    expect(screen.getByLabelText("Expected behavior")).toBeInTheDocument()
  })

  it("keeps feature policy in the sidebar and behavior policy with the selected behavior", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    expect(screen.getByText("Behavior policies (0)")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Feature policy" }))
    expect(screen.getByRole("heading", { name: "Feature AgentPolicy" })).toBeInTheDocument()
    expect(screen.getAllByLabelText("Policy guidance")).toHaveLength(2)

    await user.click(screen.getByRole("button", { name: "Arrive in the Lounge" }))

    await user.click(screen.getByRole("button", { name: "Add policy" }))
    const scopes = screen.getAllByLabelText("Scope")
    const scopeNames = screen.getAllByLabelText("Applies to")
    const guidance = screen.getAllByLabelText("Policy guidance")

    await user.selectOptions(scopes.at(-1)!, "behavior")
    expect(scopeNames.at(-1)).toHaveValue("Arrive in the Lounge")
    await user.type(guidance.at(-1)!, "Keep this behavior available to unauthenticated visitors.")

    expect(screen.getByText("Behavior policies (1)")).toBeInTheDocument()
    await waitFor(() => expect(getDesignStateFile()).toContain("Keep this behavior available to unauthenticated visitors."))
    expect(getDesignStateFile()).not.toContain("lounge.home")
    expect(getDesignStateFile()).not.toContain("routedeck.execution_authority")

    await user.click(screen.getByRole("button", { name: "Remove policy 1" }))
    expect(screen.getByText("Behavior policies (0)")).toBeInTheDocument()
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
    expect((screen.getByLabelText("Expected behavior") as HTMLTextAreaElement).value).toContain(
      "Corpus answers from current product knowledge",
    )
  })

  it("adds, selects, and autosaves a blank behavior to design-state.json", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Add behavior" }))

    expect(screen.getByRole("heading", { name: "New behavior" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Lounge 9" })).toBeInTheDocument()
    await waitFor(() => expect(getDesignStateFile()).toContain("New behavior"))
    expect(screen.getByText("Saved to file")).toBeInTheDocument()
  })

  it("deletes a draft behavior only after confirmation and autosaves the deletion", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Add behavior" }))
    await user.click(screen.getByRole("button", { name: "Delete behavior" }))
    await user.click(screen.getByRole("button", { name: "Confirm delete behavior" }))

    expect(screen.queryByRole("heading", { name: "New behavior" })).not.toBeInTheDocument()
    await waitFor(() => expect(getDesignStateFile()).not.toContain("New behavior"))
  })

  it("returns a reviewed behavior to draft when it is reopened and edited", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Approve behavior" }))
    await user.click(screen.getByRole("button", { name: "Reopen draft" }))
    await user.clear(screen.getByLabelText("Expected behavior"))
    await user.type(screen.getByLabelText("Expected behavior"), "The Lounge remains the guest starting point.")

    expect(screen.getByText("Draft")).toBeInTheDocument()
  })

  it("requires and records a rejection reason", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Reject behavior" }))
    await user.click(screen.getByRole("button", { name: "Confirm rejection" }))
    expect(screen.getByRole("alert")).toHaveTextContent("Add a reason before rejecting")

    await user.type(screen.getByLabelText("Why reject this behavior?"), "The entry point is unclear.")
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

  it("autosaves behavior edits to design-state.json", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.clear(screen.getByLabelText("User intent"))
    await user.type(screen.getByLabelText("User intent"), "Understand the guest starting point.")

    await waitFor(() => expect(getDesignStateFile()).toContain("Understand the guest starting point."))
    expect(localStorage.getItem("corpus.feature-design-workbench.v7")).toBeNull()
  })

  it("blocks on an invalid design-state.json and can explicitly replace it with the seed", async () => {
    const user = userEvent.setup()
    setDesignStateFile(JSON.stringify({ version: 13, features: [] }))
    render(<App />)

    const alert = await screen.findByRole("alert")
    expect(within(alert).getByText("The saved workbench data is invalid.")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Replace file with seed" }))
    await screen.findByRole("heading", { name: "Corpus agent design" })
    expect(getDesignStateFile()).toContain("lounge-arrival")
  })
})
