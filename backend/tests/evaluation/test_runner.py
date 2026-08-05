from corpus.evaluation.runner import _deterministic_assertions, _redact_visible_text
from corpus.evaluation.runner import _behavior_setup_operation_ids


def test_deterministic_assertions_check_runtime_facts_not_response_wording() -> None:
    scenario = {
        "expectations": {
            "finalBehavior": "Ask Lounge for product help",
            "authentication": "public",
            "requiredSuggestedActions": ["Sign in", "Sign up"],
        }
    }
    projection = {
        "current": {"node_id": "lounge.product_help"},
        "suggested_actions": [{"label": "Sign up"}, {"label": "Sign in"}],
    }
    transcript = [{"role": "assistant", "content": "The experimental API path is not connected to agent deployment."}]

    results = _deterministic_assertions(
        scenario,
        {"Ask Lounge for product help": "lounge.product_help"},
        projection,
        transcript,
    )

    assert all(item["passed"] for item in results)


def test_deterministic_assertions_accept_explicit_alternative_final_behavior() -> None:
    scenario = {
        "expectations": {
            "finalBehavior": "Sign in",
            "allowedFinalBehaviors": ["Ask Lounge for product help"],
            "authentication": "public",
            "requiredSuggestedActions": [],
        }
    }
    projection = {
        "current": {"node_id": "lounge.product_help"},
        "suggested_actions": [{"label": "Sign up"}, {"label": "Sign in"}],
    }

    results = _deterministic_assertions(
        scenario,
        {
            "Sign in": "lounge.sign_in",
            "Ask Lounge for product help": "lounge.product_help",
        },
        projection,
        [{"role": "assistant", "content": "I can open sign in or sign up."}],
    )

    assert next(item for item in results if item["name"] == "final behavior")["passed"] is True


def test_deterministic_assertions_check_starting_behavior_and_required_surfaces() -> None:
    scenario = {
        "expectations": {
            "startingBehavior": "Arrive in the Lounge",
            "finalBehavior": "Request password recovery",
            "authentication": "public",
            "requiredSurfaces": ["Password reset request surface"],
            "requiredSuggestedActions": [],
        }
    }
    starting_projection = {"current": {"node_id": "lounge.home"}}
    projection = {
        "current": {"node_id": "lounge.forgot_password"},
        "suggested_actions": [],
        "surfaces": {
            "active": {"surface_id": "lounge.forgot_password"},
            "frame": [],
        },
    }

    results = _deterministic_assertions(
        scenario,
        {
            "Arrive in the Lounge": "lounge.home",
            "Request password recovery": "lounge.forgot_password",
        },
        projection,
        [{"role": "assistant", "content": "Use the private recovery form."}],
        starting_projection=starting_projection,
        surface_ids={"Password reset request surface": "lounge.forgot_password"},
    )

    assert next(item for item in results if item["name"] == "starting behavior")["passed"] is True
    assert next(item for item in results if item["name"] == "required surfaces")["passed"] is True


def test_behavior_setup_operations_resolve_through_manifest() -> None:
    behaviors = [
        {
            "designBehavior": "Arrive in the Lounge",
            "operations": {"Open owner sign-in": "lounge.arrival.open_sign_in"},
        },
        {
            "designBehavior": "Sign in",
            "operations": {"Open password recovery": "lounge.sign_in.open_password_recovery"},
        },
    ]

    assert _behavior_setup_operation_ids("Request password recovery", behaviors) == [
        "lounge.arrival.open_sign_in",
        "lounge.sign_in.open_password_recovery",
    ]
    assert _behavior_setup_operation_ids("Set a new password", behaviors) is None


def test_deterministic_assertions_reject_internal_framework_language() -> None:
    scenario = {
        "expectations": {
            "finalBehavior": "Ask Lounge for product help",
            "authentication": "public",
            "requiredSuggestedActions": [],
        }
    }
    projection = {"current": {"node_id": "lounge.product_help"}, "suggested_actions": []}

    results = _deterministic_assertions(
        scenario,
        {"Ask Lounge for product help": "lounge.product_help"},
        projection,
        [{"role": "assistant", "content": "RouteDeck session_version is 4."}],
    )

    assert next(item for item in results if item["name"] == "framework internals absent")["passed"] is False


def test_deterministic_assertions_reject_visible_model_protocol_markup() -> None:
    scenario = {
        "expectations": {
            "finalBehavior": "Ask Lounge for product help",
            "authentication": "public",
            "requiredSuggestedActions": [],
        }
    }
    projection = {"current": {"node_id": "lounge.product_help"}, "suggested_actions": []}

    results = _deterministic_assertions(
        scenario,
        {"Ask Lounge for product help": "lounge.product_help"},
        projection,
        [
            {
                "role": "assistant",
                "content": "to=rd_lounge_open_product_help code: {} Welcome.",
            }
        ],
    )

    assert next(
        item for item in results if item["name"] == "model protocol markup absent"
    )["passed"] is False


def test_evaluation_evidence_redacts_credentials_and_email_identifiers() -> None:
    value = "My email is me@example.com and my password is Secret123! Please sign me in."

    redacted = _redact_visible_text(value)

    assert "me@example.com" not in redacted
    assert "Secret123!" not in redacted
    assert "[redacted-email]" in redacted
    assert "[redacted-password]" in redacted


def test_evaluation_evidence_redacts_password_without_separator() -> None:
    value = "Register me with me@example.com and password Hunter2! right here."

    redacted = _redact_visible_text(value)

    assert "Hunter2!" not in redacted
    assert "password [redacted-password]" in redacted


def test_evaluation_evidence_preserves_ordinary_password_guidance() -> None:
    value = "Do not send your password or other credentials in chat."

    assert _redact_visible_text(value) == value
