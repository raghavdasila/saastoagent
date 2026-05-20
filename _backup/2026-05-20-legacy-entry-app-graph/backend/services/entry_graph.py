"""Compatibility wrapper for the entry runtime service.

The implementation now lives under ``backend.services.entry_runtime`` so the
backend flow can be split into graph spec, runtime store, stage modules, and
an orchestrator that owns backend session state.
"""

from backend.services.entry_runtime import run_entry_turn

__all__ = ["run_entry_turn"]
