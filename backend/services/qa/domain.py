from __future__ import annotations

QA_DOMAIN_MODEL = {
    "name": "SaaStoAgent entry navigation QA",
    "description": "UI-driven behavioral QA for entry, auth, SaaSAgent setup, and RouteDeck navigation.",
    "capabilities": [
        {
            "id": "entry_question",
            "name": "Ask platform questions",
            "expected_user_behaviors": ["ask general questions", "stay anonymous", "avoid forced auth"],
            "evidence_gates": ["assistant_response", "message_not_contains", "route_deck_snapshot_present"],
        },
        {
            "id": "auth_navigation",
            "name": "Auth navigation recovery",
            "expected_user_behaviors": ["start signin", "cancel", "switch modes", "recover from invalid input"],
            "evidence_gates": ["route_deck_current_node", "action_enabled", "message_not_contains"],
        },
        {
            "id": "SaaSAgent_setup",
            "name": "SaaSAgent setup navigation",
            "expected_user_behaviors": ["complete signup", "describe SaaSAgent", "back or cancel setup"],
            "evidence_gates": ["route_deck_current_node", "action_enabled", "assistant_response"],
        },
        {
            "id": "routedeck_map",
            "name": "RouteDeck debugger",
            "expected_user_behaviors": ["open map", "pan graph", "zoom graph", "inspect nodes"],
            "evidence_gates": ["route_deck_snapshot_present", "visible_text", "no_console_errors"],
        },
        {
            "id": "connection_setup",
            "name": "REST connection setup",
            "expected_user_behaviors": [
                "open Connections",
                "preview OpenAPI schema",
                "activate catalog",
                "recover from validation feedback",
            ],
            "evidence_gates": [
                "saas_agent_view",
                "visible_text",
                "api_response_ok",
                "catalog_count_at_least",
                "no_console_errors",
            ],
        },
        {
            "id": "catalog_inspection",
            "name": "Generated catalog inspection",
            "expected_user_behaviors": ["open Actions", "open Entities", "inspect generated tools"],
            "evidence_gates": ["saas_agent_view", "visible_text", "catalog_count_at_least", "no_console_errors"],
        },
        {
            "id": "rest_execution",
            "name": "REST operator execution",
            "expected_user_behaviors": [
                "ask for a read-safe API task",
                "inspect tool trace",
                "hit approval guard for writes",
            ],
            "evidence_gates": ["assistant_response", "tool_called", "visible_text", "message_not_contains"],
        },
    ],
}


QA_SCENARIOS = [
    {
        "id": "first_load_contract",
        "name": "First load does not fall into email validation",
        "persona": "New visitor who has not decided whether to sign in.",
        "opening_message": "",
        "context": "The app should greet or offer intent choices on first load.",
        "pass_criteria": "No email-validation error appears before the user starts auth.",
        "max_turns": 4,
        "milestones": [
            {
                "id": "first-load-visible",
                "capability": "entry_question",
                "goal": "Inspect the initial visible state.",
                "actions": [{"action": "collect_evidence", "params": {}}],
                "evidence_gates": [
                    {"gate": "route_deck_snapshot_present", "required": True, "params": {}},
                    {
                        "gate": "message_not_contains",
                        "required": True,
                        "params": {"text": "That doesn't look like a valid email address"},
                    },
                ],
            }
        ],
    },
    {
        "id": "general_question",
        "name": "Ask a platform question without forced auth",
        "persona": "Evaluator asking what the product can do.",
        "opening_message": "What can you do here?",
        "context": "Anonymous users can ask questions before choosing auth.",
        "pass_criteria": "The assistant responds and does not force the user into email collection.",
        "max_turns": 6,
        "milestones": [
            {
                "id": "ask-question",
                "capability": "entry_question",
                "goal": "Send a normal product question through the visible composer.",
                "actions": [
                    {"action": "type_composer", "params": {"text": "What can you do here?"}},
                    {"action": "click_send", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "assistant_response", "required": True, "params": {}},
                    {"gate": "message_not_contains", "required": True, "params": {"text": "valid email address"}},
                ],
            }
        ],
    },
    {
        "id": "signin_cancel_signup",
        "name": "Start signin, cancel, then start signup",
        "persona": "User who changes their mind mid-auth.",
        "opening_message": "",
        "context": "Auth nodes must expose cancel and return to general intent.",
        "pass_criteria": "Cancel exits signin and signup can be started afterward.",
        "max_turns": 8,
        "milestones": [
            {
                "id": "start-signin",
                "capability": "auth_navigation",
                "goal": "Start signin from a visible action.",
                "actions": [{"action": "click_action", "params": {"action_id": "intent.sign_in"}}],
                "evidence_gates": [
                    {"gate": "route_deck_current_node", "required": True, "params": {"node": "email"}},
                    {"gate": "action_enabled", "required": True, "params": {"action_id": "nav.cancel"}},
                ],
            },
            {
                "id": "cancel-signin",
                "capability": "auth_navigation",
                "goal": "Cancel signin and return to intent.",
                "actions": [{"action": "click_action", "params": {"action_id": "nav.cancel"}}],
                "evidence_gates": [
                    {"gate": "route_deck_current_node", "required": True, "params": {"node": "intent"}},
                    {"gate": "action_enabled", "required": True, "params": {"action_id": "intent.register"}},
                ],
            },
            {
                "id": "start-signup",
                "capability": "auth_navigation",
                "goal": "Start signup after cancel.",
                "actions": [{"action": "click_action", "params": {"action_id": "intent.register"}}],
                "evidence_gates": [
                    {"gate": "route_deck_current_node", "required": True, "params": {"node": "display_name"}},
                    {"gate": "action_enabled", "required": True, "params": {"action_id": "nav.cancel"}},
                ],
            },
        ],
    },
    {
        "id": "auth_mode_switches",
        "name": "Switch between signin and signup",
        "persona": "User who chooses the wrong auth mode first.",
        "opening_message": "",
        "context": "Users should not be trapped inside a chosen auth mode.",
        "pass_criteria": "Signin can switch to signup and signup can switch back to signin.",
        "max_turns": 10,
        "milestones": [
            {
                "id": "signin-to-signup",
                "capability": "auth_navigation",
                "goal": "Start signin, then switch to signup.",
                "actions": [
                    {"action": "click_action", "params": {"action_id": "nav.cancel", "optional": True}},
                    {"action": "click_action", "params": {"action_id": "intent.sign_in"}},
                    {"action": "click_action", "params": {"action_id": "intent.register"}},
                ],
                "evidence_gates": [
                    {"gate": "route_deck_current_node", "required": True, "params": {"node": "display_name"}},
                    {"gate": "action_enabled", "required": True, "params": {"action_id": "intent.sign_in"}},
                ],
            },
            {
                "id": "signup-to-signin",
                "capability": "auth_navigation",
                "goal": "Switch from signup back to signin.",
                "actions": [{"action": "click_action", "params": {"action_id": "intent.sign_in"}}],
                "evidence_gates": [
                    {"gate": "route_deck_current_node", "required": True, "params": {"node": "email"}},
                    {"gate": "action_enabled", "required": True, "params": {"action_id": "intent.register"}},
                ],
            },
        ],
    },
    {
        "id": "invalid_email_recovery",
        "name": "Invalid email keeps recovery controls",
        "persona": "User mistypes an email address.",
        "opening_message": "",
        "context": "Validation errors must not remove back/cancel/switch controls.",
        "pass_criteria": "Invalid email shows validation copy while keeping recovery actions.",
        "max_turns": 8,
        "milestones": [
            {
                "id": "bad-email",
                "capability": "auth_navigation",
                "goal": "Submit an invalid email in signin.",
                "actions": [
                    {"action": "click_action", "params": {"action_id": "nav.cancel", "optional": True}},
                    {"action": "click_action", "params": {"action_id": "intent.sign_in"}},
                    {"action": "type_composer", "params": {"text": "not-an-email"}},
                    {"action": "click_send", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "route_deck_current_node", "required": True, "params": {"node": "email"}},
                    {"gate": "visible_text", "required": True, "params": {"text": "valid email address"}},
                    {"gate": "action_enabled", "required": True, "params": {"action_id": "nav.cancel"}},
                    {"gate": "action_enabled", "required": True, "params": {"action_id": "nav.back"}},
                ],
            }
        ],
    },
    {
        "id": "signup_SaaSAgent_path",
        "name": "Signup reaches SaaSAgent setup",
        "persona": "New user creating a SaaSAgent.",
        "opening_message": "",
        "context": "Signup should continue into SaaSAgent creation without dead ends.",
        "pass_criteria": "The flow reaches SaaSAgent setup, SaaSAgent confirm, or operator ready.",
        "max_turns": 14,
        "milestones": [
            {
                "id": "complete-signup",
                "capability": "SaaSAgent_setup",
                "goal": "Complete signup with generated QA credentials.",
                "actions": [
                    {"action": "click_action", "params": {"action_id": "nav.cancel", "optional": True}},
                    {"action": "click_action", "params": {"action_id": "intent.register"}},
                    {"action": "type_composer", "params": {"text": "QA User"}},
                    {"action": "click_send", "params": {}},
                    {"action": "type_composer", "params": {"text": "{{signup_email}}"}},
                    {"action": "click_send", "params": {}},
                    {"action": "type_composer", "params": {"text": "{{signup_password}}"}},
                    {"action": "click_send", "params": {}},
                ],
                "evidence_gates": [
                    {
                        "gate": "route_deck_current_node_one_of",
                        "required": True,
                        "params": {"nodes": ["saas_agent_job", "saas_agent_select", "saas_agent_confirm", "operator_ready"]},
                    }
                ],
            }
        ],
    },
    {
        "id": "routedeck_smoke",
        "name": "RouteDeck map opens and responds",
        "persona": "QA operator inspecting navigation evidence.",
        "opening_message": "",
        "context": "The debugger should be inspectable without changing nodes directly.",
        "pass_criteria": "Map opens, graph receives pan/zoom gestures, and no console errors are captured.",
        "max_turns": 4,
        "milestones": [
            {
                "id": "map-controls",
                "capability": "routedeck_map",
                "goal": "Open RouteDeck and exercise graph controls.",
                "actions": [
                    {"action": "open_route_deck", "params": {}},
                    {"action": "pan_graph", "params": {}},
                    {"action": "zoom_graph", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "visible_text", "required": True, "params": {"text": "RouteDeck map"}},
                    {"gate": "route_deck_snapshot_present", "required": True, "params": {}},
                    {"gate": "no_console_errors", "required": True, "params": {}},
                ],
            }
        ],
    },
    {
        "id": "connection_catalog_preview",
        "name": "Preview and activate an OpenAPI connection",
        "persona": "SaaSAgent owner connecting a SaaS API schema.",
        "opening_message": "",
        "context": "The SaaSAgent should expose a real Connections workbench, schema preview, and activation result.",
        "pass_criteria": "Connection preview succeeds and activation produces at least one generated action.",
        "max_turns": 8,
        "milestones": [
            {
                "id": "preview-openapi",
                "capability": "connection_setup",
                "goal": "Open Connections and preview a reachable OpenAPI URL.",
                "actions": [
                    {"action": "open_saas_agent_view", "params": {"view": "connect"}},
                    {"action": "fill_connection_form", "params": {"fixture": "petstore_openapi"}},
                    {"action": "click_button", "params": {"label": "Preview API"}},
                    {"action": "collect_evidence", "params": {"include_api_status": True}},
                ],
                "evidence_gates": [
                    {"gate": "saas_agent_view", "required": True, "params": {"view": "connect"}},
                    {"gate": "visible_text", "required": True, "params": {"text": "Catalog preview"}},
                    {"gate": "api_response_ok", "required": True, "params": {"key": "connection_preview"}},
                    {"gate": "no_console_errors", "required": True, "params": {}},
                ],
            },
            {
                "id": "activate-catalog",
                "capability": "connection_setup",
                "goal": "Activate the connection and verify generated catalog output.",
                "actions": [
                    {"action": "click_button", "params": {"label": "Save and activate"}},
                    {"action": "wait_for_catalog", "params": {}},
                    {"action": "collect_evidence", "params": {"include_catalog": True}},
                ],
                "evidence_gates": [
                    {"gate": "catalog_count_at_least", "required": True, "params": {"key": "actions", "min": 1}},
                    {"gate": "catalog_count_at_least", "required": True, "params": {"key": "tools", "min": 1}},
                    {"gate": "visible_text", "required": True, "params": {"text": "ready"}},
                ],
            },
        ],
    },
    {
        "id": "actions_entities_surfaces",
        "name": "Generated Actions and Entities canvases are inspectable",
        "persona": "Operator validating what the API schema created.",
        "opening_message": "",
        "context": "After activation, operators need focused canvases for generated actions and inferred entities.",
        "pass_criteria": "Actions and Entities views show generated catalog evidence without console errors.",
        "max_turns": 6,
        "milestones": [
            {
                "id": "actions-canvas",
                "capability": "catalog_inspection",
                "goal": "Open the generated Actions surface.",
                "actions": [
                    {"action": "ensure_petstore_connection", "params": {}},
                    {"action": "open_saas_agent_view", "params": {"view": "actions"}},
                    {"action": "collect_saas_agent_catalog", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "saas_agent_view", "required": True, "params": {"view": "actions"}},
                    {"gate": "visible_text", "required": True, "params": {"text": "Generated REST actions"}},
                    {"gate": "catalog_count_at_least", "required": True, "params": {"key": "actions", "min": 1}},
                ],
            },
            {
                "id": "entities-canvas",
                "capability": "catalog_inspection",
                "goal": "Open the inferred Entities surface.",
                "actions": [
                    {"action": "open_saas_agent_view", "params": {"view": "entities"}},
                    {"action": "collect_saas_agent_catalog", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "saas_agent_view", "required": True, "params": {"view": "entities"}},
                    {"gate": "visible_text", "required": True, "params": {"text": "API groups"}},
                    {"gate": "catalog_count_at_least", "required": True, "params": {"key": "entities", "min": 1}},
                    {"gate": "no_console_errors", "required": True, "params": {}},
                ],
            },
        ],
    },
    {
        "id": "read_safe_rest_execution_trace",
        "name": "Read-safe REST task emits a tool trace",
        "persona": "Operator asking the agent to inspect API data.",
        "opening_message": "List available pets from the connected API.",
        "context": "Read-only REST operations should execute through the generated tool surface and show trace evidence.",
        "pass_criteria": "The assistant responds and a generated REST tool call is recorded.",
        "max_turns": 8,
        "milestones": [
            {
                "id": "read-tool-call",
                "capability": "rest_execution",
                "goal": "Ask for a read-safe API operation in chat.",
                "actions": [
                    {"action": "ensure_petstore_connection", "params": {}},
                    {"action": "open_saas_agent_view", "params": {"view": "chat"}},
                    {"action": "send_operator_chat", "params": {"text": "List available pets from the connected API."}},
                    {"action": "collect_evidence", "params": {"include_tool_calls": True}},
                ],
                "evidence_gates": [
                    {"gate": "assistant_response", "required": True, "params": {}},
                    {"gate": "tool_called", "required": True, "params": {"tool_name_contains": "pet"}},
                    {"gate": "message_not_contains", "required": True, "params": {"text": "No REST catalog is active"}},
                ],
            }
        ],
    },
    {
        "id": "write_rest_execution_requires_approval",
        "name": "Write REST task stops at approval",
        "persona": "Operator asking the agent to mutate API data.",
        "opening_message": "Create a new pet named QA Approval Test.",
        "context": "Unsafe generated REST operations should not execute silently.",
        "pass_criteria": "The assistant surfaces approval-required state rather than running a write automatically.",
        "max_turns": 8,
        "milestones": [
            {
                "id": "write-approval",
                "capability": "rest_execution",
                "goal": "Ask for a write API operation and verify the approval guard.",
                "actions": [
                    {"action": "ensure_petstore_connection", "params": {}},
                    {"action": "open_saas_agent_view", "params": {"view": "chat"}},
                    {"action": "send_operator_chat", "params": {"text": "Create a new pet named QA Approval Test."}},
                    {"action": "collect_evidence", "params": {"include_tool_calls": True}},
                ],
                "evidence_gates": [
                    {"gate": "assistant_response", "required": True, "params": {}},
                    {"gate": "visible_text", "required": True, "params": {"text": "approval"}},
                    {"gate": "message_not_contains", "required": True, "params": {"text": "Executed POST"}},
                ],
            }
        ],
    },
    {
        "id": "rag_memory_learning_surfaces",
        "name": "RAG, memory, and learning surfaces are reachable",
        "persona": "Operator validating the completed SaaS Agent foundation.",
        "opening_message": "Inspect generated knowledge, save a memory, and review sandbox learning.",
        "context": "The foundation must expose knowledge generation, durable memory, and learning review as visible operator surfaces.",
        "pass_criteria": "Knowledge, memory, and learning surfaces render without console errors.",
        "max_turns": 10,
        "milestones": [
            {
                "id": "knowledge-rag",
                "capability": "rag_generation",
                "goal": "Open Knowledge Base and verify generated RAG control is visible.",
                "actions": [
                    {"action": "open_saas_agent_view", "params": {"view": "attachments"}},
                    {"action": "collect_evidence", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "saas_agent_view", "required": True, "params": {"view": "attachments"}},
                    {"gate": "visible_text", "required": True, "params": {"text": "Generate catalog RAG"}},
                    {"gate": "no_console_errors", "required": True, "params": {}},
                ],
            },
            {
                "id": "memory-panel",
                "capability": "memory",
                "goal": "Open Sessions & Memory and verify manual memory save is visible.",
                "actions": [
                    {"action": "open_saas_agent_view", "params": {"view": "admin"}},
                    {"action": "click_button", "params": {"label": "Memories"}},
                    {"action": "collect_evidence", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "saas_agent_view", "required": True, "params": {"view": "admin"}},
                    {"gate": "visible_text", "required": True, "params": {"text": "Save memory"}},
                    {"gate": "no_console_errors", "required": True, "params": {}},
                ],
            },
            {
                "id": "learning-panel",
                "capability": "sandbox_learning",
                "goal": "Open Learn and verify sandbox learning review is visible.",
                "actions": [
                    {"action": "open_saas_agent_view", "params": {"view": "learn"}},
                    {"action": "collect_evidence", "params": {}},
                ],
                "evidence_gates": [
                    {"gate": "saas_agent_view", "required": True, "params": {"view": "learn"}},
                    {"gate": "visible_text", "required": True, "params": {"text": "Sandbox learning"}},
                    {"gate": "no_console_errors", "required": True, "params": {}},
                ],
            },
        ],
    },
]
