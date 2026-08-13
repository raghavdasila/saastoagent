from __future__ import annotations

import ipaddress
import os
import subprocess
import time
from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.request import urlopen


GCLOUD = "gcloud.cmd" if os.name == "nt" else "gcloud"


@dataclass(frozen=True)
class GcpJourneyRuntime:
    project: str
    corpus_vm: str
    corpus_zone: str
    medusa_vm: str
    medusa_zone: str
    medusa_base_url: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.project,
                self.corpus_vm,
                self.corpus_zone,
                self.medusa_vm,
                self.medusa_zone,
            )
        ):
            raise ValueError("GCP project, VM, and zone identities are required.")
        parsed = urlsplit(self.medusa_base_url)
        if parsed.scheme != "http" or parsed.username or parsed.password:
            raise ValueError("The Medusa acceptance target must be an HTTP private origin.")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("The Medusa acceptance target must be an origin only.")
        try:
            address = ipaddress.ip_address(parsed.hostname or "")
        except ValueError as error:
            raise ValueError("The Medusa acceptance target must use a private IPv4 address.") from error
        if address.version != 4 or not address.is_private or address.is_loopback:
            raise ValueError("The Medusa acceptance target must use a private IPv4 address.")
        if parsed.port is None:
            raise ValueError("The Medusa acceptance target must declare its private port.")

    def ssh(self, *, vm: str, zone: str, command: str, timeout: int = 180) -> str:
        completed = subprocess.run(
            [
                GCLOUD,
                "compute",
                "ssh",
                vm,
                f"--zone={zone}",
                f"--project={self.project}",
                "--tunnel-through-iap",
                "--quiet",
                "--command",
                command,
            ],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"Remote command failed for {vm}: {detail}")
        return completed.stdout.strip()

    def corpus_generations(self) -> tuple[str, str]:
        output = self.ssh(
            vm=self.corpus_vm,
            zone=self.corpus_zone,
            command=(
                "sudo docker inspect corpus-production-backend-1 corpus-production-worker-1 "
                "--format '{{.Name}}|{{.State.StartedAt}}|{{.State.Running}}|{{.State.Restarting}}'"
            ),
        )
        rows = [line.strip().split("|") for line in output.splitlines() if line.strip()]
        values: dict[str, str] = {}
        for row in rows:
            if len(row) != 4 or row[2:] != ["true", "false"]:
                continue
            values[row[0].lstrip("/")] = row[1]
        try:
            return (
                values["corpus-production-backend-1"],
                values["corpus-production-worker-1"],
            )
        except KeyError as error:
            raise RuntimeError("The deployed Corpus runtime generation is unavailable.") from error

    def restart_corpus(self, backend_url: str) -> float:
        started = time.monotonic()
        previous = self.corpus_generations()
        self.ssh(
            vm=self.corpus_vm,
            zone=self.corpus_zone,
            command="sudo systemctl restart corpus.service",
            timeout=300,
        )
        deadline = time.monotonic() + 300
        consecutive = 0
        observed: tuple[str, str] | None = None
        target = backend_url.rstrip("/") + "/readyz"
        while time.monotonic() < deadline:
            try:
                current = self.corpus_generations()
                with urlopen(target, timeout=10) as response:
                    ready = response.status == 200 and current != previous
            except Exception:
                current = None
                ready = False
            if ready and current == observed:
                consecutive += 1
            elif ready:
                observed = current
                consecutive = 1
            else:
                consecutive = 0
                observed = None
            if consecutive >= 3:
                return time.monotonic() - started
            time.sleep(2)
        raise RuntimeError("The deployed Corpus runtime did not recover with new generations.")

    def provider_identity(self) -> str:
        output = self.ssh(
            vm=self.corpus_vm,
            zone=self.corpus_zone,
            command=(
                "sudo docker inspect corpus-production-backend-1 "
                "--format '{{range .Config.Env}}{{println .}}{{end}}' | "
                "grep '^CORPUS_MODEL_PROVIDER='"
            ),
        )
        values = [line.split("=", 1)[1] for line in output.splitlines() if "=" in line]
        if values != ["openai"]:
            raise RuntimeError("The deployed Corpus model provider is not exactly OpenAI.")
        return values[0]
