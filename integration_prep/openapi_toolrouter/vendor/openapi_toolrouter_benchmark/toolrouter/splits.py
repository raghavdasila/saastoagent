from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def stable_float(value: str) -> float:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(0xFFFFFFFFFFFF)


def task_resource(task: dict[str, Any]) -> str:
    return str(task.get("resource") or "general")


def assign_group(task_ids: list[str], train_ratio: float = 0.6, dev_ratio: float = 0.2) -> dict[str, list[str]]:
    ordered = sorted(task_ids, key=stable_float)
    splits = {"train": [], "dev": [], "test": []}
    count = len(ordered)
    if count == 1:
        splits["train"] = ordered
        return splits
    if count == 2:
        splits["train"] = [ordered[0]]
        splits["test"] = [ordered[1]]
        return splits
    train_count = max(1, int(round(count * train_ratio)))
    dev_count = max(1, int(round(count * dev_ratio)))
    if train_count + dev_count >= count:
        train_count = max(1, count - 2)
        dev_count = 1
    splits["train"] = ordered[:train_count]
    splits["dev"] = ordered[train_count : train_count + dev_count]
    splits["test"] = ordered[train_count + dev_count :]
    return splits


def build_primary_split(tasks: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for task in tasks:
        groups[(str(task.get("task_type") or "unknown"), task_resource(task))].append(task["id"])
    primary = {"train": [], "dev": [], "test": []}
    for task_ids in groups.values():
        assigned = assign_group(task_ids)
        for split, ids in assigned.items():
            primary[split].extend(ids)
    return {split: sorted(ids) for split, ids in primary.items()}


def build_leave_domain_out(tasks: list[dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
    by_resource: dict[str, list[str]] = defaultdict(list)
    task_by_id = {task["id"]: task for task in tasks}
    for task in tasks:
        by_resource[task_resource(task)].append(task["id"])
    folds: dict[str, dict[str, list[str]]] = {}
    all_ids = {task["id"] for task in tasks}
    for resource, held_out in sorted(by_resource.items()):
        if len(held_out) < 2:
            continue
        test_ids = set(held_out)
        remaining = sorted(all_ids - test_ids)
        remaining_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
        for task_id in remaining:
            task = task_by_id[task_id]
            remaining_groups[(str(task.get("task_type") or "unknown"), task_resource(task))].append(task_id)
        dev_ids: set[str] = set()
        for ids in remaining_groups.values():
            assigned = assign_group(ids, train_ratio=0.8, dev_ratio=0.2)
            dev_ids.update(assigned["dev"] or assigned["test"])
        if not dev_ids and remaining:
            dev_ids.add(sorted(remaining, key=stable_float)[0])
        folds[resource] = {
            "train": sorted(set(remaining) - dev_ids),
            "dev": sorted(dev_ids),
            "test": sorted(test_ids),
        }
    return folds


def build_task_splits(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 1,
        "primary": build_primary_split(tasks),
        "leave_domain_out": build_leave_domain_out(tasks),
    }


def split_task_ids_for_evaluation(tasks: list[dict[str, Any]], splits: dict[str, Any] | None) -> dict[str, set[str]]:
    all_ids = {task["id"] for task in tasks}
    if not splits:
        return {"all": all_ids}
    scopes: dict[str, set[str]] = {"all": all_ids}
    primary = splits.get("primary", {})
    for split in ["train", "dev", "test"]:
        scopes[split] = set(primary.get(split, []))
    for resource, fold in splits.get("leave_domain_out", {}).items():
        scopes[f"leave_domain_out:{resource}"] = set(fold.get("test", []))
    return scopes


def training_contexts(tasks: list[dict[str, Any]], splits: dict[str, Any] | None) -> dict[str, dict[str, set[str]]]:
    all_ids = {task["id"] for task in tasks}
    if not splits:
        return {"all": {"train": all_ids, "dev": set(), "eval": all_ids}}
    contexts: dict[str, dict[str, set[str]]] = {}
    primary = splits.get("primary", {})
    train_ids = set(primary.get("train", []))
    dev_ids = set(primary.get("dev", []))
    contexts["all"] = {"train": train_ids, "dev": dev_ids, "eval": all_ids}
    for split in ["train", "dev", "test"]:
        contexts[split] = {
            "train": train_ids,
            "dev": dev_ids,
            "eval": set(primary.get(split, [])),
        }
    for resource, fold in splits.get("leave_domain_out", {}).items():
        contexts[f"leave_domain_out:{resource}"] = {
            "train": set(fold.get("train", [])),
            "dev": set(fold.get("dev", [])),
            "eval": set(fold.get("test", [])),
        }
    return contexts


def primary_split_by_task(splits: dict[str, Any] | None) -> dict[str, str]:
    if not splits:
        return {}
    by_task = {}
    for split, ids in splits.get("primary", {}).items():
        for task_id in ids:
            by_task[task_id] = split
    return by_task


def write_task_splits(splits: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(splits, indent=2), encoding="utf-8")


def read_task_splits(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(path.read_text(encoding="utf-8"))
