"""concurrency 그룹을 공유하는 워크플로는 job 레벨이어야 한다 (2026-08 축출 사고 가드).

GitHub 은 concurrency group 당 pending 을 1 개만 유지하고, 새 트리거가 오면 기존 pending 을
취소한다. 공식 문서 문구는 "any existing pending job or workflow in the same concurrency
group will be canceled" 이며 `cancel-in-progress` 설정과 무관하다. 그 옵션은 실행 중인 것만
보호한다.

워크플로 레벨 concurrency 는 run 생성 즉시 큐를 점유하므로, 한 그룹을 둘 이상이 공유하면
서로를 큐에서 밀어낸다. 2026-08-19 실측: hf-dart-push 에서 취소된 run 8 건이 전부 job 0 개,
즉 실행조차 시작하지 못한 상태였다. job 레벨이면 `if` 로 skip 되는 job 은 큐에 진입조차 하지
않고, 대기 중인 job 도 워크플로 레벨 pending 처럼 축출되지 않는다.
"""

from __future__ import annotations

import collections
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def _collectGroups() -> dict[str, list[tuple[str, str]]]:
    """concurrency group -> [(표시이름, 'workflow' | 'job')] 목록."""
    groups: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for path in sorted(WORKFLOWS.glob("*.yml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            continue
        name = loaded.get("name", path.stem)

        top = loaded.get("concurrency") or {}
        if isinstance(top, dict) and top.get("group"):
            groups[str(top["group"]).split("#", 1)[0].strip()].append((name, "workflow"))

        for jobName, job in (loaded.get("jobs") or {}).items():
            jobConc = (job or {}).get("concurrency") or {}
            if isinstance(jobConc, dict) and jobConc.get("group"):
                key = str(jobConc["group"]).split("#", 1)[0].strip()
                groups[key].append((f"{name}/{jobName}", "job"))
    return groups


def test_workflows_are_discoverable() -> None:
    """테스트 전제: 워크플로를 실제로 읽고 있다."""
    groups = _collectGroups()
    assert len(groups) >= 10, f"concurrency 그룹을 거의 못 읽었다: {len(groups)}"
    assert "hf-dart-push" in groups, "핵심 직렬 그룹을 찾지 못했다"


def test_shared_groups_use_job_level_concurrency() -> None:
    """둘 이상이 공유하는 그룹에 워크플로 레벨 참여자가 없어야 한다."""
    groups = _collectGroups()
    offenders: dict[str, list[str]] = {}
    for group, members in groups.items():
        if len(members) < 2:
            continue
        workflowLevel = [name for name, level in members if level == "workflow"]
        if workflowLevel:
            offenders[group] = workflowLevel

    assert offenders == {}, (
        "공유 concurrency 그룹에 워크플로 레벨 참여자가 있다. "
        "run 생성 즉시 큐를 점유해 서로를 축출한다. job 레벨로 내려라: " + repr(offenders)
    )


def test_dart_serial_group_members_are_job_level() -> None:
    """hf-dart-push 는 사고 당사자 그룹이라 개별로도 고정한다."""
    members = _collectGroups()["hf-dart-push"]
    assert len(members) >= 6, f"참여자가 예상보다 적다: {members}"
    workflowLevel = [name for name, level in members if level == "workflow"]
    assert workflowLevel == [], f"hf-dart-push 에 워크플로 레벨 참여자 복귀: {workflowLevel}"
