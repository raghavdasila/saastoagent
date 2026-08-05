export const STUDIO_CONFIG = {
  productName: "RouteDeck Agent Design Studio",
  projectName: "Corpus",
  exportLabel: "Export JSON",
  exportFilename: "corpus-agent-design.json",
  behaviorCollectionLabel: "Behaviors",
  featurePromptLabel: "Feature guidance",
  featurePolicyLabel: "Feature rules",
  views: {
    behavior: {
      label: "Behavior",
      objectType: "Product behavior",
    },
    featurePrompt: {
      label: "Feature guidance",
      description: "Product-authored role, purpose, vocabulary, and interaction posture active throughout this feature.",
    },
    featurePolicy: {
      label: "Feature rules",
      description: "Constraints active throughout the feature. Behavior, Capability, Surface, and Operation rules remain with their owning design.",
    },
  },
} as const
