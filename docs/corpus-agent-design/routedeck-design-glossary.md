# RouteDeck Design Glossary

Status: Shared vocabulary for Corpus design discussions. This is a glossary,
not a detailed product or implementation specification.

Canonical RouteDeck documentation: [RouteDeck Reference](../../../routedeck/docs/route-deck-reference.md)
in the sibling RouteDeck repository.

The definitions below follow the current RouteDeck contracts. Examples use the
Medusa reference application's Cart feature because it demonstrates local and
cross-feature operations, guarded external actions, projected surfaces, and
frontend affordances.

## RouteDeck vocabulary

| Term | Definition | Medusa Cart example |
| --- | --- | --- |
| **Application** | The compiled RouteDeck product: a name, one entry node, and a set of features. | `medusa-buyer` composes Catalog, Cart, Checkout, and Orders. |
| **Feature** | A unique product/code ownership namespace that contributes complete nodes and optional agent policies to an application. | The `cart` feature owns the `cart.summary` node and the declarations and implementations under `cart.*`. |
| **Node** | A durable product-facing location where RouteDeck declares the available context, legal operations, surfaces, policies, and outgoing transitions. It is not a LangGraph node. | `cart.summary` is the Cart workflow node at `/cart`. |
| **Node kind** | The node's product role: `workflow`, `section`, `detail`, or `transient`. | `cart.summary` is a `workflow` node. |
| **Navgraph** | The compiled product-interaction graph formed by nodes and exact operation/outcome transitions. It governs location and legal interaction state, not model orchestration. | `catalog.product -- cart.open/opened --> cart.summary -- checkout.start/started --> checkout.contact`. |
| **Route** | The canonical URL template assigned to a node, together with its deep-link policy. | `cart.summary` uses `/cart`. |
| **Deep-link policy** | Whether a route is independently `shareable` or requires an existing session and opaque resume capability as `session_bound`. | `/cart` is session-bound because it represents a particular current cart. |
| **Route entry** | A declared operation and outcome used to enter a parameterized route authoritatively. Route parameters bind exactly to operation inputs. | A product-detail route can resolve its product through an open-by-route operation rather than trusting the URL as application state. |
| **Operation** | A typed action RouteDeck may execute. It declares its input schema, safety and review requirements, outcomes, providers, guards, entity inputs, recovery metadata, and public metadata. | `cart.add_item` accepts an opaque `variant_ref` and a quantity. |
| **Outcome** | A named result explicitly declared by an operation. Outcomes drive transitions; they are not arbitrary handler messages. | `cart.add_item` declares `added`; `cart.open` declares `opened`. |
| **Transition** | One exact `operation + outcome -> target node` rule. The declaring node is the source. | From `cart.summary`, `checkout.start + started -> checkout.contact`. |
| **Outgoing transition** | A transition owned by its source node. It defines what can happen next from that location. | `cart.update_item + updated -> cart.summary` is outgoing from `cart.summary`. |
| **Incoming transition** | A transition into a node, derived by the compiler from other nodes' outgoing declarations. It is not authored separately. | The transition from `catalog.product` makes `cart.summary` an incoming target. |
| **Context provider** | A typed runtime loader for authoritative facts required by operations or guards. | `cart.current` refreshes the current cart before Cart actions run. |
| **Entity provider** | A provider that exposes the currently valid opaque entity handles an operation may reference. | `cart.items` exposes valid opaque line-item handles. |
| **Entity handle** | A public opaque reference to a private product entity. RouteDeck validates it and resolves the private identifier server-side. | The browser and model see `line_item_ref`, never the private Medusa line-item ID. |
| **Guard** | A typed allow/block decision evaluated from declared provider facts before an operation executes. | `cart.exists` blocks actions when no authoritative current cart exists. |
| **Capability** | A node-level grouping of related operations, surfaces, and agent policies for inspection and model context. It does not create another execution path. | `cart.manage` groups the Cart operations and Cart surfaces. |
| **Surface** | A declared unit of product UI with a component name, lifecycle, strict public-props schema, and operation-backed affordances. | `cart.summary` projects cart totals, line items, and Cart actions. |
| **Surface slot** | The semantic placement of a surface at a node: `active`, `frame`, `peer`, `detail`, `form`, `review`, `status`, `error`, or `diagnostic`. | The Cart node places `cart.summary` in its active and detail slots and declares separate error and diagnostic surfaces. |
| **Surface lifecycle** | Whether canonical surface state is stable across navigation or ephemeral to the current projection. | Cart summary state is stable; diagnostic state can be ephemeral. |
| **Affordance** | A semantic UI event mapped to an exact operation. Raw clicks or form events do not directly become application truth. | Cart's `remove` affordance dispatches `cart.remove_item`. |
| **Suggested action** | A product-authored action RouteDeck may present to an agent or user when its declared visibility conditions hold. | `View cart` suggests `cart.open` when a Cart entity is available. |
| **Policy** | A declared constraint on agent behavior, navigation, review, recovery, or another governed interaction concern. | The Cart node's navigation and recovery policies govern history and cart reconciliation behavior. |
| **Review** | A durable approval boundary required before an operation may proceed when its review policy demands it. | A consequential external write could require review before the handler executes. |
| **Recovery** | Explicit behavior for a known failure or uncertain external-write outcome. RouteDeck does not invent success or silently retry an uncertain write. | Cart creation declares reconciliation for an outcome-unknown create. |
| **Projection** | The default-deny public view of the current RouteDeck state: location, legal operations, surfaces, public props, opaque handles, and related public status. | At `cart.summary`, the client receives public cart props and only the Cart and Checkout operations legal there. |
| **Session** | The versioned canonical RouteDeck interaction state, containing both public projection state and private bindings/state. | A guest session retains the current Cart binding while exposing only its opaque handle. |
| **Binding** | The startup mapping from a declaration reference to exactly one typed runtime implementation. Missing, duplicate, or extra bindings fail startup. | Cart bindings connect `cart.add_item` to `AddCartItemHandler` and `cart.exists` to `CartExistsGuard`. |
| **Handler** | The implementation of an operation. It receives validated arguments and execution context, performs the product action, and returns a declared outcome plus observations and state effects. | `AddCartItemHandler` calls the Medusa Store API and returns the `added` outcome. |
| **Effect** | An explicit state change returned by a handler and committed through RouteDeck's supervised operation path. | A successful Cart mutation updates the canonical public Cart surface state. |
| **Agent driver** | The product-supplied model/orchestration integration that receives the current RouteDeck context and can invoke only currently legal operations. | A Medusa shopping agent may interpret “add this” and select the projected `cart.add_item` operation. |
| **Product intent** | The user's business meaning expressed in natural language. RouteDeck does not store a general intent contract; the product agent maps it to a currently legal operation. | “Take me to my basket” maps to `cart.open` when that operation is projected. |
| **Navigation intent** | One of RouteDeck's narrow navigation commands: `open_path`, `back`, `forward`, `cancel`, or `restore_history_entry`. | Browser Back sends `back`; it does not replay `cart.open`. |
| **Frontend surface registry** | Product-owned mapping from a declared surface component name to its React implementation. | The registry maps `cart.summary` to `CartSummarySurface`. |

## RouteDeck feature vocabulary

The word **feature** is used at two related levels:

- The **Feature contract** contributes a namespace, complete nodes, and optional
  agent policies to application composition.
- The **feature package** is the product-owned code boundary containing the
  declarations, implementations, bindings, surfaces, and validation associated
  with that namespace.

The compiler discovers the application's canonical operation, provider, guard,
capability, and surface catalogs by traversing the nodes contributed by all
features. A Feature contract is therefore not a standalone bag of every object
owned by the package.

### Vocabulary for constructing one feature

| Feature term | Definition | Medusa Cart example |
| --- | --- | --- |
| **Feature identity** | The unique namespace and product responsibility owned by the feature. | Namespace `cart`; responsibility: current-cart management. |
| **Feature boundary** | What meaning and implementation the feature owns, independent of every node where its operations may be exposed. | Cart owns `cart.add_item`; Catalog may expose it on a product node without taking ownership of its semantics. |
| **Declaration** | An immutable contract describing a provider, guard, operation, capability, surface reference, or related RouteDeck object before runtime code is attached. | `CART_ADD_ITEM` declares input, safety, outcome, providers, guards, and entity inputs. |
| **Feature operation set** | The actions semantically owned by the feature. This does not mean every action is legal at every feature node. | Cart owns create, add, open, update, and remove. |
| **Feature outcome set** | The named results produced by the feature's operations and consumed by node transitions. | `created`, `added`, `opened`, `updated`, and `removed`. |
| **Feature context** | The authoritative facts and entity allowlists needed to make the feature's operations safe and deterministic. | Buyer market, refreshed Cart state, current Cart binding, and current line items. |
| **Feature guards** | The preconditions that decide which feature operations can execute against the current context. | `cart.exists` and `cart.absent`. |
| **Feature node set** | The complete product locations contributed by the Feature contract. | Cart contributes `cart.summary`. |
| **Node operation set** | The subset of local or imported operations legal at one node. This is the effective action boundary seen by agents and surfaces. | `cart.summary` exposes open, update, remove, and the imported `checkout.start`; it does not expose create or add. |
| **Local transition** | An operation outcome that remains within the same feature, possibly at the same node. | `cart.update_item + updated -> cart.summary`. |
| **Cross-feature transition** | An operation outcome whose target belongs to another feature namespace. | `checkout.start + started -> checkout.contact`. |
| **Imported operation** | An operation declared and implemented by one feature but deliberately made legal by another feature's node. | Catalog's product node imports `cart.add_item`; Cart's summary node imports `checkout.start`. |
| **Feature surface set** | The product UI components and schemas owned by the feature package. | Cart frame, summary, status, error, and diagnostic surfaces. |
| **Feature affordance set** | The semantic events through which feature surfaces request legal operations. | Change quantity, remove item, and start checkout. |
| **Feature capability set** | Named node-level groupings that describe coherent combinations of operations, surfaces, and policies. | `cart.manage` and the Cart node's cross-feature checkout capability. |
| **Feature recovery contract** | The declared directives and failure surface for recoverable or uncertain feature states. | Refresh Cart and reconcile an unknown Cart creation result; otherwise show `cart.error`. |
| **Feature bindings** | The exact mapping from all feature-owned runtime references to handlers, providers, and guards. | `create_cart_bindings(client)` binds the Cart declarations to the Medusa client-backed implementations. |
| **Feature adapter boundary** | The narrow layer through which feature handlers communicate with an external product or service. | Cart handlers call the Medusa Store client rather than placing Medusa logic in RouteDeck. |
| **Feature projection** | The public state and currently legal actions emitted for the feature at the active node. | The Cart projection contains opaque Cart props and conditionally exposes Checkout only when its guards pass. |
| **Feature frontend** | The registered UI implementation that renders projected state and dispatches declared affordances without owning application truth. | `CartSummarySurface` renders Cart props and dispatches update, remove, and checkout affordances. |
| **Feature composition** | Selection of the feature alongside other independently authored features in the Application contract. | `MEDUSA_APP` composes Cart with Catalog, Checkout, and Orders. |
| **Feature proof** | Validation that declarations compile, all bindings exist, legal operations and transitions project correctly, private data stays private, and the real product path executes. | Medusa tests verify cross-feature Cart operations, strict Cart props, opaque IDs, and the real Cart flow. |

## Medusa Cart construction flow

```text
Cart declarations
  -> providers + entity providers
  -> guards
  -> operations + outcomes
  -> affordances + capabilities
  -> cart.summary node
       -> legal operation subset
       -> local and cross-feature transitions
       -> surface slots
       -> navigation and recovery policies
  -> exact runtime bindings
  -> Medusa-backed handlers
  -> public RouteDeck projection
  -> registered Cart React surface
  -> contract and end-to-end proof
```

A concrete Cart interaction follows this path:

```text
User says “add this product”
  -> product agent interprets the business intent
  -> current node projection permits cart.add_item
  -> RouteDeck validates variant_ref and quantity
  -> declared providers load current Cart and entity context
  -> cart.exists evaluates the authoritative context
  -> AddCartItemHandler resolves opaque handles server-side
  -> Medusa Store API performs the external action
  -> handler returns outcome added and explicit effects
  -> the source node's added transition selects the target
  -> RouteDeck commits and emits the next public projection
```

## Reusable feature-definition shorthand

When Corpus explores one proposed feature, the minimum shared vocabulary is:

```text
Feature
  = identity + boundary + nodes + policies

Node
  = route + context + legal operations + outgoing transitions
    + capabilities + surfaces + navigation + recovery

Operation
  = inputs + entity inputs + safety/review + providers + guards
    + outcomes + recovery metadata

Surface
  = component + lifecycle + public props + affordances

Runtime feature
  = declarations + exact bindings + handlers/adapters
    + projection/frontend registration + end-to-end proof
```

This shorthand describes the questions to answer during later feature design;
it does not pre-decide the concrete Corpus nodes, operations, or surfaces.

## Reference points

- Corpus launch feature index: [Corpus Agent Design Document](./corpus-agent-design-document.md)
- Corpus behavior baseline: [Feature Behavior Notes](./feature-behavior-notes.md)
- Canonical RouteDeck reference: sibling RouteDeck repository,
  `docs/route-deck-reference.md`
- Medusa Cart declarations and feature construction: sibling RouteDeck
  repository, `examples/medusa-agent/backend/medusa_agent/features/cart/`
- Medusa Cart frontend surface: sibling RouteDeck repository,
  `examples/medusa-agent/frontend/src/features/cart/`
