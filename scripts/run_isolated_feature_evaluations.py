from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from uuid import uuid4

from pydantic import SecretStr

from corpus.evaluation import FeatureEvaluationRunner
from corpus.evaluation.isolated_runtime import IsolatedCorpusRuntime
from corpus.shared.environment import read_environment


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run one Studio feature's evaluations against a fresh local Corpus "
            "runtime and disposable persistent database."
        )
    )
    parser.add_argument("--feature", required=True)
    parser.add_argument("--scenario")
    parser.add_argument(
        "--level",
        choices=("conversation", "behavior"),
        default="behavior",
    )
    parser.add_argument("--backend-port", type=int, default=8129)
    parser.add_argument("--frontend-port", type=int, default=5229)
    args = parser.parse_args()
    artifact = asyncio.run(_run(args))
    print(f"run={artifact['runId']} status={artifact['status']}")
    for result in artifact["results"]:
        print(f"{result['evaluationId']}: {result['status']}")


async def _run(args) -> dict:
    repository = Path(__file__).resolve().parents[1]
    runtime = IsolatedCorpusRuntime(
        repository,
        name=f"feature-{args.feature.casefold()}-{uuid4().hex[:10]}",
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
    )
    endpoints = await runtime.start()
    try:
        runner = _runner(
            repository,
            endpoints.backend_url,
            endpoints.frontend_url,
        )
        return await asyncio.to_thread(
            runner.run,
            args.scenario,
            evaluation_level=args.level,
            feature_name=args.feature,
        )
    finally:
        await runtime.close()


def _runner(repository: Path, backend_url: str, frontend_url: str):
    env_file = repository / ".env.local"
    values = read_environment(
        env_file,
        {
            "CORPUS_MODEL_PROVIDER",
            "OLLAMA_BASE_URL",
            "OLLAMA_MODEL",
            "OPENAI_API_KEY",
            "CORPUS_OPENAI_MODEL",
            "CORPUS_OPENAI_REASONING_EFFORT",
            "CORPUS_EVAL_PROVIDER",
            "CORPUS_EVAL_TESTER_MODEL",
            "CORPUS_EVAL_JUDGE_MODEL",
        },
    )
    provider = values.get(
        "CORPUS_EVAL_PROVIDER",
        values.get("CORPUS_MODEL_PROVIDER", "ollama"),
    )
    default_model = values.get(
        "OLLAMA_MODEL" if provider == "ollama" else "CORPUS_OPENAI_MODEL"
    )
    if default_model is None:
        raise ValueError(
            f"No model is configured for evaluation provider {provider}"
        )
    return FeatureEvaluationRunner(
        repository=repository,
        base_url=backend_url,
        origin=frontend_url,
        model_provider=provider,
        ollama_url=values.get("OLLAMA_BASE_URL"),
        openai_api_key=(
            SecretStr(values["OPENAI_API_KEY"])
            if "OPENAI_API_KEY" in values
            else None
        ),
        openai_reasoning_effort=values.get(
            "CORPUS_OPENAI_REASONING_EFFORT", "low"
        ),
        corpus_model=default_model,
        tester_model=values.get("CORPUS_EVAL_TESTER_MODEL", default_model),
        judge_model=values.get("CORPUS_EVAL_JUDGE_MODEL", default_model),
        max_adaptive_turns=2,
    )


if __name__ == "__main__":
    main()
