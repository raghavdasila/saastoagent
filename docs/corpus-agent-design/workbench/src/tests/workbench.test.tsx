import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { vi } from "vitest"

import App from "@/App"
import { createSeedState } from "@/workbench/seed"
import { resolveInlineSurfaceHeight } from "@/workbench/SurfacePreview"
import { getDesignStateFile, setDesignStateFile } from "@/tests/designStateFileMock"
import { THEME_STORAGE_KEY } from "@/workbench/theme"

async function renderWorkbench(): Promise<void> {
  render(<App />)
  await screen.findByRole("heading", { name: "RouteDeck Agent Design Studio" })
}

describe("RouteDeck Agent Design Studio", () => {
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
      "Enter Corpus before signing in.",
    )
    expect(screen.getByLabelText("Agent intent")).toHaveValue(
      "Establish the unauthenticated Lounge context and present Lounge home.",
    )
    expect(screen.getByLabelText("Expected behavior")).toBeInTheDocument()
  })

  it("keeps feature rules separate from narrower behavior design", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    expect(screen.getByRole("heading", { name: "Behavior rules" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Capabilities" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Surfaces" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Operations" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Suggested actions" })).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "Feature rules" }))
    expect(screen.getByRole("heading", { name: "Feature rules" })).toBeInTheDocument()
    expect(screen.getAllByLabelText(/^Lounge feature rule /)).toHaveLength(7)
    expect(screen.queryByRole("heading", { name: "Capabilities" })).not.toBeInTheDocument()
    expect(screen.queryByRole("heading", { name: "Operations" })).not.toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /^Arrive in the Lounge/ }))
    const operations = screen.getByRole("heading", { name: "Operations" }).closest("section")!
    await user.click(within(operations).getByRole("button", { name: "Add operation" }))
    const operationNames = within(operations).getAllByLabelText("Operation name")
    await user.clear(operationNames.at(-1)!)
    await user.type(operationNames.at(-1)!, "Open Lounge account path")

    await waitFor(() => expect(getDesignStateFile()).toContain("Open Lounge account path"))
    expect(getDesignStateFile()).toContain('"nodePolicies"')
    expect(getDesignStateFile()).toContain('"operations"')
    expect(getDesignStateFile()).toContain('"suggestedActions"')
    expect(getDesignStateFile()).not.toContain('"policyNodes"')
  })

  it("authors and autosaves feature guidance separately from rules", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Feature guidance" }))
    expect(screen.getByRole("heading", { name: "Feature guidance" })).toBeInTheDocument()
    const prompt = screen.getByLabelText("Lounge feature guidance")
    expect((prompt as HTMLTextAreaElement).value).toContain("public Lounge")

    await user.clear(prompt)
    await user.type(prompt, "You are Corpus in the reviewed Lounge feature.")

    await waitFor(() => expect(getDesignStateFile()).toContain("reviewed Lounge feature"))
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
    expect(lounge.stories.every((story) => story.status === "draft")).toBe(true)
    expect(lounge.policies).toContain(
      "While Lounge is active, identify the product location as Lounge and keep private Workspace and feature navigation hidden until authenticated entry succeeds.",
    )
    expect(lounge.policies).toContain(
      "Describe Lounge choices in user-facing product language and never expose internal operation, tool, Node, AgentPolicy, or identifier names.",
    )
    expect(lounge.policies).toContain(
      "When a visitor starts describing work they want Corpus to perform, explain that work requires a private Workspace and ask them to sign in or sign up.",
    )
    expect(lounge.stories[1]?.suggestedActions.map((action) => action.label)).toEqual(["Sign in", "Sign up"])
    expect(lounge.stories[0]?.surfaces[0]?.policies).toContain(
      "Identify the active product location as Lounge and show only Lounge-scoped navigation; keep private Workspace and feature navigation hidden until authenticated entry succeeds.",
    )

    await renderWorkbench()
    const featureNavigation = screen.getByRole("navigation", { name: "Features" })
    expect(screen.getByText("Features")).toBeInTheDocument()
    expect(screen.queryByText("Project structure")).not.toBeInTheDocument()
    expect(featureNavigation.querySelectorAll("svg")).toHaveLength(0)
    expect(screen.getByRole("button", { name: "Lounge 8" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Workspace 6" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Agents 9" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Source Hub 5" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "API Source 9" })).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: /^Ask Lounge for product help/ }))
    expect((screen.getByLabelText("Expected behavior") as HTMLTextAreaElement).value).toContain(
      "Corpus answers only about the product from current knowledge",
    )
  })

  it("adds, selects, and autosaves a blank behavior to design-state.json", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Add behavior" }))

    expect(screen.getByRole("heading", { name: "New behavior" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Lounge 9" })).toBeInTheDocument()
    await waitFor(() => expect(getDesignStateFile()).toContain("New behavior"))
    expect(screen.getByRole("status", { name: "Saved" })).toBeInTheDocument()
  })

  it("blocks approval and explains completeness issues for an unfinished behavior", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: "Add behavior" }))
    expect(screen.getByRole("button", { name: "Approve behavior" })).toBeDisabled()
    expect(screen.getByText("Resolve 3 blocking issues before approval.")).toBeInTheDocument()

    await user.click(screen.getByRole("tab", { name: /^Completeness/ }))
    expect(screen.getByRole("heading", { name: "3 blocking issues" })).toBeInTheDocument()
    expect(screen.getByText("Describe the user intent.")).toBeInTheDocument()
    expect(screen.getByText("Describe the outcome Corpus is responsible for.")).toBeInTheDocument()
    expect(screen.getByText("Describe the observable behavior and completion state.")).toBeInTheDocument()
  })

  it("opens one focused Operation contract from the compact inventory", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(within(screen.getByRole("list", { name: "Operations" })).getByRole("button", { name: /Start product help/ }))
    const drawer = screen.getByRole("dialog", { name: "Start product help" })
    expect(within(drawer).getByLabelText("Inputs and prerequisites")).not.toHaveValue("")
    expect(within(drawer).getByLabelText("Observable outcomes")).not.toHaveValue("")
    expect(within(drawer).getByLabelText("Safety and review")).not.toHaveValue("")
    expect(within(drawer).getByLabelText("Failure and recovery")).not.toHaveValue("")

    await user.click(within(drawer).getByRole("button", { name: "Done" }))
    expect(screen.queryByRole("dialog", { name: "Start product help" })).not.toBeInTheDocument()
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

    expect(screen.getByRole("button", { name: "Approve behavior" })).toBeEnabled()
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
    expect(screen.getAllByText("Rejected")).not.toHaveLength(0)
  })

  it("keeps Lounge arrival limited to public entry operations and its surface", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    expect(screen.getByRole("heading", { name: "Surface preview" })).toBeInTheDocument()
    expect(screen.getByTitle("Mock surface: Arrive in the Lounge")).toHaveAttribute("src", "/mock-surfaces/lounge/home.html")
    expect(screen.getByRole("list", { name: "Operations" })).toHaveTextContent("Start product help")
    expect(screen.getByRole("list", { name: "Operations" })).toHaveTextContent("Open owner registration")
    expect(screen.getByRole("list", { name: "Operations" })).toHaveTextContent("Open owner sign-in")
    expect(screen.getByRole("list", { name: "Operations" })).not.toHaveTextContent("Open password reset link")
    expect(screen.getByRole("list", { name: "Operations" })).not.toHaveTextContent("Open email verification link")
    await user.click(screen.getByRole("tab", { name: "Chat" }))
    const chatPath = screen.getByRole("heading", { name: "Chat preview" }).closest("section")!
    expect(within(chatPath).queryByLabelText("Suggested actions")).not.toBeInTheDocument()
  })

  it("defines every Operation by its intended product effect", () => {
    const stories = createSeedState().features.flatMap((feature) => feature.stories)

    for (const story of stories) {
      expect(new Set(story.operations.map((operation) => operation.name)).size).toBe(story.operations.length)
      for (const operation of story.operations) {
        expect(operation.purpose).not.toMatch(/^(Perform|Support)\b/)
        expect(operation.purpose.length).toBeGreaterThan(40)
      }
      for (const action of story.suggestedActions) {
        expect(story.operations.some((operation) => operation.name === action.operationName)).toBe(true)
      }
    }
  })

  it("renders an authentication surface with only height-reporting scripts allowed", async () => {
    const user = userEvent.setup()
    await renderWorkbench()

    await user.click(screen.getByRole("button", { name: /^Create an owner account/ }))
    const frame = screen.getByTitle("Mock surface: Create an owner account")
    expect(frame).toHaveAttribute("src", "/mock-surfaces/workspace/authentication.html#register")
    expect(frame).toHaveAttribute("sandbox", "allow-scripts")
  })

  it("grows a surface to its content and caps it at half the chat height", () => {
    expect(resolveInlineSurfaceHeight(180, 640)).toBe(180)
    expect(resolveInlineSurfaceHeight(900, 640)).toBe(320)
  })

  it("keeps materially revised Lounge authentication in draft review and sign-out in Workspace", async () => {
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!
    const workspace = createSeedState().features.find((feature) => feature.id === "workspace")!
    const loungeAuthentication = lounge.stories.filter((story) => story.id.startsWith("owner-auth-"))

    expect(loungeAuthentication).toHaveLength(6)
    expect(loungeAuthentication.every((story) => story.status === "draft")).toBe(true)
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

  it("exports the current Corpus design state as JSON", async () => {
    const user = userEvent.setup()
    const createObjectUrl = vi.fn((_blob: Blob) => "blob:corpus-design")
    const revokeObjectUrl = vi.fn()
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: createObjectUrl })
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: revokeObjectUrl })
    let downloadedAs = ""
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      downloadedAs = this.download
    })

    await renderWorkbench()
    await user.click(screen.getByRole("button", { name: "Export JSON" }))

    expect(createObjectUrl).toHaveBeenCalledOnce()
    expect(createObjectUrl.mock.calls[0][0]).toBeInstanceOf(Blob)
    expect(downloadedAs).toBe("corpus-agent-design.json")
    click.mockRestore()
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
    setDesignStateFile(JSON.stringify({ features: [] }))
    render(<App />)

    const alert = await screen.findByRole("alert")
    expect(within(alert).getByText("The saved studio data is invalid.")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Replace file with seed" }))
    await screen.findByRole("heading", { name: "RouteDeck Agent Design Studio" })
    expect(getDesignStateFile()).toContain("lounge-arrival")
  })
})
