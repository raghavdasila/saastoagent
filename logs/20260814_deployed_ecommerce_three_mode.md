# 2026-08-14 Deployed Ecommerce Three-Mode Log

- Provisioned and proved private Medusa 2.13.6 on Free Tier `e2-micro`.
- Backed up Corpus, wired the single private API destination, and retained
  OpenAI `gpt-5.6-luna` with protected credentials.
- Corrected the OpenAI strict-schema incompatibility and duplicate operation
  candidate clarification; deployed backend digest `sha256:501456...bf595`.
- Passed deployed Surface 39/39, Hybrid 40/40, and Chat 39/39 with one audited
  Medusa cart each and continuous normal-speed videos.
- Measured both VMs throughout. No OOM, Corpus swap, sustained saturation, or
  hardware-attributable product failure occurred. No resize was performed.
- RouteDeck was inspected read-only and not changed. No Git push was made.
