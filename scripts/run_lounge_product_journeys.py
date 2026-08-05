from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from corpus.evaluation import LoungeProductJourneyRunner
from corpus.evaluation.isolated_runtime import IsolatedCorpusRuntime


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run Studio-owned Lounge product journeys through a real Corpus "
            "browser, isolated auth database, Gmail SMTP, and Mail.tm mailbox."
        )
    )
    parser.add_argument("--journey")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[1]
    artifact = asyncio.run(_run(repository, args.journey, not args.headed))
    print(f"run={artifact['runId']} status={artifact['status']}")
    print("mailbox=Mail.tm https://mail.tm")
    cost = artifact["usage"]["exactCostUsd"]
    cost_text = f"${cost:.2f}" if cost is not None else "not returned; not estimated"
    print(
        "usage="
        f"{artifact['usage']['inputTokens']} input + "
        f"{artifact['usage']['outputTokens']} output tokens; exact cost {cost_text}"
    )
    for result in artifact["results"]:
        print(f"{result['evaluationId']}: {result['status']}")


async def _run(repository: Path, journey: str | None, headless: bool):
    run_name = __import__("uuid").uuid4().hex[:10]
    primary = IsolatedCorpusRuntime(
        repository,
        name=f"{run_name}-primary",
        backend_port=8109,
        frontend_port=5209,
    )
    outage = IsolatedCorpusRuntime(
        repository,
        name=f"{run_name}-outage",
        backend_port=8110,
        frontend_port=5210,
        mail_outage=True,
    )
    primary_endpoints = await primary.start()
    outage_endpoints = None
    try:
        if journey in {None, "lounge-journey-mail-outage"}:
            outage_endpoints = await outage.start()
        runner = LoungeProductJourneyRunner(
            repository=repository,
            frontend_url=primary_endpoints.frontend_url,
            auth_database_url=primary_endpoints.auth_database_url,
            headless=headless,
            mail_outage_frontend_url=(
                outage_endpoints.frontend_url
                if outage_endpoints is not None
                else None
            ),
        )
        return await runner.run(journey)
    finally:
        await outage.close()
        await primary.close()


if __name__ == "__main__":
    main()
