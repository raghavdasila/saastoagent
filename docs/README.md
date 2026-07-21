# Corpus Documentation

This directory owns product meaning, verified behavior references, and design
artifacts. It does not own current source boundaries or session state.

- `corpus-product-definition.md` — locked product layout, not locked features.
- `corpus-behavior-reference.md` — verified legacy benchmark behavior.
- `corpus-routedeck-design-notebook.html` — mobile design discussion artifact
  and proposed RouteDeck Navgraph.

Run `python scripts/validate_design_notebook.py` after changing the notebook's
Navgraph adjacency or inline JavaScript.
