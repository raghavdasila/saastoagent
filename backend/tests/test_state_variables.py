from types import SimpleNamespace

from backend.services.agent.state_variables import (
    get_variable_value,
    pending_choice_prompt,
    pending_choice_target_path_for_message,
    remember_choice_variable,
    remember_resource_result_variables,
    resolve_input_from_variables,
    resolve_pending_choice,
)


def test_remember_resource_result_variables_stores_id_and_scalar_fields():
    frame = {"kind": "result_context"}
    result = {
        "body": {
            "account": {
                "id": "acct_1",
                "region_id": "region_1",
                "currency_code": "usd",
                "items": [{"id": "line_1"}],
                "address": {"city": "Austin"},
            }
        },
        "error": None,
    }

    updated = remember_resource_result_variables(
        frame,
        collection_path="/api/accounts",
        result=result,
        origin={"method": "POST", "path": "/api/accounts/{id}/items", "tool_name": "postItems"},
    )

    assert get_variable_value(updated, "resource./api/accounts.id") == "acct_1"
    assert get_variable_value(updated, "resource./api/accounts.region_id") == "region_1"
    assert get_variable_value(updated, "resource./api/accounts.currency_code") == "usd"
    assert get_variable_value(updated, "resource./api/accounts.items") is None
    assert get_variable_value(updated, "resource./api/accounts.address") is None
    assert frame == {"kind": "result_context"}


def test_remember_resource_result_variables_prefers_declared_collection_object():
    result = {
        "body": {
            "line_item": {"id": "line_1", "quantity": 1},
            "cart": {"id": "cart_1", "region_id": "region_1"},
        },
        "error": None,
    }

    updated = remember_resource_result_variables(
        {"kind": "result_context"},
        collection_path="/store/carts",
        result=result,
        origin={"path": "/store/carts/{id}/line-items"},
    )

    assert get_variable_value(updated, "resource./store/carts.id") == "cart_1"
    assert get_variable_value(updated, "resource./store/carts.region_id") == "region_1"


def test_resolve_input_from_variables_prefers_matching_resource_field():
    frame = remember_resource_result_variables(
        {"kind": "result_context"},
        collection_path="/api/accounts",
        result={"body": {"account": {"id": "acct_1", "region_id": "region_1"}}, "error": None},
        origin={"path": "/api/accounts"},
    )
    action = SimpleNamespace(path="/api/accounts/{id}/complete")

    assert resolve_input_from_variables(frame, "id", action=action) == "acct_1"
    assert resolve_input_from_variables(frame, "region_id", action=action) == "region_1"


def test_choice_variable_prompts_by_label_and_resolves_private_value():
    frame = remember_choice_variable(
        {"kind": "result_context"},
        input_name="option_id",
        target_action_path="/api/accounts/{id}/options",
        items=[
            {"id": "opt_fast", "name": "Fast Delivery"},
            {"id": "opt_slow", "name": "Slow Delivery"},
        ],
        origin={"method": "GET", "path": "/api/options"},
    )

    prompt = pending_choice_prompt(frame, ["option_id"])

    assert "Fast Delivery" in prompt
    assert "opt_fast" not in prompt
    assert resolve_pending_choice(frame, "option_id", "use fast delivery") == "opt_fast"
    assert pending_choice_target_path_for_message(frame, "use fast delivery") == "/api/accounts/{id}/options"
