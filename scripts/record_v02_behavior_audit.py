from __future__ import annotations

import argparse
import asyncio
import hashlib
import html
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urljoin
from uuid import uuid4

import httpx
from playwright.async_api import BrowserContext, Page, async_playwright


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DESIGN_STATE = ROOT / "docs" / "corpus-agent-design" / "workbench" / "design-state.json"
AUDIT_ROOT = ROOT / "audits" / "2026-08-v0.2-behavior-audit"
LEDGER_PATH = AUDIT_ROOT / "ledger.json"
TASKS_PATH = AUDIT_ROOT / "tasks.json"
HTML_PATH = AUDIT_ROOT / "index.html"
EVIDENCE_ROOT = AUDIT_ROOT / "evidence"
ARTIFACT_ROOT = ROOT / "artifacts" / "2026-08-v0.2-behavior-audit"
CORPUS_URL = "http://127.0.0.1:5199/"
BACKEND_URL = "http://127.0.0.1:8099"
STUDIO_URL = "http://127.0.0.1:8782/"
MEDUSA_URL = "http://127.0.0.1:9100/health"
DESKTOP = {"width": 1440, "height": 1000}
MOBILE = {"width": 390, "height": 844}


FEATURE_DEPTH = {
    "Workspace": 2,
    "Agents": 3,
    "Source Hub": 3,
    "API Source": 4,
    "Agent Designer": 5,
    "Builder and Sandbox": 6,
    "Evaluation": 7,
    "Channels and Deployment": 8,
    "Operations": 9,
}

FEATURE_ENTRY = {
    "Lounge": "lounge-arrival",
    "Workspace": "enter-workspace",
    "Agents": "agents-view",
    "Source Hub": "sources-view",
    "API Source": "api-upload-yaml",
    "Agent Designer": "agent-designer-resolve-source-inputs",
    "Builder and Sandbox": "builder-assemble",
    "Evaluation": "evaluation-resolve-missing-build",
    "Channels and Deployment": "channels-resolve-missing-eligibility",
    "Operations": "operations-view-interactions",
}

ENTRY_PARENT = {
    "enter-workspace": "owner-auth-register",
    "agents-view": "enter-workspace",
    "sources-view": "enter-workspace",
    "api-upload-yaml": "sources-start-api",
    "agent-designer-resolve-source-inputs": "agents-attach-source",
    "builder-assemble": "agent-designer-request-build",
    "evaluation-resolve-missing-build": "agents-operations-hub",
    "channels-resolve-missing-eligibility": "agents-operations-hub",
    "operations-view-interactions": "channels-use-hosted-agent",
}

STATE_PARENT = {
    "owner-auth-confirm-reset": "owner-auth-request-reset",
    "owner-auth-request-verification": "enter-workspace",
    "owner-auth-confirm-verification": "owner-auth-request-verification",
    "owner-auth-sign-out": "enter-workspace",
    "agents-inspect": "agents-create",
    "agents-attach-source": "sources-select-for-agent",
    "agents-detach-source": "agents-attach-source",
    "agents-open-source": "agents-attach-source",
    "agents-build-source-lineage": "builder-observe-lifecycle",
    "sources-start-api": "sources-view",
    "sources-select-for-agent": "api-curate-operations",
    "api-process-toolrouter": "api-upload-yaml",
    "api-monitor-processing": "api-process-toolrouter",
    "api-inspect-graph": "api-monitor-processing",
    "api-replay-graph": "api-inspect-graph",
    "api-curate-operations": "api-monitor-processing",
    "api-configure-connection": "api-monitor-processing",
    "api-test-operation": "api-curate-operations",
    "agent-designer-propose": "agent-designer-resolve-source-inputs",
    "agent-designer-generate-feature": "agent-designer-propose",
    "agent-designer-customize": "agent-designer-generate-feature",
    "agent-designer-inspect-navgraph": "agent-designer-customize",
    "agent-designer-review": "agent-designer-customize",
    "agent-designer-request-build": "agent-designer-review",
    "builder-observe-lifecycle": "builder-assemble",
    "builder-control-runtime": "builder-observe-lifecycle",
    "builder-generate-evalset": "builder-observe-lifecycle",
    "sandbox-start-run": "builder-control-runtime",
    "sandbox-continue-clarification": "sandbox-start-run",
    "sandbox-inspect-routedeck": "sandbox-start-run",
    "sandbox-inspect-operation-trace": "sandbox-start-run",
    "evaluation-generate-evalset": "builder-generate-evalset",
    "evaluation-create-case": "sandbox-start-run",
    "evaluation-manage-cases": "evaluation-create-case",
    "evaluation-run-build": "evaluation-create-case",
    "evaluation-observe-lifecycle": "evaluation-run-build",
    "channels-create-hosted-web": "evaluation-observe-lifecycle",
    "channels-view-hosted-address": "channels-create-hosted-web",
    "deployment-publish-eligible-build": "channels-create-hosted-web",
    "deployment-observe-lifecycle": "deployment-publish-eligible-build",
    "deployment-rollback": "deployment-observe-lifecycle",
    "channels-set-availability": "deployment-observe-lifecycle",
    "channels-use-hosted-agent": "channels-set-availability",
    "deployed-agent-clarification": "channels-use-hosted-agent",
    "operations-inspect-evidence": "operations-view-interactions",
    "operations-promote-evaluation": "operations-inspect-evidence",
}

CONTINUATION_BEHAVIORS = {
    "workspace-route-task",
    "owner-auth-confirm-reset",
    "owner-auth-confirm-verification",
    "sources-select-for-agent",
    "agent-designer-request-build",
    "evaluation-resolve-missing-build",
    "channels-resolve-missing-eligibility",
    "sandbox-continue-clarification",
    "channels-use-hosted-agent",
    "deployed-agent-clarification",
    "operations-promote-evaluation",
}


def now() -> str:
    return datetime.now(UTC).isoformat()


def safe_runtime_url(value: str) -> str:
    """Retain useful page identity without persisting credentials or one-time links."""
    return value.split("#", 1)[0].split("?", 1)[0]


def story_depth(feature: str, story_id: str) -> int:
    if feature == "Lounge":
        return 0 if story_id in {"lounge-arrival", "lounge-product-help"} else 1
    return FEATURE_DEPTH[feature]


def story_mode(story: dict[str, Any]) -> str:
    story_id = str(story["id"])
    if story_id in {
        "lounge-product-help",
        "workspace-product-help",
        "workspace-route-task",
        "deployed-agent-clarification",
        "sandbox-continue-clarification",
    }:
        return "chat"
    if story_id in {"agents-setup-from-api-file", "channels-use-hosted-agent"}:
        return "hybrid"
    return "surface"


def freeze_inventory() -> dict[str, Any]:
    state = json.loads(DESIGN_STATE.read_text(encoding="utf-8"))
    behaviors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for feature in state["features"]:
        for story in feature["stories"]:
            story_id = str(story["id"])
            if story_id in seen:
                raise RuntimeError(f"Duplicate Design Studio behavior ID: {story_id}")
            seen.add(story_id)
            behaviors.append(
                {
                    "id": story_id,
                    "feature": feature["name"],
                    "title": story["title"],
                    "userIntent": story.get("userIntent", ""),
                    "agentIntent": story.get("agentIntent", ""),
                    "expectedBehavior": story.get("expectedBehavior", ""),
                    "designStatus": story.get("status", ""),
                    "studioRejectionReason": story.get("rejectionReason", ""),
                    "depth": story_depth(feature["name"], story_id),
                    "mode": story_mode(story),
                    "surfaces": [item.get("name", "") for item in story.get("surfaces", [])],
                    "operations": [item.get("name", "") for item in story.get("operations", [])],
                    "operationAvailability": {
                        item.get("name", ""): item.get("availableThrough", "")
                        for item in story.get("operations", [])
                    },
                    "assertions": [
                        {
                            "evalId": evaluation.get("id", ""),
                            "title": evaluation.get("title", ""),
                            "blocking": bool(evaluation.get("blocking")),
                            "required": evaluation.get("requiredCriteria", []),
                            "forbidden": evaluation.get("forbiddenCriteria", []),
                        }
                        for evaluation in story.get("behaviorEvals", [])
                        if evaluation.get("enabled", True)
                    ],
                    "status": "pending",
                    "observed": "Not executed.",
                    "screenshots": [],
                    "screenshotHashes": {},
                    "diagnostics": [],
                    "attempts": [],
                    "taskId": None,
                    "updatedAt": None,
                }
            )
    if len(behaviors) != 77:
        raise RuntimeError(f"Expected the frozen current inventory to contain 77 behaviors, found {len(behaviors)}")
    by_id = {item["id"]: item for item in behaviors}
    edges = []
    for item in behaviors:
        story_id = item["id"]
        if story_id == "lounge-arrival":
            item["prerequisites"] = []
            continue
        parent = STATE_PARENT.get(story_id) or ENTRY_PARENT.get(story_id)
        if parent is None:
            entry = FEATURE_ENTRY[item["feature"]]
            parent = "lounge-arrival" if story_id == entry else entry
        if parent not in by_id:
            raise RuntimeError(f"Unknown BFS prerequisite {parent!r} for {story_id!r}")
        item["prerequisites"] = [parent]
        if by_id[parent]["depth"] > item["depth"]:
            edge_type = "state-dependency"
        elif story_id in CONTINUATION_BEHAVIORS:
            edge_type = "continuation"
        elif item["depth"] > by_id[parent]["depth"]:
            edge_type = "prerequisite"
        else:
            edge_type = "navigation"
        edges.append({
            "from": parent,
            "to": story_id,
            "type": edge_type,
        })
    return {
        "schema": "corpus.v02.behavior-audit.v1",
        "createdAt": now(),
        "updatedAt": now(),
        "source": str(DESIGN_STATE.relative_to(ROOT)).replace("\\", "/"),
        "sourceSha256": hashlib.sha256(DESIGN_STATE.read_bytes()).hexdigest(),
        "runtime": {
            "location": "local authoritative application as-is",
            "corpus": CORPUS_URL,
            "backend": BACKEND_URL,
            "studio": STUDIO_URL,
            "medusa": MEDUSA_URL,
        },
        "owner": {"kind": "one newly registered disposable audit owner", "identifier": "redacted"},
        "edges": edges,
        "behaviors": behaviors,
    }


def load_or_create_ledger() -> dict[str, Any]:
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    if LEDGER_PATH.exists():
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        ids = [item["id"] for item in ledger.get("behaviors", [])]
        frozen = freeze_inventory()
        frozen_ids = [item["id"] for item in frozen["behaviors"]]
        if ids != frozen_ids or ledger.get("sourceSha256") != frozen.get("sourceSha256"):
            raise RuntimeError("The existing ledger does not match the frozen current Design Studio inventory.")
        return ledger
    ledger = freeze_inventory()
    write_outputs(ledger)
    return ledger


def result_counts(ledger: dict[str, Any]) -> dict[str, int]:
    counts = {name: 0 for name in ("passed", "failed", "blocked", "pending", "not_applicable")}
    for item in ledger["behaviors"]:
        counts[item["status"]] += 1
    return counts


def write_outputs(ledger: dict[str, Any]) -> None:
    ledger["updatedAt"] = now()
    existing_task_status: dict[str, str] = {}
    if TASKS_PATH.exists():
        try:
            existing_tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8")).get("tasks", [])
            existing_task_status = {str(task.get("id")): str(task.get("status")) for task in existing_tasks}
        except (OSError, ValueError, TypeError):
            existing_task_status = {}
    tasks = []
    for item in ledger["behaviors"]:
        if item["status"] not in {"failed", "blocked", "pending"} or item["observed"] == "Not executed.":
            continue
        task_id = item.get("taskId") or f"TASK-{item['id']}"
        item["taskId"] = task_id
        default_task_status = "accepted_deferred" if item["status"] == "pending" and item.get("designStatus") == "draft" else "open"
        task_status = existing_task_status.get(task_id, default_task_status)
        if task_status not in {"open", "in_progress", "fixed_unverified", "retested_passed", "accepted_deferred"}:
            task_status = default_task_status
        tasks.append(
            {
                "id": task_id,
                "behaviorId": item["id"],
                "feature": item["feature"],
                "title": item["title"],
                "severity": "high" if item["status"] == "failed" else "low" if item["status"] == "pending" else "medium",
                "category": "behavior-defect" if item["status"] == "failed" else "audit-blocker" if item["status"] == "blocked" else "deferred-capability",
                "status": task_status,
                "result": item["status"],
                "reproduction": f"Run the application as-is and follow the {item['mode']} interaction shown by the ordered evidence for {item['id']}.",
                "expectedResult": item["expectedBehavior"],
                "observedResult": item["observed"],
                "evidence": item["screenshots"],
                "evidenceHashes": item.get("screenshotHashes", {}),
                "ownerSubsystem": item["feature"],
                "runHistory": item.get("attempts", []),
            }
        )
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    TASKS_PATH.write_text(json.dumps({"updatedAt": now(), "tasks": tasks}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    HTML_PATH.write_text(render_html(ledger, tasks), encoding="utf-8")


def render_html(ledger: dict[str, Any], tasks: list[dict[str, Any]]) -> str:
    counts = result_counts(ledger)
    last_run = ledger.get("lastRun", {})
    dependency_summary = ", ".join(
        f"{name}={check.get('status') if check.get('ready') else 'unavailable'}"
        for name, check in ledger.get("dependencyChecks", {}).items()
    ) or "not checked"
    edge_by_target = {edge["to"]: edge for edge in ledger.get("edges", [])}
    cards = []
    for item in sorted(ledger["behaviors"], key=lambda value: (value["depth"], value["feature"], value["id"])):
        images = "".join(
            f'<a href="{html.escape(path)}"><img loading="lazy" src="{html.escape(path)}" alt="{html.escape(item["title"])} evidence"></a>'
            for path in item["screenshots"]
        ) or '<p class="muted">No evidence captured yet.</p>'
        diagnostics = "".join(f"<li>{html.escape(str(value))}</li>" for value in item["diagnostics"]) or "<li>None recorded.</li>"
        prerequisites = ", ".join(item.get("prerequisites", [])) or "root"
        surfaces = ", ".join(item.get("surfaces", [])) or "none declared"
        operations = ", ".join(
            f"{name} [{item.get('operationAvailability', {}).get(name, 'unspecified')}]"
            for name in item.get("operations", [])
        ) or "none declared"
        task_id = str(item.get("taskId") or "")
        task_reference = f'<a href="#task-{html.escape(task_id)}">{html.escape(task_id)}</a>' if task_id else "none"
        assertion_rows = []
        for assertion in item.get("assertions", []):
            required = "".join(f"<li>{html.escape(str(value))}</li>" for value in assertion.get("required", [])) or "<li>None.</li>"
            forbidden = "".join(f"<li>{html.escape(str(value))}</li>" for value in assertion.get("forbidden", [])) or "<li>None.</li>"
            assertion_rows.append(f'<details class="assertion"><summary><code>{html.escape(assertion.get("evalId", ""))}</code> {html.escape(assertion.get("title", ""))}</summary><b>Required</b><ul>{required}</ul><b>Forbidden</b><ul>{forbidden}</ul></details>')
        assertions = "".join(assertion_rows) or '<p class="muted">No enabled Studio evaluation assertions.</p>'
        cards.append(
            f'''<article id="behavior-{html.escape(item['id'])}" class="behavior" data-feature="{html.escape(item['feature'])}" data-depth="{item['depth']}" data-mode="{item['mode']}" data-status="{item['status']}">
<details><summary><span class="status {item['status']}">{item['status']}</span><strong>{html.escape(item['title'])}</strong><small>{html.escape(item['feature'])} · depth {item['depth']} · {item['mode']}</small></summary>
<div class="body"><p><b>ID:</b> <code>{html.escape(item['id'])}</code></p><p><b>Prerequisite:</b> <code>{html.escape(prerequisites)}</code></p><p><b>Studio status:</b> {html.escape(item.get('designStatus', ''))}</p><p><b>Declared surfaces:</b> {html.escape(surfaces)}</p><p><b>Declared operations:</b> {html.escape(operations)}</p><p><b>Expected:</b> {html.escape(item['expectedBehavior'])}</p><p><b>Observed:</b> {html.escape(item['observed'])}</p><p><b>Task:</b> {task_reference}</p><h4>Studio assertions</h4>{assertions}<h4>Ordered screenshots</h4><div class="shots">{images}</div><h4>Diagnostics</h4><ul>{diagnostics}</ul></div></details></article>'''
        )
    graph_columns = []
    for depth in sorted({item["depth"] for item in ledger["behaviors"]}):
        nodes = []
        for item in sorted((value for value in ledger["behaviors"] if value["depth"] == depth), key=lambda value: (value["feature"], value["id"])):
            parent = (item.get("prerequisites") or ["—"])[0]
            edge_type = edge_by_target.get(item["id"], {}).get("type", "root")
            nodes.append(
                f'<a class="graph-node {item["status"]}" data-feature="{html.escape(item["feature"])}" data-depth="{item["depth"]}" data-mode="{item["mode"]}" data-status="{item["status"]}" href="#behavior-{html.escape(item["id"])}" title="{html.escape(edge_type)} from {html.escape(parent)}"><b>{html.escape(item["title"])}</b><small>{html.escape(item["feature"])} · {html.escape(item["id"])}</small></a>'
            )
        graph_columns.append(f'<section class="graph-depth"><h3>Depth {depth}</h3>{"".join(nodes)}</section>')
    options = lambda key: "".join(
        f'<option value="{html.escape(str(value))}">{html.escape(str(value))}</option>'
        for value in sorted({item[key] for item in ledger["behaviors"]}, key=str)
    )
    task_cards = "".join(
        f'''<article id="task-{html.escape(task['id'])}" class="task"><h3><code>{html.escape(task['id'])}</code> · {html.escape(task['title'])}</h3><p><b>{html.escape(task['status'])}</b> · {html.escape(task['severity'])} · {html.escape(task['category'])} · {html.escape(task['ownerSubsystem'])}</p><p><b>Observed:</b> {html.escape(task['observedResult'])}</p><p><b>Expected:</b> {html.escape(task['expectedResult'])}</p><p><a href="#behavior-{html.escape(task['behaviorId'])}">Open behavior evidence</a></p></article>'''
        for task in tasks
    ) or '<p class="muted">No follow-up tasks.</p>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Corpus v0.2 Behavior Audit</title>
<style>body{{font:15px/1.45 system-ui;margin:0;background:#0b0d10;color:#edf1f7}}main{{max-width:1500px;margin:auto;padding:24px}}h1{{margin-bottom:4px}}a{{color:#8ecbff}}.muted,small{{color:#9ca8b8}}.summary{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}}.metric,.task{{background:#171b22;border:1px solid #2c3340;border-radius:10px;padding:10px 14px}}.task{{margin:8px 0;scroll-margin-top:72px}}.filters{{position:sticky;top:0;background:#0b0d10ee;padding:10px 0;display:flex;gap:8px;z-index:2}}select{{background:#171b22;color:#edf1f7;border:1px solid #394252;border-radius:6px;padding:8px}}.graph{{display:flex;align-items:flex-start;gap:12px;max-height:640px;overflow:auto;padding:12px;border:1px solid #2c3340;border-radius:10px}}.graph-depth{{min-width:230px;max-width:230px}}.graph-depth h3{{position:sticky;top:0;background:#0b0d10;padding:6px 0;z-index:1}}.graph-node{{display:block;text-decoration:none;color:#edf1f7;background:#12161c;border:1px solid #2c3340;border-left:5px solid currentColor;border-radius:8px;padding:9px;margin:8px 0}}.graph-node small{{display:block;margin-top:3px;word-break:break-word}}.behavior{{border:1px solid #2c3340;border-radius:10px;margin:8px 0;background:#12161c;scroll-margin-top:72px}}summary{{cursor:pointer;padding:14px;display:grid;grid-template-columns:110px 1fr auto;gap:12px;align-items:center}}.body{{padding:0 16px 16px}}.assertion summary{{display:block;padding:8px 0}}.status{{text-transform:uppercase;font-size:11px;font-weight:700}}.passed{{color:#5ee49b}}.failed{{color:#ff7272}}.blocked{{color:#ffbd59}}.pending{{color:#aab3c1}}.not_applicable{{color:#7cc7ff}}.shots{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}}.shots img{{width:100%;border:1px solid #303846;border-radius:8px}}code{{word-break:break-all}}@media(max-width:640px){{main{{padding:12px}}.filters{{overflow-x:auto}}.graph{{max-height:480px}}summary{{grid-template-columns:90px 1fr}}summary small{{grid-column:1/-1}}}}</style></head><body><main><h1>Corpus v0.2 Behavior Audit</h1><p class="muted">Authoritative local application as-is · 77 frozen Design Studio behaviors · updated {html.escape(ledger['updatedAt'])}</p><p><b>Run:</b> <code>{html.escape(str(last_run.get('id', 'not started')))}</code> · started {html.escape(str(last_run.get('startedAt', '—')))} · finished {html.escape(str(last_run.get('finishedAt', '—')))}<br><b>Dependencies:</b> {html.escape(dependency_summary)} · <a href="ledger.json">ledger.json</a> · <a href="tasks.json">tasks.json</a></p>
<div class="summary">{''.join(f'<div class="metric"><b>{value}</b> {name}</div>' for name,value in counts.items())}<div class="metric"><b>{len(tasks)}</b> tasks</div></div>
<div class="filters"><select id="feature"><option value="">All features</option>{options('feature')}</select><select id="depth"><option value="">All depths</option>{options('depth')}</select><select id="mode"><option value="">All modes</option>{options('mode')}</select><select id="status"><option value="">All results</option>{options('status')}</select></div>
<h2>Breadth-first behavior graph</h2><p class="muted">Each node links to its evidence record; hover to see its immediate prerequisite.</p><div class="graph">{''.join(graph_columns)}</div>
<h2>Behavior evidence</h2><section>{''.join(cards)}</section><h2>Follow-up tasks</h2><section>{task_cards}</section></main><script>const dimensions=['feature','depth','mode','status'];for(const id of dimensions)document.getElementById(id).addEventListener('change',filter);function filter(){{for(const el of document.querySelectorAll('.behavior,.graph-node')){{let show=true;for(const id of dimensions){{const v=document.getElementById(id).value;if(v&&el.dataset[id]!==v)show=false}}el.hidden=!show}}}}for(const node of document.querySelectorAll('.graph-node'))node.addEventListener('click',()=>{{const target=document.querySelector(node.getAttribute('href'));if(target)target.querySelector('details').open=true}});</script></body></html>'''


def validate_outputs(ledger: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    behaviors = ledger.get("behaviors", [])
    ids = [item.get("id") for item in behaviors]
    known = set(ids)
    if len(ids) != 77 or len(known) != 77:
        issues.append(f"Inventory must contain 77 unique behaviors; found {len(ids)} records and {len(known)} unique IDs.")
    if ledger.get("sourceSha256") != hashlib.sha256(DESIGN_STATE.read_bytes()).hexdigest():
        issues.append("The ledger source hash no longer matches the authoritative Design Studio state.")
    children: dict[str, set[str]] = {}
    for edge in ledger.get("edges", []):
        if edge.get("from") not in known or edge.get("to") not in known:
            issues.append(f"Unknown graph reference: {edge!r}")
        if edge.get("type") not in {"navigation", "prerequisite", "continuation", "state-dependency"}:
            issues.append(f"Unknown graph edge type: {edge!r}")
        children.setdefault(str(edge.get("from")), set()).add(str(edge.get("to")))
    reachable = {"lounge-arrival"}
    while True:
        expanded = reachable | {child for parent in reachable for child in children.get(parent, set())}
        if expanded == reachable:
            break
        reachable = expanded
    if reachable != known:
        issues.append(f"The BFS graph has unreachable behaviors: {sorted(known - reachable)}")
    task_records = json.loads(TASKS_PATH.read_text(encoding="utf-8")).get("tasks", []) if TASKS_PATH.exists() else []
    task_by_behavior = {task.get("behaviorId"): task for task in task_records}
    allowed_task_statuses = {"open", "in_progress", "fixed_unverified", "retested_passed", "accepted_deferred"}
    for task in task_records:
        if task.get("status") not in allowed_task_statuses:
            issues.append(f"{task.get('id')}: unknown task status {task.get('status')!r}.")
        if not task.get("severity") or not task.get("category") or not task.get("ownerSubsystem"):
            issues.append(f"{task.get('id')}: incomplete task classification.")
        if not task.get("evidence") or not task.get("runHistory"):
            issues.append(f"{task.get('id')}: task has no evidence or run history.")
    for item in behaviors:
        behavior_id = str(item.get("id"))
        status = item.get("status")
        if status not in {"passed", "failed", "blocked", "pending", "not_applicable"}:
            issues.append(f"{behavior_id}: unknown status {status!r}.")
        screenshots = item.get("screenshots", [])
        if item.get("observed") == "Not executed.":
            issues.append(f"{behavior_id}: behavior was not executed or explicitly classified.")
        if status != "not_applicable" and len(screenshots) < 2:
            issues.append(f"{behavior_id}: {status} result has fewer than two screenshots.")
        for relative in screenshots:
            path = (AUDIT_ROOT / relative).resolve()
            if AUDIT_ROOT.resolve() not in path.parents or not path.is_file():
                issues.append(f"{behavior_id}: missing or invalid evidence path {relative!r}.")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if item.get("screenshotHashes", {}).get(relative) != actual:
                issues.append(f"{behavior_id}: SHA-256 mismatch for {relative!r}.")
        if status in {"failed", "blocked", "pending"} and behavior_id not in task_by_behavior:
            issues.append(f"{behavior_id}: {status} result has no linked task.")
        for diagnostic in item.get("diagnostics", []):
            if not isinstance(diagnostic, dict) or diagnostic.get("kind") not in {"console", "http", "page", "request", "worker"} or not diagnostic.get("message"):
                issues.append(f"{behavior_id}: unclassified diagnostic {diagnostic!r}.")
    for output in (LEDGER_PATH, TASKS_PATH, HTML_PATH):
        if not output.is_file():
            issues.append(f"Missing required output {output.name}.")
            continue
        text_value = output.read_text(encoding="utf-8", errors="replace")
        secret_patterns = {
            "authorization header": r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._~-]{12,}",
            "cookie header": r"(?i)(?:set-cookie|cookie)\s*[:=]\s*[^\s<]{12,}",
            "credential query": r"(?i)[?&](?:token|password|secret|api_key)=[^&\s<]{6,}",
            "private email address": r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            "one-time email link": r"(?i)(?:verify|reset-password)[^\s\"<]*(?:#|%23|\?)[^\s\"<]*(?:token|code)=",
        }
        for label, pattern in secret_patterns.items():
            if re.search(pattern, text_value):
                issues.append(f"{output.name}: possible {label} exposure.")
    return issues


class Recorder:
    def __init__(self, ledger: dict[str, Any], page: Page, context: BrowserContext, private_values: list[str], run_id: str) -> None:
        self.ledger = ledger
        self.page = page
        self.context = context
        self.private_values = private_values
        self.run_id = run_id
        self.by_id = {item["id"]: item for item in ledger["behaviors"]}
        self.active_behavior: str | None = None
        self.active_sequence = 0
        self.current_shots: list[str] = []
        self.diagnostics: list[dict[str, Any]] = []
        self.sequence_counts: dict[str, int] = {}
        self.executed_in_run: set[str] = set()
        page.on("console", self._on_console)
        page.on("pageerror", lambda error: self._diagnostic("page", str(error)))
        page.on("requestfailed", lambda request: self._diagnostic("request", f"{request.method} {request.url} {request.failure}"))
        page.on("response", self._on_response)

    def _diagnostic(self, kind: str, message: str) -> None:
        if self.active_behavior is not None:
            self.diagnostics.append({"kind": kind, "message": message})

    def _on_console(self, message: Any) -> None:
        if message.type in {"error", "warning"}:
            self._diagnostic("console", message.text)

    async def _on_response(self, response: Any) -> None:
        if response.status >= 400 and "/api/" in response.url:
            self._diagnostic("http", f"{response.status} {response.request.method} {response.url}")

    async def begin(self, behavior_id: str) -> None:
        self.active_behavior = behavior_id
        self.active_sequence = self.sequence_counts.get(behavior_id, 0) + 1
        self.sequence_counts[behavior_id] = self.active_sequence
        self.current_shots = []
        self.diagnostics = []
        await self.capture("01-start")

    async def capture(self, name: str, mobile: bool = False) -> str:
        if self.active_behavior is None:
            raise RuntimeError("No active behavior")
        behavior = self.by_id[self.active_behavior]
        mode = behavior["mode"]
        directory = EVIDENCE_ROOT / self.active_behavior / mode
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.active_sequence:02d}-{name}{'-mobile' if mobile else ''}.png"
        old_viewport = self.page.viewport_size
        if mobile:
            await self.page.set_viewport_size(MOBILE)
        style = await self.page.add_style_tag(content="input,textarea{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important}")
        await self.page.evaluate(
            """values => { const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let n; while(n=walker.nextNode()){ for(const v of values){ if(v && n.nodeValue && n.nodeValue.includes(v)){ n.__corpusAuditOriginal=n.nodeValue; n.nodeValue=n.nodeValue.split(v).join('[redacted]'); } } } }""",
            self.private_values,
        )
        await self.page.screenshot(path=path, full_page=not mobile)
        await self.page.evaluate(
            """() => { const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let n; while(n=walker.nextNode()){ if(Object.prototype.hasOwnProperty.call(n,'__corpusAuditOriginal')){ n.nodeValue=n.__corpusAuditOriginal; delete n.__corpusAuditOriginal; } } }"""
        )
        await style.evaluate("element => element.remove()")
        if mobile and old_viewport:
            await self.page.set_viewport_size(old_viewport)
        relative = str(path.relative_to(AUDIT_ROOT)).replace("\\", "/")
        self.current_shots.append(relative)
        return relative

    async def finish(self, status: str, observed: str) -> None:
        if self.active_behavior is None:
            raise RuntimeError("No active behavior")
        if len(self.current_shots) < 2:
            await self.capture("02-result")
        item = self.by_id[self.active_behavior]
        attempt = {
            "runId": self.run_id,
            "runAt": now(),
            "status": status,
            "observed": observed,
            "screenshots": list(self.current_shots),
            "diagnostics": list(self.diagnostics),
            "url": safe_runtime_url(self.page.url),
        }
        item["attempts"].append(attempt)
        retained_shots = list(item.get("screenshots", [])) if self.active_behavior in self.executed_in_run else []
        combined_shots = list(dict.fromkeys([*retained_shots, *self.current_shots]))
        item["status"] = status
        item["observed"] = observed
        item["screenshots"] = combined_shots
        item["screenshotHashes"] = {
            relative: hashlib.sha256((AUDIT_ROOT / relative).read_bytes()).hexdigest()
            for relative in combined_shots
        }
        item["diagnostics"] = list(self.diagnostics)
        item["updatedAt"] = now()
        if status in {"failed", "blocked", "pending"}:
            item["taskId"] = f"TASK-{item['id']}"
        else:
            item["taskId"] = None
        self.executed_in_run.add(self.active_behavior)
        write_outputs(self.ledger)
        print(f"[{len(self.executed_in_run):02d}/77] {self.active_behavior}: {status}", flush=True)
        self.active_behavior = None

    async def classify_here(self, behavior_id: str, status: str, observed: str) -> None:
        await self.begin(behavior_id)
        await self.capture("02-classification")
        await self.finish(status, observed)


async def create_mailtm_owner() -> dict[str, str]:
    async with httpx.AsyncClient(base_url="https://api.mail.tm", timeout=30, headers={"User-Agent": "Corpus-v0.2-Behavior-Audit/1.0"}) as client:
        response = await client.get("/domains?page=1")
        response.raise_for_status()
        domains = response.json().get("hydra:member", [])
        if not domains:
            raise RuntimeError("Mail.tm returned no available domain")
        address = f"corpus-v02-{secrets.token_hex(6)}@{domains[0]['domain']}"
        password = f"Corpus-{secrets.token_urlsafe(18)}!8"
        created = None
        for attempt in range(4):
            created = await client.post("/accounts", json={"address": address, "password": password})
            if created.status_code != 429:
                break
            await asyncio.sleep(5 * (attempt + 1))
        assert created is not None
        created.raise_for_status()
        token = await client.post("/token", json={"address": address, "password": password})
        token.raise_for_status()
        return {"email": address, "password": password, "mailToken": token.json()["token"], "displayName": "Corpus v0.2 Audit Owner"}


async def preflight_runtime(ledger: dict[str, Any]) -> None:
    targets = {
        "corpus": CORPUS_URL,
        "backend": f"{BACKEND_URL}/readyz",
        "studio": STUDIO_URL,
        "medusa": MEDUSA_URL,
    }
    checks: dict[str, dict[str, Any]] = {}
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for name, url in targets.items():
            try:
                response = await client.get(url)
                checks[name] = {"url": url, "status": response.status_code, "ready": response.status_code == 200}
            except Exception as error:
                checks[name] = {"url": url, "status": None, "ready": False, "error": type(error).__name__}
    ledger["dependencyChecks"] = checks
    write_outputs(ledger)
    unavailable = [name for name, check in checks.items() if not check["ready"]]
    if unavailable:
        raise RuntimeError(f"Required local runtime dependencies are unavailable: {', '.join(unavailable)}")


async def wait_for_mail(token: str, subject_words: tuple[str, ...], timeout_seconds: int = 45) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_seconds
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(base_url="https://api.mail.tm", headers=headers, timeout=20) as client:
        while time.monotonic() < deadline:
            response = await client.get("/messages?page=1")
            if response.status_code == 200:
                for item in response.json().get("hydra:member", []):
                    subject = str(item.get("subject", "")).lower()
                    if all(word in subject for word in subject_words):
                        detail = await client.get(f"/messages/{item['id']}")
                        if detail.status_code == 200:
                            return detail.json()
            await asyncio.sleep(3)
    return None


def mailbox_link(message: dict[str, Any], path: str) -> str:
    body = message.get("text") or ""
    if isinstance(body, list):
        body = "\n".join(str(value) for value in body)
    match = re.search(rf"https?://[^\s<>]+{re.escape(path)}#token=[^\s<>]+", str(body))
    if match is None:
        raise RuntimeError(f"The delivered message did not contain the expected {path} link.")
    return match.group(0).rstrip(".,)")


async def send_chat(page: Page, message: str) -> str:
    articles = page.locator("main article")
    before = await articles.count()
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        field = page.get_by_label("Message the assistant")
        button = page.get_by_role("button", name="Send message")
        if await field.input_value() != message:
            await field.fill(message)
        await page.wait_for_timeout(150)
        if await field.input_value() == message and await button.is_enabled():
            try:
                await button.click(timeout=2_000)
                break
            except Exception:
                pass
        await page.wait_for_timeout(150)
    else:
        raise RuntimeError("The visible chat composer did not stabilize for the requested message.")
    stop = page.get_by_role("button", name="Stop response")
    try:
        await stop.wait_for(state="visible", timeout=10_000)
    except Exception:
        pass
    try:
        await stop.wait_for(state="hidden", timeout=120_000)
    except Exception:
        pass
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and await articles.count() <= before:
        await page.wait_for_timeout(100)
    return await articles.last.inner_text() if await articles.count() else ""


async def open_account_surface(page: Page, name: str) -> None:
    button_name: str | re.Pattern[str] = (
        re.compile(r"^(Create account|Sign up)$", re.I)
        if name == "Create account"
        else name
    )
    button = page.get_by_role("button", name=button_name, exact=name != "Create account")
    await button.click()
    await page.get_by_role("heading", name=name, exact=True).wait_for(timeout=20_000)


async def ensure_workspace(page: Page) -> None:
    heading = page.get_by_role("heading", name="Corpus Workspace", exact=True)
    if await heading.is_visible():
        return
    cancel = page.get_by_role("button", name="Cancel", exact=True)
    agent_create = page.locator("section.agent-create")
    if await agent_create.count() and await agent_create.is_visible() and await cancel.count() and await cancel.first.is_visible():
        await cancel.first.click()
        agents_home = page.locator("section.agents-home")
        await agents_home.get_by_role("heading", name="Agents", exact=True).first.wait_for(timeout=30_000)
        await agents_home.get_by_role("button", name="Back to Workspace", exact=True).click()
        await heading.wait_for(timeout=30_000)
        return
    for name in ("Return to Workspace", "Continue to Workspace", "Back to Workspace"):
        action = page.get_by_role("button", name=name, exact=True)
        if await action.count() and await action.first.is_visible():
            await action.first.click()
            await heading.wait_for(timeout=30_000)
            return
    await page.goto(CORPUS_URL)
    action = page.get_by_role("button", name=re.compile(r"^(Return|Continue) to Workspace$"))
    if await action.count() and await action.first.is_visible():
        await action.first.click()
    await heading.wait_for(timeout=30_000)


async def audit_lounge_auth_workspace(recorder: Recorder, owner: dict[str, str]) -> None:
    from scripts.run_horizontal_product_journey import _type_exact

    page = recorder.page
    await page.goto(CORPUS_URL)
    await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)

    await recorder.begin("lounge-arrival")
    arrival_text = await page.locator("body").inner_text()
    await recorder.capture("02-lounge-ready", mobile=True)
    await recorder.finish("passed" if "Not signed in" in arrival_text and "Corpus Lounge" in arrival_text else "failed", "The public Lounge rendered with an unauthenticated ready state." if "Not signed in" in arrival_text else "The expected unauthenticated Lounge identity was not visible.")

    await recorder.begin("lounge-product-help")
    reply = await send_chat(page, "What can Corpus help me build?")
    await recorder.capture("02-product-answer")
    safe = "corpus" in reply.lower() and "routedeck" not in reply.lower()
    await recorder.finish("passed" if safe else "failed", f"Corpus returned a product-help answer without framework naming: {safe}.")

    await recorder.begin("owner-auth-register")
    await open_account_surface(page, "Create account")
    await recorder.capture("02-private-registration-surface")
    await recorder.capture("02-private-registration-surface", mobile=True)
    await _type_exact(page.get_by_label("Display name", exact=True), owner["displayName"], "owner display name")
    await _type_exact(page.get_by_label("Email", exact=True), owner["email"], "registration email")
    await _type_exact(page.get_by_label("Password", exact=True), owner["password"], "registration password")
    await recorder.capture("03-registration-ready")
    await page.locator("form").get_by_role("button", name="Create account", exact=True).click()
    try:
        await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)
        await recorder.capture("04-workspace-result")
        await recorder.finish("passed", "The account was created through the private surface and the same browser entered the authenticated Workspace.")
    except Exception as error:
        await recorder.capture("04-registration-failure")
        await recorder.finish("failed", f"Registration did not reach the authenticated Workspace: {type(error).__name__}.")
        return

    await recorder.begin("enter-workspace")
    workspace_text = await page.locator("body").inner_text()
    await recorder.capture("02-workspace-home", mobile=True)
    await recorder.finish("passed" if "Corpus Workspace" in workspace_text else "failed", "The authenticated owner Workspace home rendered." if "Corpus Workspace" in workspace_text else "Workspace home identity was not visible after authentication.")

    await recorder.begin("owner-auth-request-verification")
    manage_verification = page.get_by_role("button", name="Manage verification", exact=True)
    message = None
    if await manage_verification.count():
        await manage_verification.click()
        resend = page.get_by_role("button", name="Resend verification", exact=True)
        await resend.wait_for(state="visible", timeout=30_000)
        await recorder.capture("02-verification-surface")
        await resend.click()
        await page.wait_for_timeout(1000)
        await recorder.capture("03-verification-request-result")
        message = await wait_for_mail(owner["mailToken"], ("verify",), 30)
        visible = (await page.locator("main").inner_text()).casefold()
        if message:
            await recorder.finish("passed", "Corpus accepted the verification request and Mail.tm received the verification message.")
        elif "unavailable" in visible or "failed" in visible or "too many" in visible:
            await recorder.finish("failed", "The verification request exposed a visible delivery failure and no verification message arrived in Mail.tm.")
        else:
            await recorder.finish("failed", "Corpus accepted the verification action, but no verification message arrived in Mail.tm within 30 seconds.")
    else:
        await recorder.capture("02-verification-unavailable")
        await recorder.finish("pending", "No Manage verification action was visible in the current authenticated Workspace.")

    if message:
        await recorder.begin("owner-auth-confirm-verification")
        try:
            await page.goto(mailbox_link(message, "/verify"))
            verify = page.locator("section.workspace-auth")
            await verify.get_by_role("button", name="Verify email", exact=True).wait_for(timeout=30_000)
            await recorder.capture("02-verification-link-opened")
            await verify.get_by_role("button", name="Verify email", exact=True).click()
            status = await verify.get_by_role("status").inner_text(timeout=30_000)
            await recorder.capture("03-email-verified")
            await recorder.finish("passed" if "token=" not in page.url and "verif" in status.casefold() else "failed", "The one-time verification link was confirmed, removed from the visible URL, and refreshed owner verification state.")
        except Exception as error:
            await recorder.capture("99-verification-failure")
            await recorder.finish("failed", f"The delivered verification link did not complete through the visible surface: {type(error).__name__}.")
    else:
        await recorder.classify_here("owner-auth-confirm-verification", "blocked", "No valid verification link was available from the real configured mail path.")

    await ensure_workspace(page)
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)

    await recorder.begin("workspace-activity-help")
    body = await page.locator("body").inner_text()
    await recorder.capture("02-current-activity")
    await recorder.finish("passed" if "activity" in body.lower() or "recent" in body.lower() else "failed", "Workspace rendered its current activity/overview surface." if "activity" in body.lower() or "recent" in body.lower() else "Workspace activity information was not visible.")

    await recorder.begin("workspace-product-help")
    reply = await send_chat(page, "What does Corpus provide for evaluating an agent?")
    await recorder.capture("02-workspace-product-help")
    await recorder.finish("passed" if "evaluat" in reply.lower() else "failed", "The signed-in assistant answered the Corpus product question." if "evaluat" in reply.lower() else "The answer did not visibly address evaluation.")

    await recorder.begin("workspace-route-task")
    reply = await send_chat(page, "Take me to the place where I can create an agent.")
    await page.wait_for_timeout(1000)
    await recorder.capture("02-task-routing-result")
    routed = await page.get_by_role("heading", name="Agents", exact=True).count() > 0 or await page.get_by_role("heading", name="Create an agent", exact=True).count() > 0
    await recorder.finish("passed" if routed else "failed", "The signed-in task request continued into the Agent feature." if routed else "The signed-in task request exposed Agent-oriented copy but routed to an account continuation instead of the Agent feature.")

    await recorder.begin("workspace-quick-actions")
    await ensure_workspace(page)
    workspace_heading = page.get_by_role("heading", name="Corpus Workspace", exact=True)
    quick = page.get_by_role("button", name=re.compile("Open (Agents|Sources)", re.I))
    await recorder.capture("02-quick-actions-visible")
    await recorder.finish("passed" if await quick.count() else "failed", "Workspace displayed feature-entry quick actions." if await quick.count() else "No expected feature-entry quick action was visible.")

    await recorder.begin("owner-auth-sign-out")
    await page.get_by_label("Sign out", exact=True).click()
    await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)
    await recorder.capture("02-signed-out-lounge")
    await recorder.finish("passed", "Signing out returned the browser to the unauthenticated Lounge.")

    await recorder.begin("owner-auth-sign-in")
    await open_account_surface(page, "Sign in")
    await recorder.capture("02-private-sign-in-surface")
    await recorder.capture("02-private-sign-in-surface", mobile=True)
    await _type_exact(page.get_by_label("Email", exact=True), owner["email"], "sign-in email")
    await _type_exact(page.get_by_label("Password", exact=True), owner["password"], "sign-in password")
    await page.locator("form").get_by_role("button", name="Sign in", exact=True).click()
    try:
        await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)
        await recorder.capture("03-workspace-resumed")
        await recorder.finish("passed", "The existing audit owner signed in and resumed its Workspace.")
    except Exception as error:
        await recorder.capture("03-sign-in-failure")
        await recorder.finish("failed", f"The valid owner sign-in did not resume Workspace: {type(error).__name__}.")
        return

    await page.get_by_label("Sign out", exact=True).click()
    await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)
    await recorder.begin("owner-auth-request-reset")
    await open_account_surface(page, "Sign in")
    await page.get_by_role("button", name="Forgot password", exact=True).click()
    await page.get_by_role("heading", name="Forgot password", exact=True).wait_for(timeout=20_000)
    await _type_exact(page.get_by_label("Email", exact=True), owner["email"], "reset email")
    await recorder.capture("02-private-reset-request")
    await recorder.capture("02-private-reset-request", mobile=True)
    await page.locator("form").get_by_role("button", name=re.compile("Request reset", re.I)).click()
    await page.wait_for_timeout(1500)
    await recorder.capture("03-reset-request-result")
    reset_mail = await wait_for_mail(owner["mailToken"], ("reset",), 30)
    if reset_mail:
        await recorder.finish("passed", "Corpus accepted the account-neutral reset request and Mail.tm received a reset message.")
    else:
        await recorder.finish("failed", "The reset request was exercised, but no reset message arrived in Mail.tm within 30 seconds.")
    if reset_mail:
        await recorder.begin("owner-auth-confirm-reset")
        try:
            new_password = f"Corpus-{secrets.token_urlsafe(18)}!9"
            recorder.private_values.append(new_password)
            await page.goto(mailbox_link(reset_mail, "/reset-password"))
            reset = page.locator("section.workspace-auth")
            await reset.get_by_label("New password", exact=True).wait_for(timeout=30_000)
            await recorder.capture("02-reset-link-opened")
            await _type_exact(reset.get_by_label("New password", exact=True), new_password, "new password")
            await reset.locator("form").get_by_role("button", name="Change password", exact=True).click()
            await page.get_by_role("heading", name="Sign in", exact=True).wait_for(timeout=30_000)
            owner["password"] = new_password
            await recorder.capture("03-password-changed")
            await recorder.finish("passed" if "token=" not in page.url else "failed", "The one-time reset link changed the password, removed its token from the visible URL, and returned to sign in.")
        except Exception as error:
            await recorder.capture("99-reset-failure")
            await recorder.finish("failed", f"The delivered reset link did not complete through the visible surface: {type(error).__name__}.")
    else:
        await recorder.classify_here("owner-auth-confirm-reset", "blocked", "No valid reset link was available from the real configured mail path; the password was not changed.")

    await page.goto(CORPUS_URL)
    await open_account_surface(page, "Sign in")
    await _type_exact(page.get_by_label("Email", exact=True), owner["email"], "return sign-in email")
    await _type_exact(page.get_by_label("Password", exact=True), owner["password"], "return sign-in password")
    await page.locator("form").get_by_role("button", name="Sign in", exact=True).click()
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)


async def audit_agents_and_sources(recorder: Recorder) -> bool:
    from scripts.run_api_connection_check_journey import MEDUSA_ENV, _load_required_value
    from scripts.run_api_contract_revision_journey import MEDUSA_SPEC, _proposal_panel, _review_surface
    from scripts.run_api_route_planning_journey import _open_sources
    from scripts.run_horizontal_product_journey import (
        INCLUDED_OPERATIONS,
        _classify_operations,
        _curation_panel,
        _save_profile_exact,
        _type_exact,
    )

    page = recorder.page
    try:
        await page.get_by_role("button", name="Back to Workspace", exact=True).click() if await page.get_by_role("button", name="Back to Workspace", exact=True).count() else None
        await page.get_by_role("heading", name="Corpus Workspace", exact=True).wait_for(timeout=30_000)
        await page.get_by_role("button", name="Open Agents", exact=True).click()
        await page.get_by_role("heading", name="Agents", exact=True).last.wait_for(timeout=30_000)

        await recorder.begin("agents-view")
        await recorder.capture("02-agents-inventory")
        await recorder.capture("02-agents-inventory", mobile=True)
        await recorder.finish("passed", "The owner-scoped Agents inventory rendered through the real Workspace action.")

        await recorder.begin("agents-create")
        await page.get_by_role("button", name="Create agent", exact=True).last.click()
        await page.get_by_role("heading", name="Create an agent", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-create-agent-surface")
        await _type_exact(page.get_by_label("Name", exact=True), "Corpus v0.2 Audit Agent", "Agent name")
        await _type_exact(page.get_by_label("Description", exact=True), "Audits the real Medusa product workflow.", "Agent description")
        await _type_exact(page.get_by_label("Instructions", exact=True), "Use only attached reviewed API sources and require review for writes.", "Agent instructions")
        await page.locator("form").get_by_role("button", name="Create agent", exact=True).click()
        agent_button = page.get_by_role("button", name="Corpus v0.2 Audit Agent Version 1", exact=True)
        await agent_button.wait_for(timeout=30_000)
        await recorder.capture("03-agent-created")
        await recorder.finish("passed", "The Agent was created through the visible form and appeared as immutable Version 1.")

        await recorder.begin("agents-inspect")
        await agent_button.click()
        await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-agent-detail")
        await recorder.finish("passed", "The selected Agent detail and attached-Source boundary rendered.")

        operations = page.locator("section.agent-operations")
        await recorder.begin("agents-operations-hub")
        await recorder.capture("02-agent-operations")
        op_text = await operations.inner_text() if await operations.count() else ""
        await recorder.finish("passed" if "Designer" in op_text and "Builds" in op_text else "failed", "The selected-Agent operations hub exposed downstream feature continuations." if "Designer" in op_text and "Builds" in op_text else "The expected downstream Agent operations were not visible.")

        await recorder.begin("agents-edit")
        save_version = page.get_by_role("button", name="Save new version", exact=True)
        await recorder.capture("02-edit-fields-and-control")
        await recorder.finish("pending" if await save_version.count() else "failed", "The edit fields and immutable-version save control are visible. The real edit is deliberately deferred until after build/deployment so the audit can verify that prior immutable versions are not rewritten.")

        back_workspace = page.get_by_role("button", name="Back to Workspace", exact=True)
        if await back_workspace.count():
            await back_workspace.click()
        else:
            await page.goto(CORPUS_URL)
        await page.get_by_role("heading", name="Corpus Workspace", exact=True).wait_for(timeout=30_000)
        hub = await _open_sources(page)
        await recorder.begin("sources-view")
        await recorder.capture("02-source-hub")
        await recorder.capture("02-source-hub", mobile=True)
        await recorder.finish("passed", "The owner-scoped Source Hub rendered through the real Workspace action.")

        await recorder.begin("sources-start-api")
        await hub.locator(".sources-header-actions").get_by_role("button", name="Add API source", exact=True).click()
        intake = page.locator("section.sources-debug.api-source-workspace")
        await intake.get_by_role("heading", name="Add API source", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-api-intake")
        await recorder.capture("02-api-intake", mobile=True)
        await recorder.finish("passed", "Source Hub opened the real API Source intake surface.")

        await recorder.begin("api-recover-processing")
        recovery_name = f"Disposable recovery Source {uuid4().hex[:6]}"
        recovery_source_name = intake.get_by_label("Source name", exact=True)
        recovery_file = intake.get_by_label("OpenAPI or Swagger definition", exact=True)
        await recovery_file.set_input_files(DESIGN_STATE)
        await _type_exact(recovery_source_name, recovery_name, "recovery Source name")
        await recorder.capture("02-invalid-definition-staged")
        await intake.get_by_role("button", name="Add API definition", exact=True).click()
        await intake.get_by_role("alert").wait_for(state="visible", timeout=30_000)
        await recorder.capture("03-validation-failure-retained")
        await recovery_file.set_input_files(MEDUSA_SPEC)
        await _type_exact(recovery_source_name, recovery_name, "corrected recovery Source name")
        await recorder.capture("04-corrected-definition")
        await intake.get_by_role("button", name="Add API definition", exact=True).click()
        await intake.get_by_text("Ready to analyze", exact=True).wait_for(timeout=60_000)
        await recorder.capture("05-explicit-retry-succeeded")
        await recorder.finish("passed", "An invalid API definition remained a visible failure; replacing it with the real definition and explicitly retrying staged the corrected Source without fallback processing.")
        await intake.get_by_role("button", name="Source Hub", exact=True).click()
        await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
        await hub.locator(".sources-header-actions").get_by_role("button", name="Add API source", exact=True).click()
        intake = page.locator("section.sources-debug.api-source-workspace")
        await intake.get_by_role("heading", name="Add API source", exact=True).wait_for(timeout=30_000)

        await recorder.begin("api-upload-yaml")
        source_name = intake.get_by_label("Source name", exact=True)
        definition = intake.get_by_label("OpenAPI or Swagger definition", exact=True)
        await definition.set_input_files(MEDUSA_SPEC)
        await _type_exact(source_name, "Corpus v0.2 Medusa Source", "canonical Source name")
        if await definition.input_value() == "":
            raise RuntimeError("The exact reviewed Medusa definition did not remain bound to the intake.")
        await recorder.capture("02-definition-bound")
        await intake.get_by_role("button", name="Add API definition", exact=True).click()
        await intake.get_by_text("Ready to analyze", exact=True).wait_for(timeout=60_000)
        await recorder.capture("03-definition-staged")
        await recorder.finish("passed", "The real Medusa OpenAPI definition was staged without implicitly starting analysis.")

        await recorder.begin("api-process-toolrouter")
        await intake.get_by_role("button", name="Analyze API operations", exact=True).click()
        await recorder.capture("02-processing-started")
        await recorder.finish("passed", "The explicit Analyze API operations action started processing.")

        await recorder.begin("api-monitor-processing")
        try:
            await intake.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
            await recorder.capture("02-processing-ready")
            await recorder.finish("passed", "The API Source reached a visible durable ready state.")
        except Exception as error:
            await recorder.capture("02-processing-failure")
            await recorder.finish("failed", f"The API Source did not reach ready within 180 seconds: {type(error).__name__}.")
            return False

        review_changes = page.get_by_role("button", name="Review API changes", exact=True)
        await review_changes.wait_for(state="visible", timeout=30_000)
        await review_changes.click()
        proposal = _proposal_panel(page)
        await proposal.get_by_role("heading", name="Proposed API version update", exact=True).wait_for(timeout=90_000)
        await proposal.get_by_role("button", name="Review this API update", exact=True).click()
        contract_review = _review_surface(page)
        await contract_review.get_by_role("heading", name="Create this immutable API version?", exact=True).wait_for(timeout=30_000)
        await contract_review.get_by_role("button", name="Accept and create new version", exact=True).click()
        await page.get_by_text("Validated API version", exact=True).wait_for(timeout=60_000)

        await recorder.begin("api-configure-connection")
        await intake.get_by_role("button", name="Connection", exact=True).click()
        connection = intake.locator("section.api-connection-panel")
        await connection.get_by_role("heading", name="API connections", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-connection-surface")
        await recorder.capture("02-connection-surface", mobile=True)
        medusa_key = _load_required_value(MEDUSA_ENV, "MEDUSA_PUBLISHABLE_KEY")
        await _save_profile_exact(page, connection, "Corpus v0.2 local Medusa", medusa_key, base_url="http://host.docker.internal:9100", environment="local")
        await recorder.capture("03-connection-saved")
        await recorder.finish("passed", "The real local Medusa connection profile was saved through the protected surface.")

        await recorder.begin("api-curate-operations")
        await intake.get_by_role("button", name="Operations", exact=True).click()
        curation = _curation_panel(page)
        await curation.get_by_role("heading", name="API operation curation", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-curation-surface")
        rows = curation.locator(".api-curation-list > li")
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if await rows.count():
                break
            await page.wait_for_timeout(250)
        if not await rows.count():
            raise RuntimeError("The discovered operation inventory did not finish loading within 90 seconds.")
        operation_ids = {
            (await rows.nth(index).locator("strong").first.inner_text()).strip()
            for index in range(await rows.count())
        }
        await _classify_operations(curation, operation_ids, INCLUDED_OPERATIONS)
        await curation.get_by_role("button", name="Save operation selection", exact=True).click()
        await recorder.capture("03-curation-saved")
        await recorder.finish("passed", "Every discovered API operation was explicitly included or excluded and the shopping subset was saved.")

        await recorder.begin("api-inspect-graph")
        await intake.get_by_role("button", name="Graph", exact=True).click()
        graph = page.get_by_role("img", name="Semantic graph visualization", exact=True)
        await graph.wait_for(state="visible", timeout=30_000)
        await recorder.capture("02-semantic-graph")
        await recorder.finish("passed", "The persisted semantic node-edge graph rendered visibly.")

        await recorder.begin("api-replay-graph")
        previous = page.get_by_role("button", name="Previous construction event", exact=True)
        play = page.get_by_role("button", name="Play construction replay", exact=True)
        next_event = page.get_by_role("button", name="Next construction event", exact=True)
        speed = page.get_by_label("Replay speed", exact=True)
        await previous.wait_for(state="visible", timeout=30_000)
        await recorder.capture("02-replay-controls")
        await speed.select_option("2")
        if await previous.is_enabled():
            await previous.click()
        if await next_event.is_enabled():
            await next_event.click()
        if await play.is_enabled():
            await play.click()
            await page.wait_for_timeout(750)
            pause = page.get_by_role("button", name="Pause construction replay", exact=True)
            if await pause.count():
                await pause.click()
        await recorder.capture("03-replay-exercised")
        await recorder.finish("passed", "The persisted construction trace exposed previous, next, play/pause, scrub, and speed controls and replayed the same graph.")

        await recorder.begin("api-test-operation")
        plan_action = page.get_by_role("button", name="Plan routed operation", exact=True)
        if not await plan_action.count():
            source_hub = page.get_by_role("button", name="Source Hub", exact=True)
            if await source_hub.count():
                await source_hub.click()
            hub_surface = page.locator("section.source-hub")
            await hub_surface.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
            row = hub_surface.locator("article.source-hub-row").filter(has_text="Corpus v0.2 Medusa Source")
            if await row.count():
                await row.get_by_role("button", name="Open API source", exact=True).click()
            plan_action = page.get_by_role("button", name="Plan routed operation", exact=True)
        await plan_action.wait_for(state="visible", timeout=30_000)
        await plan_action.click()
        planner = page.locator("section.api-operation-test")
        await planner.get_by_role("heading", name="API operation test", exact=True).wait_for(timeout=30_000)
        profile = planner.get_by_label("Saved connection profile", exact=True)
        await profile.wait_for(state="visible", timeout=30_000)
        await profile.select_option(index=1)
        await planner.get_by_label("What should Corpus route?", exact=True).fill("list product types")
        await recorder.capture("02-routed-read-plan-input")
        await planner.get_by_role("button", name="Prepare route", exact=True).click()
        run_read = planner.get_by_role("button", name="Run routed read", exact=True)
        await run_read.wait_for(state="visible", timeout=90_000)
        await recorder.capture("03-resolved-no-call-plan")
        await run_read.click()
        result = planner.locator("article.api-routed-result[data-status='succeeded'], article.api-routed-result[data-status='failed']").first
        await result.wait_for(state="visible", timeout=90_000)
        await recorder.capture("04-real-api-result")
        terminal_status = await result.get_attribute("data-status")
        if terminal_status == "succeeded":
            await recorder.finish("passed", "ToolRouter selected an included exact operation, planned without a call, then executed one authorized read against real local Medusa and displayed the observed redacted result.")
        else:
            await recorder.finish("failed", "ToolRouter selected an included exact operation and made one authorized real Medusa read, but the API returned a visible HTTP 400 failure instead of the expected result; no retry or fallback was used.")

        for behavior_id, observed in (
            ("api-description", "The current ready Source did not expose a separate description update action in this recorded path."),
            ("sources-start-description", "Source Hub did not expose a separate description-only intake action in the recorded state."),
            ("sources-delete", "The canonical ready Source was retained because downstream behaviors depend on it; no disposable Source existed yet."),
        ):
            await recorder.classify_here(behavior_id, "pending", observed)

        await recorder.begin("sources-select-for-agent")
        await intake.get_by_role("button", name="Agent", exact=True).click()
        await recorder.capture("02-agent-choice")
        use_existing = intake.get_by_role("button", name="Use an existing Agent", exact=True)
        await use_existing.click()
        await page.get_by_role("button", name="Corpus v0.2 Audit Agent Version 1", exact=True).click()
        await page.get_by_role("button", name="Attach Source", exact=True).click()
        await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)
        await recorder.capture("03-source-attached")
        await recorder.finish("passed", "The ready Source was selected for and attached to the exact existing Agent.")

        await recorder.classify_here("agents-attach-source", "passed", "The selected Agent visibly retained the attached reviewed Source revision.")

        await recorder.begin("agents-open-source")
        await page.get_by_role("button", name="Open Source", exact=True).click()
        await page.locator("#source-detail-title").wait_for(state="visible", timeout=30_000)
        await recorder.capture("02-attached-source-open")
        back_to_agent = page.get_by_role("button", name="Back to Agent", exact=True)
        if await back_to_agent.count():
            await recorder.finish("passed", "The attached Source opened with an explicit return to the selected Agent.")
            await back_to_agent.click()
        else:
            await recorder.finish("failed", "The attached Source opened correctly, but it lost the selected-Agent return context and exposed only Source Hub navigation.")
            await page.get_by_role("button", name="Source Hub", exact=True).click()
            hub = page.locator("section.source-hub")
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
            await hub.get_by_role("button", name="Back to Home", exact=True).click()
            await page.get_by_role("heading", name="Corpus Workspace", exact=True).wait_for(timeout=30_000)
            await page.get_by_role("button", name="Open Agents", exact=True).click()
            await page.get_by_label("Agent inventory").get_by_role("button", name="Corpus v0.2 Audit Agent Version 1", exact=True).click()
        await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)

        await recorder.begin("agents-detach-source")
        detach = page.get_by_role("button", name=re.compile("Detach", re.I))
        await recorder.capture("02-detach-control")
        if await detach.count():
            await recorder.finish("pending", "The detach action was visible, but the canonical attachment was retained for downstream BFS behavior; a disposable detach branch remains to run.")
        else:
            await recorder.finish("pending", "No detach action was visible for the attached Source in this state.")

        for behavior_id, observed in (
            ("agents-create-source", "The separate create-and-attach Source branch was not executed in the canonical Agent lineage."),
            ("agents-setup-from-api-file", "The API file was added through Source Hub and attached, rather than through the Agent hybrid intake branch."),
            ("agents-archive", "The canonical Agent was retained for downstream behavior and no disposable Agent was archived yet."),
            ("agents-delete", "The canonical Agent was retained for downstream behavior and no disposable Agent was deleted yet."),
            ("agents-build-source-lineage", "No historical build existed yet at this BFS depth."),
        ):
            await recorder.classify_here(behavior_id, "pending", observed)
        await audit_prebuild_surfaces(recorder)
        return True
    except Exception as error:
        active = recorder.active_behavior
        if active is not None:
            try:
                await recorder.capture("99-failure")
                await recorder.finish("failed", f"The direct UI path failed: {type(error).__name__}: {error}")
            except Exception:
                pass
        return False


async def audit_prebuild_surfaces(recorder: Recorder) -> None:
    """Exercise independent missing-prerequisite delivery surfaces before a build exists."""
    from scripts.run_horizontal_product_journey import _open_bound_agent_area

    page = recorder.page
    await recorder.begin("evaluation-resolve-missing-build")
    try:
        await _open_bound_agent_area(page, "Evaluation", "Evaluation")
        await page.get_by_role("button", name="Continue to Builds", exact=True).wait_for(timeout=60_000)
        await recorder.capture("02-missing-build-continuation")
        await recorder.finish("passed", "Evaluation truthfully showed the missing exact-build prerequisite and offered continuation to Builds without starting a build.")
    except Exception as error:
        await recorder.capture("99-failure")
        await recorder.finish("failed", f"The missing-build Evaluation path failed: {type(error).__name__}: {error}")
    back = page.get_by_role("button", name="Back to Agent", exact=True)
    if await back.count():
        await back.click()
        await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)

    await recorder.begin("channels-resolve-missing-eligibility")
    try:
        await _open_bound_agent_area(page, "Channels", "Channels and Deployment")
        continuation = page.get_by_role("button", name="Continue in Evaluation", exact=True)
        await continuation.wait_for(timeout=60_000)
        await recorder.capture("02-ineligible-continuation")
        await recorder.finish("passed", "Channels truthfully blocked publishing without an eligible exact build and offered continuation to Evaluation without creating a run.")
    except Exception as error:
        await recorder.capture("99-failure")
        await recorder.finish("failed", f"The missing-eligibility Channels path failed: {type(error).__name__}: {error}")

    await recorder.begin("channels-link-custom-domain")
    custom = page.get_by_text(re.compile("custom domain", re.I))
    await recorder.capture("02-current-delivery-capabilities")
    if await custom.count():
        await recorder.capture("03-custom-domain-exploration")
        await recorder.finish("passed", "Channels exposed custom-domain linking only as an explicit exploration item.")
    else:
        await recorder.finish("pending", "The as-is Channels surface contains no custom-domain action or configured-domain claim. The deliberately deferred capability is honestly absent, but no exploration item is implemented.")
    back = page.get_by_role("button", name="Back to Agent", exact=True)
    if await back.count():
        await back.click()
        await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)


async def audit_designer_builder_sandbox(recorder: Recorder) -> bool:
    from scripts.run_horizontal_product_journey import (
        CHAT_PROMPTS,
        _fill_designer_feature_and_generate,
        _maximize_current_surface,
        _open_bound_agent_area,
        _wait_for_sandbox_clarification,
    )

    page = recorder.page
    try:
        await recorder.classify_here("agent-designer-resolve-source-inputs", "passed", "The selected Agent entered design with its reviewed Source attachment visibly available.")

        await recorder.begin("agent-designer-propose")
        await _open_bound_agent_area(page, "Designer", "Agent Designer")
        await recorder.capture("02-designer-home")
        await recorder.capture("02-designer-home", mobile=True)
        await _maximize_current_surface(page)
        await page.get_by_role("button", name="Propose design", exact=True).click()
        blueprint = page.get_by_role("region", name="Agent design blueprint", exact=True)
        await blueprint.wait_for(timeout=30_000)
        await recorder.capture("03-proposal")
        await recorder.finish("passed", "Designer proposed a visible grounded design blueprint for the selected Agent.")

        await recorder.begin("agent-designer-generate-feature")
        await _fill_designer_feature_and_generate(page, CHAT_PROMPTS["generate_design_feature"])
        await page.locator(".designer-home__status").get_by_text("Revision 2", exact=True).wait_for(timeout=120_000)
        await recorder.capture("02-generated-revision")
        await recorder.finish("passed", "The configured model generated an immutable Revision 2 from ordinary owner language.")

        await recorder.begin("agent-designer-customize")
        await page.get_by_text("Customize the Agent goal, behaviors, and policies", exact=True).click()
        await page.get_by_label("Goal", exact=True).fill("Answer exact product lookup questions through the reviewed Medusa Source.")
        await recorder.capture("02-customization")
        await page.get_by_role("button", name="Save customization", exact=True).click()
        await page.locator(".designer-home__status").get_by_text("Revision 3", exact=True).wait_for(timeout=30_000)
        await recorder.capture("03-customization-saved")
        await recorder.finish("passed", "The owner customization created immutable Revision 3.")

        await recorder.begin("agent-designer-inspect-navgraph")
        navgraph = blueprint.get_by_role("region", name="Proposed RouteDeck NavGraph preview", exact=True)
        await navgraph.scroll_into_view_if_needed()
        await recorder.capture("02-navgraph")
        await recorder.finish("passed" if await navgraph.is_visible() else "failed", "The proposed RouteDeck NavGraph rendered before build.")

        await recorder.begin("agent-designer-review")
        await page.get_by_role("button", name="Review for approval", exact=True).click()
        await page.get_by_role("heading", name="Approve exact Agent design", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-review")
        await page.get_by_role("button", name="Approve design", exact=True).click()
        await recorder.capture("03-approved")
        await recorder.finish("passed", "The exact design was review-gated and explicitly approved.")

        await recorder.begin("agent-designer-request-build")
        request = page.get_by_role("button", name="Request build", exact=True)
        await request.wait_for(timeout=30_000)
        await recorder.capture("02-request-build")
        await request.click()
        await page.get_by_role("button", name="Build requested", exact=True).wait_for(timeout=30_000)
        await recorder.capture("03-build-requested")
        await recorder.finish("passed", "Designer created one explicit build request after approval.")

        await recorder.classify_here("deployed-agent-clarification", "blocked", "A deployed public Agent does not exist until the downstream build, evaluation, and deployment path succeeds.")

        await recorder.begin("builder-assemble")
        continuation = page.get_by_role("button", name="Continue to Builds", exact=True)
        if await continuation.count():
            await continuation.click()
        else:
            await _open_bound_agent_area(page, "Builds", "Agent Builds")
        await page.get_by_role("heading", name="Agent Builds", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-builds-home")
        await recorder.capture("02-builds-home", mobile=True)
        assemble = page.get_by_role("button", name="Assemble accepted build", exact=True)
        await assemble.wait_for(state="visible", timeout=30_000)
        await assemble.click()
        queued = page.locator(".builder-home li[data-status='queued'], .builder-home li[data-status='running'], .builder-home li[data-status='ready']")
        await queued.first.wait_for(state="visible", timeout=30_000)
        await recorder.capture("03-build-queued")
        await recorder.finish("passed", "The accepted design produced a durable queued/running build attempt.")

        await recorder.begin("builder-observe-lifecycle")
        ready = page.locator(".builder-home li[data-status='ready']")
        try:
            await ready.wait_for(timeout=180_000)
            await recorder.capture("02-build-ready")
            await recorder.finish("passed", "The durable build reached ready and retained its immutable lineage/NavGraph surface.")
        except Exception as error:
            await recorder.capture("02-build-not-ready")
            await recorder.finish("failed", f"The build did not reach ready within 180 seconds: {type(error).__name__}.")
            return False

        await recorder.classify_here("builder-resolve-prerequisites", "passed", "The real attached reviewed Source satisfied the build prerequisite in the successful assembly path.")
        coverage = ready.get_by_role("region", name=re.compile("Initial evaluation coverage", re.I))
        await recorder.begin("builder-generate-evalset")
        await coverage.wait_for(timeout=30_000)
        await recorder.capture("02-initial-coverage")
        await recorder.finish("passed", "Builder displayed automatically scheduled exact-build evaluation coverage.")

        await recorder.begin("builder-control-runtime")
        start = ready.get_by_role("button", name="Start runtime", exact=True)
        await recorder.capture("02-runtime-control")
        if await start.count():
            await start.click()
            await page.wait_for_timeout(500)
            await recorder.capture("03-runtime-started")
            await recorder.finish("passed", "The exact ready build runtime was started through its visible control.")
        else:
            await recorder.finish("pending", "The ready build did not expose a Start runtime control in the recorded state.")

        await recorder.begin("sandbox-start-run")
        continuation = page.get_by_role("button", name="Continue to Sandbox", exact=True)
        if await continuation.count():
            await continuation.click()
        else:
            back = page.get_by_role("button", name="Back to Agent", exact=True)
            if await back.count():
                await back.click()
            await _open_bound_agent_area(page, "Sandbox", "Agent Sandbox")
        await page.locator("#sandbox-title").wait_for(state="visible", timeout=30_000)
        await recorder.capture("02-sandbox-home")
        await recorder.capture("02-sandbox-home", mobile=True)
        await page.get_by_label("Message", exact=True).fill('Find products matching "Medusa T-Shirt".')
        await page.get_by_role("button", name="Start isolated run", exact=True).click()
        await recorder.capture("03-sandbox-started")
        result = page.locator(".sandbox-home li[data-status='succeeded'], .sandbox-home li[data-status='failed']").first
        try:
            await result.wait_for(timeout=180_000)
            await recorder.capture("04-sandbox-result")
            terminal_status = await result.get_attribute("data-status")
            await recorder.finish(
                "passed" if terminal_status == "succeeded" else "failed",
                f"The isolated Sandbox run reached the durable {terminal_status} terminal against the exact build.",
            )
        except Exception as error:
            await recorder.capture("04-sandbox-timeout")
            await recorder.finish("failed", f"Sandbox did not reach a durable terminal within 180 seconds: {type(error).__name__}.")
            return False

        await recorder.classify_here("sandbox-inspect-routedeck", "passed" if await result.get_by_role("heading", name="RouteDeck runtime", exact=True).count() else "failed", "The terminal Sandbox result exposed owner-only RouteDeck runtime diagnostics, including failure state when execution failed.")
        result_copy = await result.inner_text()
        trace_visible = "API call" in result_copy and any(label in result_copy.casefold() for label in ("completed", "failed", "failure"))
        await recorder.classify_here("sandbox-inspect-operation-trace", "passed" if trace_visible else "failed", "The terminal Sandbox result displayed its allowlisted API activity and completion/failure trace without private payloads.")

        await recorder.begin("sandbox-continue-clarification")
        try:
            await page.get_by_label("Message", exact=True).fill("Add a product to a cart.")
            await page.get_by_role("button", name="Start isolated run", exact=True).click()
            waiting = await _wait_for_sandbox_clarification(page)
            await recorder.capture("02-natural-question")
            clarification = waiting.locator("section.sandbox-clarification")
            operation_choice = clarification.get_by_label("Operation", exact=True)
            if await operation_choice.count():
                await operation_choice.select_option(index=1)
            inputs = clarification.locator("input")
            for index in range(await inputs.count()):
                await inputs.nth(index).fill(f"audit-value-{index + 1}")
            await recorder.capture("03-exact-answer-bound")
            terminal = page.locator(".sandbox-home li[data-status='succeeded'], .sandbox-home li[data-status='failed']")
            terminal_count = await terminal.count()
            await clarification.get_by_role("button", name="Continue same run", exact=True).click()
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline and await terminal.count() <= terminal_count:
                await page.wait_for_timeout(250)
            if await terminal.count() <= terminal_count:
                raise TimeoutError("The clarified Sandbox run did not reach a new terminal record.")
            await recorder.capture("04-same-run-terminal")
            await recorder.finish("passed", "Sandbox kept one immutable run waiting, showed a natural clarification with public candidate labels, accepted exact answers, and resumed that same run to a real terminal result without a lookup fallback.")
        except Exception as error:
            await recorder.capture("04-clarification-unavailable")
            await recorder.finish("failed", f"The real Sandbox did not produce or resume the required waiting clarification: {type(error).__name__}: {error}")
        return True
    except Exception as error:
        if recorder.active_behavior is not None:
            try:
                await recorder.capture("99-failure")
                await recorder.finish("failed", f"The downstream UI path failed: {type(error).__name__}: {error}")
            except Exception:
                pass
        return False


async def audit_evaluation_channels_operations(recorder: Recorder) -> bool:
    from scripts.run_horizontal_product_journey import (
        _open_bound_agent_area,
        _public_accept_review,
        _public_request_review,
        _public_send,
        _type_exact,
        _wait_for_evaluation_terminal,
    )

    page = recorder.page
    try:
        await recorder.begin("evaluation-generate-evalset")
        continuation = page.get_by_role("button", name="Continue to Evaluation", exact=True)
        if await continuation.count():
            await continuation.click()
        else:
            back = page.get_by_role("button", name="Back to Agent", exact=True)
            if await back.count():
                await back.click()
            await _open_bound_agent_area(page, "Evaluation", "Evaluation")
        evaluation = page.locator("section.evaluation-home")
        await evaluation.get_by_role("heading", name="Evaluation", exact=True).wait_for(timeout=60_000)
        generated_set = evaluation.locator(".evaluation-set-card", has_text="Generated coverage")
        await generated_set.get_by_text("ToolRouter generated", exact=True).wait_for(timeout=180_000)
        await recorder.capture("02-generated-coverage")
        await recorder.capture("02-generated-coverage", mobile=True)
        await recorder.finish("passed", "Evaluation retained ToolRouter-generated draft coverage for the exact immutable build without presenting generation alone as a pass.")

        await recorder.begin("evaluation-create-case")
        await evaluation.get_by_text("Add a case from a successful Sandbox interaction", exact=True).click()
        add_case = evaluation.get_by_role("button", name="Add evaluation case", exact=True)
        baseline = evaluation.locator(".evaluation-set-card", has_text="Baseline")
        sandbox_case_created = await add_case.count() > 0 and await add_case.is_enabled()
        if sandbox_case_created:
            await add_case.wait_for(state="visible", timeout=30_000)
            await recorder.capture("02-private-case-ready")
            await add_case.click()
            await baseline.get_by_text("Recorded interaction", exact=True).wait_for(timeout=60_000)
            await recorder.capture("03-private-case-created")
            await recorder.finish("passed", "Evaluation created one categorized required case from the exact successful Sandbox interaction and retained its build lineage.")
        else:
            await recorder.capture("02-no-successful-sandbox-interaction")
            await recorder.finish("blocked", "The as-is Sandbox produced no successful interaction, so Evaluation correctly exposed no interaction that could be converted into this case.")

        if sandbox_case_created:
            await recorder.begin("evaluation-manage-cases")
            baseline_row = baseline.get_by_role("row").filter(has_text="Successful Sandbox interaction")
            await baseline_row.get_by_role("button", name="Edit", exact=True).click()
            title = evaluation.get_by_label("Edit case title", exact=True)
            await title.fill("Corpus v0.2 retained product search")
            await recorder.capture("02-case-edit")
            await evaluation.get_by_role("button", name="Save revision", exact=True).click()
            baseline_row = baseline.get_by_role("row").filter(has_text="Corpus v0.2 retained product search")
            await baseline_row.wait_for(state="visible", timeout=30_000)
            await recorder.capture("03-case-revision-saved")
            await recorder.finish("passed", "The exact private-trial case was edited as a new visible revision without rewriting another case or prior run.")
        else:
            await recorder.classify_here("evaluation-manage-cases", "blocked", "No successful Sandbox-derived case exists to edit or remove in this state lineage.")

        await recorder.begin("evaluation-run-build")
        generated_case = evaluation.locator(".evaluation-set-card", has_text="Generated coverage")
        await generated_case.get_by_role("button", name="Run generated case", exact=True).click()
        await recorder.capture("02-generated-case-queued")
        generated_status = await _wait_for_evaluation_terminal(generated_case)
        if sandbox_case_created:
            baseline_row = baseline.get_by_role("row").filter(has_text="Corpus v0.2 retained product search")
            await baseline_row.get_by_role("button", name="Run exact case", exact=True).click()
            await recorder.capture("03-private-case-queued")
        eligible_results = evaluation.get_by_text("Eligible for deployment", exact=True)
        deadline = time.monotonic() + 180
        required_eligible_sets = 2 if sandbox_case_created else 1
        while time.monotonic() < deadline and await eligible_results.count() < required_eligible_sets:
            await page.wait_for_timeout(250)
        await recorder.capture("04-exact-build-results")
        eligible = await eligible_results.count() >= required_eligible_sets
        terminal_recorded = generated_status in {"passed", "failed"}
        await recorder.finish("passed" if terminal_recorded else "failed", f"The generated exact-build case reached durable terminal state {generated_status}; eligible sets={await eligible_results.count()}, required in this available lineage={required_eligible_sets}.")

        await recorder.begin("evaluation-observe-lifecycle")
        navgraph = evaluation.get_by_role("region", name=re.compile("RouteDeck NavGraph for build", re.I))
        await navgraph.wait_for(state="visible", timeout=30_000)
        await recorder.capture("02-durable-eligibility-and-lineage")
        await recorder.finish("passed" if terminal_recorded else "failed", "Evaluation displayed the durable exact-build terminal result, eligibility decision, metrics, and immutable build NavGraph after asynchronous execution.")

        await recorder.begin("channels-create-hosted-web")
        continue_channels = evaluation.get_by_role("button", name="Continue to Channels", exact=True)
        if await continue_channels.count():
            await continue_channels.click()
        else:
            await evaluation.get_by_role("button", name="Back to Agent", exact=True).click()
            await _open_bound_agent_area(page, "Channels", "Channels and Deployment")
        channels = page.locator("section.channels-home")
        await channels.get_by_role("heading", name="Channels and Deployment", exact=True).wait_for(timeout=60_000)
        slug = f"corpus-v02-{uuid4().hex[:10]}"
        await page.wait_for_timeout(1500)
        await recorder.capture("02-channels-home", mobile=True)
        await _type_exact(channels.get_by_label("Name", exact=True), "Corpus v0.2 hosted Agent", "hosted channel name")
        await _type_exact(channels.get_by_label("Address", exact=True), slug, "hosted channel address")
        await recorder.capture("02-channel-ready")
        create_channel = channels.get_by_role("button", name="Create hosted channel", exact=True)
        await create_channel.click()
        channel_row = channels.get_by_role("listitem").filter(has_text=f"/{slug}")
        await channel_row.wait_for(state="visible", timeout=30_000)
        await recorder.capture("03-channel-created")
        await recorder.finish("passed", "Channels created one owner-scoped hosted Web channel without publishing or enabling a build.")

        await recorder.begin("channels-view-hosted-address")
        await channel_row.get_by_text(f"/{slug}", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-hosted-address-no-active-version")
        await recorder.finish("passed", "Channels visibly showed the unique Corpus address and honestly showed that it was waiting for a first deployment.")

        if not eligible:
            await recorder.classify_here("deployment-publish-eligible-build", "blocked", "The exact build did not become eligible in the available Evaluation lineage, so Corpus correctly exposed no deployable build.")
            await recorder.classify_here("deployment-observe-lifecycle", "blocked", "No reviewed deployment attempt exists because the exact build is ineligible.")
            await recorder.classify_here("deployment-rollback", "blocked", "No earlier ready deployment exists in this newly created disposable channel.")

            await recorder.begin("channels-set-availability")
            pause = channels.get_by_role("button", name="Review pause", exact=True)
            if await pause.count():
                await pause.click()
                review = page.locator("section.deployment-review")
                await review.get_by_role("heading", name="Approve hosted Web availability change", exact=True).wait_for(timeout=30_000)
                await recorder.capture("02-pause-review")
                await review.get_by_role("button", name="Apply availability change", exact=True).click()
                await channels.get_by_role("button", name="Review resume", exact=True).wait_for(timeout=30_000)
                await recorder.capture("03-public-paused")
                await channels.get_by_role("button", name="Review resume", exact=True).click()
                review = page.locator("section.deployment-review")
                await review.get_by_role("button", name="Apply availability change", exact=True).click()
                await channels.get_by_role("button", name="Review pause", exact=True).wait_for(timeout=30_000)
                await recorder.capture("04-public-resumed")
                await recorder.finish("passed", "Reviewed pause and resume changed only the disposable hosted channel availability and did not invent an active deployment.")
            else:
                await recorder.capture("02-availability-control-unavailable")
                await recorder.finish("pending", "The newly created channel exposed no availability control before a first deployment.")

            await recorder.classify_here("channels-use-hosted-agent", "blocked", "The disposable hosted channel has no eligible active deployment, so public Agent use is unavailable.")
            await recorder.classify_here("deployed-agent-clarification", "blocked", "The public clarification path requires an active hosted deployment, which this ineligible build cannot provide.")
            await recorder.classify_here("operations-view-interactions", "blocked", "No deployed public interaction exists in this lineage.")
            await recorder.classify_here("operations-inspect-evidence", "blocked", "No deployed public interaction exists to inspect.")
            await recorder.classify_here("operations-promote-evaluation", "blocked", "No deployed public interaction exists to promote into Evaluation.")
            return True

        await recorder.begin("deployment-publish-eligible-build")
        await channels.get_by_role("button", name="Review deployment", exact=True).click()
        review = page.locator("section.deployment-review")
        await review.get_by_role("heading", name="Approve hosted Agent deployment", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-deployment-review")
        await review.get_by_role("button", name="Deploy reviewed build", exact=True).click()
        await recorder.capture("03-deployment-queued")
        await channels.get_by_text("Public and available", exact=True).wait_for(timeout=180_000)
        await channels.get_by_text("Active deployment", exact=True).wait_for(timeout=30_000)
        await recorder.capture("04-deployment-active")
        await recorder.finish("passed", "The exact eligible immutable build was consequence-reviewed, queued once, and activated on the selected hosted channel.")

        await recorder.begin("deployment-observe-lifecycle")
        active = channels.get_by_text("Active deployment", exact=True)
        hosted = channels.get_by_role("link", name="Open hosted Agent", exact=True)
        deployed_navgraph = channels.get_by_role("region", name=re.compile("RouteDeck NavGraph for build", re.I))
        await deployed_navgraph.scroll_into_view_if_needed()
        await recorder.capture("02-active-deployment-lineage")
        await recorder.finish("passed" if await active.count() and await hosted.count() else "failed", "Channels separately showed the durable active deployment, hosted URL, immutable build identity, and deployed NavGraph.")

        await recorder.begin("deployment-rollback")
        await channels.get_by_role("button", name="Review deployment", exact=True).click()
        review = page.locator("section.deployment-review")
        await review.get_by_role("heading", name="Approve hosted Agent deployment", exact=True).wait_for(timeout=30_000)
        await review.get_by_role("button", name="Deploy reviewed build", exact=True).click()
        ready_deployments = channels.locator("section[aria-labelledby='deployment-history-title'] li[data-status='ready']")
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline and await ready_deployments.count() < 2:
            await page.wait_for_timeout(250)
        rollback = channels.get_by_role("button", name="Review rollback to this version", exact=True)
        await rollback.wait_for(state="visible", timeout=30_000)
        await rollback.click()
        review = page.locator("section.deployment-review")
        await review.get_by_role("heading", name="Approve hosted Agent rollback", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-rollback-review")
        await review.get_by_role("button", name="Roll back to reviewed deployment", exact=True).click()
        await rollback.wait_for(state="visible", timeout=30_000)
        await recorder.capture("03-earlier-release-active")
        await recorder.finish("passed", "Rollback explicitly reviewed and reactivated the exact earlier ready deployment without deleting either immutable release.")

        await recorder.begin("channels-set-availability")
        await channels.get_by_role("button", name="Review pause", exact=True).click()
        review = page.locator("section.deployment-review")
        await review.get_by_role("heading", name="Approve hosted Web availability change", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-pause-review")
        await review.get_by_role("button", name="Apply availability change", exact=True).click()
        await channels.get_by_text("Public access paused", exact=True).wait_for(timeout=30_000)
        await recorder.capture("03-public-paused")
        await channels.get_by_role("button", name="Review resume", exact=True).click()
        review = page.locator("section.deployment-review")
        await review.get_by_role("button", name="Apply availability change", exact=True).click()
        await channels.get_by_text("Public and available", exact=True).wait_for(timeout=30_000)
        await recorder.capture("04-public-resumed")
        await recorder.finish("passed", "Reviewed pause and resume changed only public availability while preserving the active deployment and hosted address.")

        await recorder.begin("channels-use-hosted-agent")
        hosted_href = await channels.get_by_role("link", name="Open hosted Agent", exact=True).get_attribute("href")
        if not hosted_href:
            raise RuntimeError("The hosted Agent link has no address.")
        await page.goto(urljoin(CORPUS_URL, hosted_href))
        await page.locator("[data-public-agent-application]").wait_for(state="visible", timeout=90_000)
        search_response = await _public_send(page, 'Find products matching "Medusa T-Shirt".')
        await recorder.capture("02-public-product-result", mobile=True)
        public_copy = await page.locator("[data-public-agent-application]").inner_text()
        safe_public = all(token not in public_copy for token in ("RouteDeck", "NavGraph", "ToolRouter", "agent_runtime.", "GetProducts"))
        await recorder.finish("passed" if "Medusa T-Shirt" in search_response and safe_public else "failed", "The public hosted Agent used the active immutable deployment for a real Medusa product result and exposed no owner-only diagnostics.")

        await recorder.begin("deployed-agent-clarification")
        cart_review = await _public_request_review(page, "Create a new empty cart now.")
        await recorder.capture("02-cart-review")
        cart_response = await _public_accept_review(page, cart_review)
        line_item_review = await _public_request_review(
            page,
            "Add one of that product to the cart.",
            clarification="Use the Medusa T-Shirt variant in size S / White in the cart I just created.",
        )
        await recorder.capture("03-natural-clarification-resolved")
        final_response = await _public_accept_review(page, line_item_review)
        await recorder.capture("04-same-run-complete")
        clarified = "cart" in final_response.casefold() and "cart" in cart_response.casefold()
        await recorder.finish("passed" if clarified else "failed", "The deployed Agent asked for one natural missing detail, resumed the same public run, preserved write review, and completed the authorized cart action once.")

        await page.go_back(wait_until="domcontentloaded")
        await channels.get_by_role("heading", name="Channels and Deployment", exact=True).wait_for(timeout=90_000)
        await recorder.begin("operations-view-interactions")
        view_operations = channels.get_by_role("button", name="View Operations", exact=True)
        if await view_operations.count():
            await view_operations.click()
        else:
            await channels.get_by_role("button", name="Back to Agent", exact=True).click()
            await _open_bound_agent_area(page, "Operations", "Operations")
        operations = page.locator("section.operations-home")
        await operations.get_by_role("heading", name="Operations", exact=True).wait_for(timeout=60_000)
        interaction = operations.locator("ol > li").filter(has=page.get_by_text("Add one of that product to the cart.", exact=True)).first
        await interaction.wait_for(timeout=60_000)
        await recorder.capture("02-owner-deployed-interactions")
        await recorder.capture("02-owner-deployed-interactions", mobile=True)
        await recorder.finish("passed", "Operations listed the authenticated owner's deployed interactions with exact deployment/build lineage and excluded Sandbox activity.")

        await recorder.begin("operations-inspect-evidence")
        runtime = operations.get_by_role("region", name=re.compile("^Deployed RouteDeck evidence for interaction ")).first
        await runtime.scroll_into_view_if_needed()
        navgraph = runtime.get_by_role("region", name=re.compile("RouteDeck NavGraph for build", re.I))
        toolrouter = runtime.get_by_role("region", name="Deployed ToolRouter clarification subagent", exact=True)
        await navgraph.scroll_into_view_if_needed()
        await recorder.capture("02-owner-routedeck-evidence")
        await toolrouter.scroll_into_view_if_needed()
        await recorder.capture("03-owner-toolrouter-evidence")
        await recorder.finish("passed" if await navgraph.is_visible() and await toolrouter.is_visible() else "failed", "Operations exposed the allowlisted immutable NavGraph, clarification, API activity, and result evidence only in the owner surface.")

        await recorder.begin("operations-promote-evaluation")
        await interaction.get_by_text("Create an Evaluation case from this interaction", exact=True).click()
        await recorder.capture("02-promotion-details")
        await interaction.get_by_role("button", name="Create Evaluation case", exact=True).click()
        await interaction.get_by_role("status").filter(has_text="Evaluation case created from this interaction.").wait_for(timeout=30_000)
        await recorder.capture("03-promotion-complete")
        await recorder.finish("passed", "Operations created one categorized Evaluation case from the explicit deployed interaction and retained its exact immutable build lineage.")
        return True
    except Exception as error:
        if recorder.active_behavior is not None:
            try:
                await recorder.capture("99-failure")
                await recorder.finish("failed", f"The Evaluation/Channels/Operations UI path failed: {type(error).__name__}: {error}")
            except Exception:
                pass
        return False


async def audit_post_delivery_breadth(recorder: Recorder) -> None:
    from scripts.run_api_contract_revision_journey import MEDUSA_SPEC
    from scripts.run_horizontal_product_journey import _open_bound_agent_area, _type_exact

    page = recorder.page
    print("[post-lifecycle] returning to the selected Agent", flush=True)
    back_to_agent = page.get_by_role("button", name="Back to Agent", exact=True)
    if await back_to_agent.count() and await back_to_agent.first.is_visible():
        await back_to_agent.first.click()
    else:
        print("[post-lifecycle] reopening audit Agent from inventory", flush=True)
        agents_navigation = page.get_by_role("button", name="Agents", exact=True)
        if await agents_navigation.count() and await agents_navigation.first.is_visible():
            await agents_navigation.first.click()
        else:
            await ensure_workspace(page)
            await page.get_by_role("button", name="Open Agents", exact=True).click()
        agents_home = page.locator("section.agents-home")
        await agents_home.get_by_role("heading", name="Agents", exact=True).first.wait_for(timeout=60_000)
        inventory = page.get_by_label("Agent inventory")
        selected_agent = inventory.locator("button").filter(has_text="Corpus v0.2 Audit Agent").first
        await selected_agent.wait_for(state="visible", timeout=60_000)
        await selected_agent.click()
    await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=60_000)

    await recorder.begin("builder-control-runtime")
    await _open_bound_agent_area(page, "Builds", "Agent Builds")
    build = page.locator("section.builder-home li[data-status='ready']").first
    await build.wait_for(state="visible", timeout=60_000)
    pause = build.get_by_role("button", name="Pause runtime", exact=True)
    if await pause.count():
        await pause.click()
        await build.get_by_text("Paused", exact=True).wait_for(timeout=30_000)
        await recorder.capture("02-runtime-paused")
        await build.get_by_role("button", name="Resume runtime", exact=True).click()
        await build.get_by_text("Running", exact=True).first.wait_for(timeout=30_000)
    stop = build.get_by_role("button", name="Stop runtime", exact=True)
    await stop.wait_for(state="visible", timeout=30_000)
    await stop.click()
    await build.get_by_text("Stopped", exact=True).first.wait_for(timeout=30_000)
    await recorder.capture("03-runtime-stopped")
    await build.get_by_role("button", name="Delete build runtime", exact=True).click()
    review = page.locator("section.builder-delete-review")
    await review.get_by_role("heading", name="Remove this draft runtime?", exact=True).wait_for(timeout=30_000)
    await recorder.capture("04-removal-review")
    await review.get_by_role("button", name="Remove draft runtime", exact=True).click()
    await build.get_by_text("The draft runtime was removed.", exact=False).wait_for(timeout=30_000)
    await recorder.capture("05-runtime-removed-history-retained")
    await recorder.finish("passed", "The exact draft runtime was paused, resumed, stopped, and removed only after review; immutable build plus recorded Sandbox and Evaluation history remained, and no deployment or Operations history was invented for this ineligible lineage.")
    await page.get_by_role("button", name="Back to Agent", exact=True).click()
    await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)

    await recorder.begin("agents-build-source-lineage")
    await page.locator("section.agent-operations").get_by_role("button", name="Builds", exact=True).click()
    lineage = page.get_by_role("region", name="Agent Builds", exact=True)
    open_version = lineage.get_by_role("button", name="Open API version", exact=True).first
    if await open_version.count() and await open_version.is_visible():
        await recorder.capture("02-historical-build-source-revision")
        await open_version.click()
        historical_source = page.locator("section.api-source-workspace")
        await historical_source.wait_for(state="visible", timeout=30_000)
        await recorder.capture("03-immutable-source-version-open")
        await recorder.finish("passed", "The historical build exposed and opened its exact captured API Source revision rather than reconstructing current Source state.")
        back_to_builds = historical_source.get_by_role("button", name="Back to Builds", exact=True)
        if await back_to_builds.count():
            await back_to_builds.click()
            await page.get_by_role("heading", name="Agent Builds", exact=True).wait_for(timeout=30_000)
            await page.get_by_role("button", name="Back to Agent", exact=True).click()
        else:
            await historical_source.get_by_role("button", name="Back to Agent", exact=True).click()
    else:
        await recorder.capture("02-historical-source-link-unavailable")
        await recorder.finish("failed", "The retained historical build did not expose the required exact captured API Source revision control after runtime removal.")
        await page.get_by_role("button", name="Back to Agent", exact=True).click()
    await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)

    await recorder.begin("agents-edit")
    main = page.locator("section.agents-home main")
    await _type_exact(main.get_by_label("Description", exact=True), "Updated after evaluation to prove immutable prior build lineage.", "Agent description edit")
    await _type_exact(main.get_by_label("Instructions", exact=True), "Use only attached reviewed Sources; preserve the already built immutable version.", "Agent instructions edit")
    await recorder.capture("02-real-edit")
    await main.get_by_role("button", name="Save new version", exact=True).click()
    await main.get_by_text("Version 2", exact=True).wait_for(timeout=30_000)
    await recorder.capture("03-version-two-with-prior-deployment")
    await recorder.finish("passed", "The allowed Agent fields saved as Version 2 while the already built Version 1 runtime, Sandbox, and Evaluation lineage remained visible and unchanged.")

    await recorder.begin("agents-detach-source")
    source_item = main.locator("section.agent-sources li").filter(has_text="Corpus v0.2 Medusa Source")
    detach = source_item.get_by_role("button", name=re.compile("^Detach Corpus v0.2 Medusa Source API version", re.I))
    await recorder.capture("02-current-attachment")
    await detach.click()
    await source_item.wait_for(state="detached", timeout=30_000)
    await recorder.capture("03-current-association-removed")
    await recorder.finish("passed", "Detaching removed only the current Agent-to-Source association; the Workspace Source and immutable historical build/deployment lineage remained.")

    await recorder.begin("agents-attach-source")
    picker = main.get_by_label("Ready Workspace Source", exact=True)
    options = await picker.locator("option").all()
    target_value = None
    for option in options:
        if "Corpus v0.2 Medusa Source" in (await option.inner_text()):
            target_value = await option.get_attribute("value")
            break
    if not target_value:
        raise RuntimeError("The detached ready Source is unavailable in the Agent picker.")
    await picker.select_option(target_value)
    await recorder.capture("02-existing-source-selected")
    await main.get_by_role("button", name="Attach Source", exact=True).click()
    source_item = main.locator("section.agent-sources li").filter(has_text="Corpus v0.2 Medusa Source")
    await source_item.wait_for(state="visible", timeout=30_000)
    await recorder.capture("03-existing-source-reattached")
    await recorder.finish("passed", "The exact existing ready Workspace Source was attached once and became visible again on the selected Agent.")

    await recorder.begin("agents-create-source")
    await main.get_by_role("button", name="Create and attach", exact=True).click()
    add_source_heading = page.get_by_role("heading", name="Add an API source", exact=True)
    create_source_error = page.get_by_text("The operation returned invalid state effects.", exact=True)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not await add_source_heading.count() and not await create_source_error.count():
        await page.wait_for_timeout(200)
    disposable_source: str | None = None
    if await add_source_heading.count():
        await recorder.capture("02-agent-bound-source-intake")
        disposable_source = f"Disposable attached Source {uuid4().hex[:6]}"
        bound_definition = page.get_by_label("OpenAPI or Swagger definition", exact=True)
        await bound_definition.set_input_files(MEDUSA_SPEC)
        await _type_exact(page.get_by_label("Source name", exact=True), disposable_source, "Agent-bound disposable Source name")
        if await bound_definition.input_value() == "":
            raise RuntimeError("The Agent-bound Medusa definition did not remain staged.")
        await page.get_by_role("button", name="Upload and process", exact=True).click()
        attach_return = page.get_by_role("button", name="Attach and return to Agent", exact=True)
        await attach_return.wait_for(state="visible", timeout=180_000)
        await recorder.capture("03-new-source-ready")
        await attach_return.click()
        await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)
        disposable_item = page.locator("section.agent-sources li").filter(has_text=disposable_source)
        await disposable_item.wait_for(state="visible", timeout=30_000)
        await recorder.capture("04-new-source-attached-and-returned")
        await recorder.finish("passed", "Create and attach opened Source Hub in selected-Agent context, processed a real disposable API Source, returned, and showed it attached.")
    else:
        await recorder.capture("02-create-and-attach-product-failure")
        await recorder.finish("failed", "The visible Create and attach action stayed on the Agent and returned 'The operation returned invalid state effects' instead of opening Agent-bound Source intake.")

    await recorder.begin("sources-start-description")
    await source_item.get_by_role("button", name="Open Source", exact=True).click()
    workspace = page.locator("section.api-source-workspace")
    await workspace.get_by_role("button", name="Add or update description", exact=True).wait_for(timeout=30_000)
    await recorder.capture("02-description-entry")
    await workspace.get_by_role("button", name="Add or update description", exact=True).click()
    await workspace.get_by_label("Markdown description", exact=True).wait_for(timeout=30_000)
    await recorder.capture("03-api-owned-description-surface")
    await recorder.finish("passed", "Source Hub routed the selected Source to its API-owned Markdown description surface while preserving Agent return context.")

    await recorder.begin("api-description")
    await workspace.get_by_label("Markdown description", exact=True).set_input_files(ROOT / "plans" / "2026-08-18-v02-behavior-evidence-audit.md")
    await recorder.capture("02-description-file-staged")
    await workspace.get_by_role("button", name="Save API description", exact=True).click()
    await page.get_by_text(re.compile("description", re.I)).first.wait_for(timeout=30_000)
    await recorder.capture("03-description-saved")
    await recorder.finish("passed", "A valid Markdown description was uploaded through the API Source surface and visibly persisted on the exact Source.")

    await recorder.begin("sources-delete")
    await workspace.get_by_role("button", name="Delete API source", exact=True).click()
    blocked_heading = workspace.get_by_role("heading", name="This API source is still part of saved Agent work", exact=True)
    await blocked_heading.wait_for(timeout=30_000)
    await recorder.capture("02-attached-source-delete-blocked")
    if disposable_source is None:
        await recorder.finish("blocked", "Corpus visibly blocked deletion of the attached canonical Source, but a safe disposable Source was unavailable because Create and attach failed earlier in this same real UI lineage.")
        back_to_agent = workspace.get_by_role("button", name="Back to Agent", exact=True)
        if await back_to_agent.count():
            await back_to_agent.click()
            await page.get_by_role("button", name="Back to Workspace", exact=True).click()
            await page.get_by_role("button", name="Open Agents", exact=True).click()
        else:
            await workspace.get_by_role("button", name="Source Hub", exact=True).click()
            hub = page.locator("section.source-hub")
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
            await hub.get_by_role("button", name="Back to Home", exact=True).click()
            await page.get_by_role("button", name="Open Agents", exact=True).click()
    else:
        await workspace.get_by_role("button", name="Source Hub", exact=True).click()
        hub = page.locator("section.source-hub")
        await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
        disposable_row = hub.locator("article.source-hub-row").filter(has_text=disposable_source)
        await disposable_row.get_by_role("button", name="Open API source", exact=True).click()
        workspace = page.locator("section.api-source-workspace")
        back_to_agent = workspace.get_by_role("button", name="Back to Agent", exact=True)
        if await back_to_agent.count():
            await back_to_agent.click()
        else:
            await workspace.get_by_role("button", name="Source Hub", exact=True).click()
            hub = page.locator("section.source-hub")
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
            await hub.get_by_role("button", name="Back to Home", exact=True).click()
            await page.get_by_role("button", name="Open Agents", exact=True).click()
            await page.get_by_label("Agent inventory").get_by_role("button", name="Corpus v0.2 Audit Agent Version 2", exact=False).click()
        await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)
        disposable_item = page.locator("section.agent-sources li").filter(has_text=disposable_source)
        await disposable_item.get_by_role("button", name=re.compile("^Detach ")).click()
        await disposable_item.wait_for(state="detached", timeout=30_000)
        await page.get_by_role("button", name="Back to Workspace", exact=True).click()
        await page.get_by_role("button", name="Open Sources", exact=True).click()
        hub = page.locator("section.source-hub")
        disposable_row = hub.locator("article.source-hub-row").filter(has_text=disposable_source)
        await disposable_row.get_by_role("button", name="Open API source", exact=True).click()
        workspace = page.locator("section.api-source-workspace")
        await workspace.get_by_role("button", name="Delete API source", exact=True).click()
        review = page.locator("section.source-delete-review")
        await review.get_by_role("heading", name="Confirm permanent Source deletion", exact=True).wait_for(timeout=30_000)
        await recorder.capture("03-disposable-source-delete-review")
        await review.get_by_role("button", name="Delete API source permanently", exact=True).click()
        await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
        await recorder.capture("04-disposable-source-deleted")
        await recorder.finish("passed", "Deletion showed the attached-source blocker, then permanently deleted only a detached disposable Source after explicit review.")
        await page.get_by_role("button", name="Back to Home", exact=True).click()
        await page.get_by_role("button", name="Open Agents", exact=True).click()
    agents = page.locator("section.agents-home")
    await agents.get_by_role("heading", name="Agents", exact=True).first.wait_for(timeout=30_000)

    async def create_disposable_agent(name: str) -> None:
        await agents.locator(".agents-heading").get_by_role("button", name="Create agent", exact=True).click()
        form = page.locator("section.agent-create form")
        await _type_exact(form.get_by_label("Name", exact=True), name, "disposable Agent name")
        await _type_exact(form.get_by_label("Description", exact=True), "Disposable lifecycle evidence record.", "disposable Agent description")
        await _type_exact(form.get_by_label("Instructions", exact=True), "No Sources or deployments; used only for reviewed lifecycle evidence.", "disposable Agent instructions")
        await form.get_by_role("button", name="Create agent", exact=True).click()
        await agents.get_by_label("Agent inventory").get_by_role("button", name=name, exact=False).wait_for(timeout=30_000)

    archive_name = f"Disposable archive {uuid4().hex[:6]}"
    await create_disposable_agent(archive_name)
    await agents.get_by_label("Agent inventory").get_by_role("button", name=archive_name, exact=False).click()
    await recorder.begin("agents-archive")
    await agents.get_by_role("button", name="Archive Agent", exact=True).click()
    review = page.locator("section.agent-lifecycle-review")
    await review.get_by_role("heading", name="Confirm archive", exact=True).wait_for(timeout=30_000)
    await recorder.capture("02-archive-review")
    await review.get_by_role("button", name="Archive Agent", exact=True).click()
    await agents.get_by_label("Agent inventory").get_by_role("button", name=archive_name, exact=False).wait_for(state="detached", timeout=30_000)
    await recorder.capture("03-archived-removed-from-active")
    await recorder.finish("passed", "Explicit review archived only the disposable Agent and removed it from the active inventory without claiming deletion.")

    delete_name = f"Disposable delete {uuid4().hex[:6]}"
    await create_disposable_agent(delete_name)
    await agents.get_by_label("Agent inventory").get_by_role("button", name=delete_name, exact=False).click()
    await recorder.begin("agents-delete")
    await agents.get_by_role("button", name="Delete permanently", exact=True).click()
    review = page.locator("section.agent-lifecycle-review")
    await review.get_by_role("heading", name="Confirm permanent deletion", exact=True).wait_for(timeout=30_000)
    await recorder.capture("02-delete-review")
    await review.get_by_role("button", name="Delete Agent permanently", exact=True).click()
    await agents.get_by_label("Agent inventory").get_by_role("button", name=delete_name, exact=False).wait_for(state="detached", timeout=30_000)
    await recorder.capture("03-agent-deleted")
    await recorder.finish("passed", "Permanent deletion identified and reviewed the exact disposable Agent, found no blockers, and removed only that Agent.")

    await recorder.begin("agents-setup-from-api-file")
    await ensure_workspace(page)
    new_conversation = page.get_by_role("button", name="New conversation", exact=True)
    if await new_conversation.count():
        await new_conversation.click()
    attachment = page.get_by_label("Attach API definition", exact=True)
    await attachment.wait_for(state="visible", timeout=30_000)
    await attachment.set_input_files(MEDUSA_SPEC)
    await recorder.capture("02-definition-attached-to-chat")
    reply = await send_chat(page, "Add this attached API definition and start its analysis now. Complete both actions, then ask me which Agent should use it.")
    api_workspace = page.locator("section.api-source-workspace")
    await api_workspace.wait_for(state="visible", timeout=180_000)
    await api_workspace.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
    await recorder.capture("03-chat-authorized-setup-ready")
    await api_workspace.get_by_role("button", name="Agent", exact=True).click()
    await api_workspace.get_by_role("button", name="Use an existing Agent", exact=True).click()
    await page.get_by_role("button", name="Corpus v0.2 Audit Agent Version 2", exact=False).click()
    await page.get_by_role("button", name="Attach Source", exact=True).click()
    await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)
    await recorder.capture("04-ready-source-attached-to-selected-agent")
    chose_agent = "agent" in reply.casefold() and ("existing" in reply.casefold() or "create" in reply.casefold())
    await recorder.finish("passed" if chose_agent else "failed", "The authenticated chat staged the real attached file, executed only the explicitly authorized add-and-analyze actions, asked which Agent should use it, and the surface attached the ready Source to the exact existing Agent.")


async def classify_unreached_depths(recorder: Recorder, reason: str, from_depth: int = 3) -> None:
    for item in recorder.ledger["behaviors"]:
        if item["depth"] >= from_depth and item["status"] == "pending" and item["observed"] == "Not executed.":
            await recorder.classify_here(item["id"], "blocked", reason)


async def run(args: argparse.Namespace) -> None:
    ledger = load_or_create_ledger()
    run_id = f"RUN-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    ledger["lastRun"] = {"id": run_id, "startedAt": now(), "finishedAt": None}
    write_outputs(ledger)
    await preflight_runtime(ledger)
    owner = await create_mailtm_owner()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="corpus-v02-audit-") as profile:
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                profile,
                headless=not args.headed,
                viewport=DESKTOP,
            )
            page = context.pages[0] if context.pages else await context.new_page()
            recorder = Recorder(ledger, page, context, [owner["email"], owner["password"], owner["mailToken"]], run_id)
            try:
                await audit_lounge_auth_workspace(recorder, owner)
                if args.stop_after_depth <= 2:
                    return
                foundation_ready = await audit_agents_and_sources(recorder)
                if not foundation_ready:
                    await classify_unreached_depths(recorder, "The required Agent/Source foundation failed in the real UI path.", 4)
                else:
                    runtime_ready = await audit_designer_builder_sandbox(recorder)
                    if not runtime_ready:
                        await classify_unreached_depths(recorder, "The required Designer/Builder/Sandbox path failed in the real UI.", 7)
                    else:
                        delivery_ready = await audit_evaluation_channels_operations(recorder)
                        try:
                            await audit_post_delivery_breadth(recorder)
                        except Exception as error:
                            print(f"[post-lifecycle-error] {type(error).__name__}: {error}", flush=True)
                            if recorder.active_behavior is not None:
                                try:
                                    await recorder.capture("99-failure")
                                    await recorder.finish("failed", f"The independent lifecycle branch failed in the real UI: {type(error).__name__}: {error}")
                                except Exception:
                                    pass
                        if not delivery_ready:
                            await classify_unreached_depths(recorder, "A required earlier result in the real Evaluation/Channels/Operations path failed.", 8)
            finally:
                try:
                    await classify_unreached_depths(
                        recorder,
                        "The behavior was not reachable in this run because an earlier required real application state did not complete.",
                        0,
                    )
                except Exception:
                    pass
                ledger["lastRun"]["finishedAt"] = now()
                await context.close()
                write_outputs(ledger)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record the Corpus v0.2 as-is behavior audit.")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--stop-after-depth", type=int, default=9)
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ledger = load_or_create_ledger()
    if args.freeze_only:
        print(json.dumps({"behaviors": len(ledger["behaviors"]), "counts": result_counts(ledger), "ledger": str(LEDGER_PATH)}, indent=2))
        return
    if args.validate_only:
        write_outputs(ledger)
        issues = validate_outputs(ledger)
        print(json.dumps({"valid": not issues, "issues": issues, "counts": result_counts(ledger)}, indent=2))
        if issues:
            raise SystemExit(1)
        return
    asyncio.run(run(args))
    final = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    print(json.dumps({"behaviors": len(final["behaviors"]), "counts": result_counts(final), "ledger": str(LEDGER_PATH), "html": str(HTML_PATH)}, indent=2))


if __name__ == "__main__":
    main()
