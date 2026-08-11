export interface CorpusLocationPresentation {
  feature: string;
  title: string;
  description: string;
}

const LOCATIONS: Readonly<Record<string, CorpusLocationPresentation>> = Object.freeze({
  lounge: { feature: "Lounge", title: "Corpus Lounge", description: "Ask about Corpus or choose an account path when you are ready." },
  workspace: { feature: "Workspace", title: "Corpus Workspace", description: "Ask Corpus what to explore, design, connect, or operate." },
  agents: { feature: "Agents", title: "Corpus Agents", description: "Create an Agent, manage its Sources, and continue its exact lifecycle." },
  sources: { feature: "Sources", title: "Corpus Sources", description: "Connect, inspect, and prepare the Sources available to your Workspace." },
  designer: { feature: "Designer", title: "Agent Designer", description: "Review the proposed behavior, tools, policies, surfaces, and RouteDeck NavGraph." },
  builder: { feature: "Builder", title: "Agent Builder", description: "Provision and control immutable Agent builds from an accepted design." },
  sandbox: { feature: "Sandbox", title: "Agent Sandbox", description: "Run the exact draft Agent and inspect its owner-only routing and execution evidence." },
  evaluation: { feature: "Evaluation", title: "Agent Evaluation", description: "Generate, manage, and run evaluation coverage for one exact Agent build." },
  channels: { feature: "Channels", title: "Channels and Deployment", description: "Publish an eligible build, manage availability, and inspect deployment history." },
  operations: { feature: "Operations", title: "Agent Operations", description: "Inspect deployed interactions and promote exact evidence into future evaluation." },
});

export function corpusLocation(nodeId: string | null): CorpusLocationPresentation {
  const prefix = nodeId?.split(".", 1)[0] ?? "workspace";
  return LOCATIONS[prefix] ?? LOCATIONS.workspace!;
}

