"""레슨 스키마 검증기의 계약.

검증기가 조용히 무력화되면(예: 경계 검사가 늘 통과) 브라우저에서 죽는 레슨이 배포된다.
여기서 각 오류 부류를 하나씩 못 박는다.
"""

from __future__ import annotations

import pytest

from tests.audit.lessonSchema import _checkLesson, _findCycle, validate

pytestmark = [pytest.mark.unit]

_TRACKS = {"foundations", "market"}


def _lesson(sections: list[dict], *, level: str = "기초", track: str = "foundations") -> dict:
    """검증기가 받는 모양(YAML 파싱 결과)을 그대로 만든다."""
    return {
        "meta": {
            "id": "sample",
            "title": "샘플",
            "description": "설명",
            "level": level,
            "track": track,
            "order": 1,
            "tags": ["x"],
        },
        "intro": {"goal": "목표", "body": "본문"},
        "sections": sections,
    }


def test_realCorpusPasses() -> None:
    """저장소에 실린 레슨 전수가 스키마·그래프·규모 계약을 만족한다."""
    assert validate() == []


def test_rejectsUnknownLevel(tmp_path) -> None:
    doc = _lesson([{"id": "a", "code": 'c.panel("IS")'}], level="초급")
    errs = _checkLesson(tmp_path / "x.yaml", doc, _TRACKS)
    assert any("meta.level" in e for e in errs)


def test_rejectsUnknownTrack(tmp_path) -> None:
    doc = _lesson([{"id": "a", "code": 'c.panel("IS")'}], track="ghost")
    errs = _checkLesson(tmp_path / "x.yaml", doc, _TRACKS)
    assert any("TRACKS 에 없다" in e for e in errs)


def test_rejectsDuplicateSectionId(tmp_path) -> None:
    """섹션 id 는 진도 오버레이가 셀을 매칭하는 키라 중복이면 사용자 편집이 엉킨다."""
    doc = _lesson([{"id": "a", "code": 'c.panel("IS")'}, {"id": "a", "code": 'c.panel("BS")'}])
    errs = _checkLesson(tmp_path / "x.yaml", doc, _TRACKS)
    assert any("중복" in e for e in errs)


def test_rejectsSyntaxError(tmp_path) -> None:
    doc = _lesson([{"id": "a", "code": "this is not python((("}])
    errs = _checkLesson(tmp_path / "x.yaml", doc, _TRACKS)
    assert any("문법 오류" in e for e in errs)


def test_rejectsBrowserImpossibleGather(tmp_path) -> None:
    """수집 호출을 pyodide 로 태깅하면 브라우저에서 죽는다."""
    doc = _lesson([{"id": "a", "code": 'c.gather("price")'}])
    errs = _checkLesson(tmp_path / "x.yaml", doc, _TRACKS)
    assert any("브라우저에서 못 돈다" in e for e in errs)


def test_allowsGatherCatalog(tmp_path) -> None:
    """인자 없는 카탈로그 조회는 브라우저에서 실제로 동작한다(실측)."""
    doc = _lesson([{"id": "a", "code": "c.gather()"}])
    assert _checkLesson(tmp_path / "x.yaml", doc, _TRACKS) == []


def test_allowsLocalTaggedGather(tmp_path) -> None:
    """``runtime: local`` 이면 브라우저는 읽기 전용으로 렌더하므로 통과."""
    doc = _lesson([{"id": "a", "runtime": "local", "code": 'c.gather("price")'}])
    assert _checkLesson(tmp_path / "x.yaml", doc, _TRACKS) == []


def test_allowsExpectErrorBoundaryLesson(tmp_path) -> None:
    """경계를 가르치는 셀은 예외가 나는 것이 정상이다."""
    doc = _lesson([{"id": "a", "expectError": True, "code": 'c.gather("price")'}])
    assert _checkLesson(tmp_path / "x.yaml", doc, _TRACKS) == []


def test_rejectsBrowserImpossibleScanAxis(tmp_path) -> None:
    """screen 축은 KRX 목록이 필요해 브라우저에서 못 돈다 (runtime.pyodide 실측)."""
    doc = _lesson([{"id": "a", "code": 'dartlab.scan("screen", "value")'}])
    errs = _checkLesson(tmp_path / "x.yaml", doc, _TRACKS)
    assert any("브라우저 불가" in e for e in errs)


def test_allowsBrowserScanAxis(tmp_path) -> None:
    doc = _lesson([{"id": "a", "code": 'dartlab.scan("ratio", "roe")'}])
    assert _checkLesson(tmp_path / "x.yaml", doc, _TRACKS) == []


def test_findCycle_detectsSelfLoopAndRing() -> None:
    assert _findCycle({"a": ["a"]}) == ["a", "a"]
    assert _findCycle({"a": ["b"], "b": ["c"], "c": ["a"]})
    assert _findCycle({"a": ["b"], "b": []}) is None
