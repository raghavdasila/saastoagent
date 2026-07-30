export const STUDIO_CONFIG = {
  productName: "RouteDeck Agent Design Studio",
  projectName: "Corpus",
  exportLabel: "Export JSON",
  exportFilename: "corpus-agent-design.json",
  behaviorCollectionLabel: "Behaviors",
  featurePolicyLabel: "Feature policies",
  views: {
    behavior: {
      label: "Behavior",
      objectType: "Node",
    },
    featurePolicy: {
      label: "Feature AgentPolicies",
      description: "Guidance active throughout the feature. Narrower AgentPolicies remain inside the behavior Node.",
    },
  },
} as const
