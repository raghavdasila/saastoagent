# Deployed Ecommerce Three-Mode Checkpoint

Corpus is live at `https://corpus.saastoagent.com` on `corpus-vm-1`
(`n2-standard-2`). Private Medusa 2.13.6 is live on `medusa-test-vm-1`
(`e2-micro`) at `10.138.0.2:9100`, reachable only from Corpus plus IAP SSH.

Final accepted runs:

- Surface `20260813T183912Z-76fa3a454a`: 39/39.
- Hybrid `20260813T191806Z-5249834ee9`: 40/40.
- Chat `20260813T193405Z-5f81fb0b5f`: 39/39.

Each has zero unexpected diagnostics, one continuous video, successful Corpus
restart recovery, and exactly one audited cart with one T-shirt quantity 1.
Capacity decision: retain both VM sizes. Corpus is sufficient for the internal
five-user target. Medusa Free Tier is sufficient for acceptance but remains a
marginal, non-SLA dependency.

Production backend/worker digest:
`sha256:50145616831f69ad3999b35589794897404565b4d789855ea486004deb6bf595`.
Detailed evidence is in
`docs/superpowers/validation/2026-08-13-deployed-ecommerce-three-mode.md` and
operations are in `docs/deployment/gcp-single-vm.md` plus
`docs/deployment/gcp-medusa-acceptance-vm.md`.

RouteDeck and user-owned behavior notes remain untouched. The next work is
normal product QA/monitoring, not another horizontal acceptance rerun.
