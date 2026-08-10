import pytest

import scripts.run_agents_lifecycle_journey as recorder
from scripts.run_agents_lifecycle_journey import _inside_viewport, restore_agents


class _RecoveryLocator:
    def __init__(self, page: "_RecoveryPage", name: str) -> None:
        self.page = page
        self.name = name

    @property
    def last(self) -> "_RecoveryLocator":
        return self

    async def count(self) -> int:
        return int(self.name in self.page.visible)

    async def is_visible(self) -> bool:
        return self.name in self.page.visible

    async def click(self) -> None:
        self.page.clicked.append(self.name)
        if self.name == "Continue to Workspace":
            self.page.visible = {"Open Agents"}
        elif self.name == "Open Agents":
            self.page.visible = {"Agents"}

    async def wait_for(self, **_kwargs) -> None:
        raise TimeoutError("one-shot heading wait cannot recover from bootstrap")


class _RecoveryPage:
    def __init__(self) -> None:
        self.visible: set[str] = set()
        self.clicked: list[str] = []
        self.waits = 0

    def get_by_role(self, _role: str, *, name: str, exact: bool) -> _RecoveryLocator:
        assert exact is True
        return _RecoveryLocator(self, name)

    async def wait_for_timeout(self, _milliseconds: int) -> None:
        self.waits += 1
        if self.waits == 1:
            self.visible = {"Continue to Workspace"}


def test_mobile_evidence_requires_each_control_fully_inside_viewport() -> None:
    viewport = {"width": 390, "height": 844}

    assert _inside_viewport(
        {"x": 16, "y": 96, "width": 358, "height": 48},
        viewport,
    )
    assert not _inside_viewport(
        {"x": 16, "y": 820, "width": 358, "height": 48},
        viewport,
    )
    assert not _inside_viewport(None, viewport)


@pytest.mark.asyncio
async def test_restore_agents_waits_for_late_bootstrap_controls() -> None:
    page = _RecoveryPage()

    await restore_agents(page, timeout_ms=1_000, poll_interval_ms=1)

    assert page.clicked == ["Continue to Workspace", "Open Agents"]
    assert page.visible == {"Agents"}


@pytest.mark.asyncio
async def test_post_reload_evidence_runs_mobile_before_restart_and_retains_both() -> None:
    observed: list[str] = []

    async def capture_mobile() -> None:
        observed.append("mobile")

    async def verify_restart() -> None:
        observed.append("restart")

    await recorder._run_post_reload_evidence(capture_mobile, verify_restart)

    assert observed == ["mobile", "restart"]
