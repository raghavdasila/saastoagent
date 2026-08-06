from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import SecretStr

from corpus.evaluation import FeatureEvaluationRunner
from corpus.shared.environment import read_environment


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run Studio-owned feature evaluations against the live Corpus "
            "product path."
        )
    )
    parser.add_argument("--feature", required=True)
    parser.add_argument("--scenario")
    parser.add_argument(
        "--level",
        choices=("conversation", "behavior"),
        default="behavior",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8099")
    parser.add_argument("--origin", default="http://127.0.0.1:5199")
    parser.add_argument("--max-adaptive-turns", type=int, default=2)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
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
    runner = FeatureEvaluationRunner(
        repository=repository,
        base_url=args.base_url,
        origin=args.origin,
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
        max_adaptive_turns=args.max_adaptive_turns,
    )
    artifact = runner.run(
        args.scenario,
        evaluation_level=args.level,
        feature_name=args.feature,
    )
    print(f"run={artifact['runId']} status={artifact['status']}")
    for result in artifact["results"]:
        print(f"{result['evaluationId']}: {result['status']}")


if __name__ == "__main__":
    main()
