export const STUDIO_CONFIG = {
  productName: "RouteDeck Agent Design Studio",
  projectName: "Corpus",
  exportLabel: "Export JSON",
  exportFilename: "corpus-agent-design.json",
  behaviorCollectionLabel: "Behaviors",
  featurePromptLabel: "Feature prompt",
  featurePolicyLabel: "Feature policies",
  views: {
    behavior: {
      label: "Behavior",
      objectType: "Node",
    },
    featurePrompt: {
      label: "Feature prompt",
      description: "Product-authored instructions active whenever RouteDeck resolves this feature from the current Node.",
    },
    featurePolicy: {
      label: "Feature AgentPolicies",
      description: "Guidance active throughout the feature. Narrower AgentPolicies remain inside the behavior Node.",
    },
  },
} as const
