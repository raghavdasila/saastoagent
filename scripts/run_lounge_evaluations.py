from __future__ import annotations

import argparse
from pathlib import Path

from corpus.evaluation import LoungeEvaluationRunner
from corpus.runtime.config import CorpusRuntimeSettings
from corpus.shared.environment import read_environment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Studio-owned Lounge conversation evaluations against live Corpus.")
    parser.add_argument("--scenario")
    parser.add_argument(
        "--level",
        choices=("conversation", "behavior"),
        default="conversation",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8099")
    parser.add_argument("--origin", default="http://127.0.0.1:5199")
    parser.add_argument("--max-adaptive-turns", type=int, default=2)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    env_file = repository / ".env.local"
    settings = CorpusRuntimeSettings.from_env(env_file)
    evaluation = read_environment(
        env_file,
        {
            "CORPUS_EVAL_PROVIDER",
            "CORPUS_EVAL_TESTER_MODEL",
            "CORPUS_EVAL_JUDGE_MODEL",
        },
    )
    provider = evaluation.get("CORPUS_EVAL_PROVIDER", settings.model_provider)
    default_evaluation_model = (
        settings.ollama_model if provider == "ollama" else settings.openai_model
    )
    if default_evaluation_model is None:
        raise ValueError(f"No model is configured for evaluation provider {provider}")
    runner = LoungeEvaluationRunner(
        repository=repository,
        base_url=args.base_url,
        origin=args.origin,
        model_provider=provider,
        ollama_url=(
            str(settings.ollama_base_url)
            if settings.ollama_base_url is not None
            else None
        ),
        openai_api_key=settings.openai_api_key,
        openai_reasoning_effort=settings.openai_reasoning_effort,
        corpus_model=settings.selected_model_name,
        tester_model=evaluation.get(
            "CORPUS_EVAL_TESTER_MODEL", default_evaluation_model
        ),
        judge_model=evaluation.get(
            "CORPUS_EVAL_JUDGE_MODEL", default_evaluation_model
        ),
        max_adaptive_turns=args.max_adaptive_turns,
    )
    artifact = runner.run(args.scenario, evaluation_level=args.level)
    print(f"run={artifact['runId']} status={artifact['status']}")
    for result in artifact["results"]:
        print(f"{result['evaluationId']}: {result['status']}")


if __name__ == "__main__":
    main()
