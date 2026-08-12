# Shared ToolRouter semantic-graph visualizer

This integration is the maintained Corpus boundary for the already-proven
ToolRouter and Source Hub graph UI. Product features provide an immutable graph
DTO; this package owns the renderer, layout worker, construction replay, graph
inspection, and pinned visualization dependencies.

Reference implementation:

- checkout: `D:\Dev\AI Projects\source-hub-runtime`
- commit: `114fa4d4bfbda71d891aae01b8a82ba09705004f`
- component SHA-256: `99818f9869391ac5e634adf6e21fc2aeaa3a0708c49675925560b29ac0ea91dd`
- worker SHA-256: `fc0a2f163f3eed5cc31f3fc5b1490e65d8d6f5aad67787593ae4ae0ff4a3b057`
- architecture: Sigma 3.0.3 + Graphology 0.26.0 + worker ForceAtlas2 for
  the complete accumulated graph; Cytoscape 3.33.1 for one operation's exact
  neighborhood.

The Corpus renderer retains those two renderer modes, semantic zoom, typed
styling, off-main-thread layout, fit/full-screen controls and node/edge
inspection. It additionally consumes the immutable ToolRouter construction
trace so users can pause, step, seek and replay the complete recorded build.
This is recorded playback of completed processing, not a claim of live graph
mutation.

Reference baseline rechecked locally on 2026-08-11:

```powershell
cd D:\Dev\AI Projects\source-hub-runtime\frontend
node -e "import('cytoscape').then(({default:c})=>{const x=c({headless:true,elements:[{data:{id:'a'}}]});if(x.nodes().length!==1)process.exit(1)})"
```

No Source feature may implement a second graph renderer. Source-specific
identity, semantic groups and RouteDeck stage selection remain in the Source
adapter/panel; rendering and replay remain here.
