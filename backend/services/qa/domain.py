from __future__ import annotations

QA_DOMAIN_MODEL = {
    "name": "SaaStoAgent entry navigation QA",
    "description": "UI-driven behavioral QA for entry, auth, workspace setup, and RouteDeck navigation.",
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
            "id": "workspace_setup",
            "name": "Workspace setup navigation",
            "expected_user_behaviors": ["complete signup", "describe workspace", "back or cancel setup"],
            "evidence_gates": ["route_deck_current_node", "action_enabled", "assistant_response"],
        },
        {
            "id": "routedeck_map",
            "name": "RouteDeck debugger",
            "expected_user_behaviors": ["open map", "pan graph", "zoom graph", "inspect nodes"],
            "evidence_gates": ["route_deck_snapshot_present", "visible_text", "no_console_errors"],
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
        "id": "signup_workspace_path",
        "name": "Signup reaches workspace setup",
        "persona": "New user creating a workspace.",
        "opening_message": "",
        "context": "Signup should continue into workspace creation without dead ends.",
        "pass_criteria": "The flow reaches workspace job, workspace confirm, or operator ready.",
        "max_turns": 14,
        "milestones": [
            {
                "id": "complete-signup",
                "capability": "workspace_setup",
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
                        "params": {"nodes": ["workspace_job", "workspace_select", "workspace_confirm", "operator_ready"]},
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
]
