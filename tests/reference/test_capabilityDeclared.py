"""capability 축 반사가 엔진의 **이미 있는 선언**을 버리지 않는지 (reference/capability/builder).

배경: `_injectAxisRegistriesLive` 가 label/description 만 캐리하고 축 엔트리의 나머지 선언
(scan returnType/listFn, quant stockRequired/multiStock, gather/industry targetType/hidden,
macro act, credit group) 을 버렸다. 그래서 소비측이 축의 반환형·타깃 필요 여부·카탈로그 원자
여부를 알 수 없었고, "선언이 없다" 는 오독으로 새 선언 표면을 발명할 뻔했다 (2026-07-07).

Covers:
- 조용한 누락 0: ignore 아닌 non-None 필드 집합 == declared 키 집합 (새 엔진이 새 필드명을 써도 흐름).
- 카탈로그 원자 3축(scan.account/ratio/note) 이 returnType + listFn 을 선언한다 (척추 식별 근거).
- False 보존: targetRequired=False 는 유효 선언(타깃 불요 = 전종목 벌크)이라 None 처럼 버리지 않는다.
- 키 불변: "{engine}.{axis}" 키는 additive 변경에도 byte-안정 (registry._validateCapabilityRefs 캐스케이드 가드).
- 비-dataclass 엔트리는 크래시 대신 빈 declared (미래 레지스트리 가드).
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

from dartlab.reference.capability.builder import (
    _AXIS_IGNORE_FIELDS,
    _AXIS_REGISTRIES,
    _declaredAxisFields,
    _injectAxisRegistriesLive,
)

pytestmark = pytest.mark.unit

SPINE_ATOMS = ("scan.account", "scan.ratio", "scan.note")


def _reflect() -> dict[str, dict]:
    entries: dict[str, dict] = {}
    _injectAxisRegistriesLive(entries)
    return entries


def _liveRegistries():
    for prefix, modPath, attr in _AXIS_REGISTRIES:
        registry = getattr(importlib.import_module(modPath), attr, None)
        if isinstance(registry, dict):
            yield prefix, registry


def testNoSilentDrop():
    """ignore 아닌 non-None 선언은 하나도 버려지지 않는다 (자동흡수의 기계 보증)."""
    for prefix, registry in _liveRegistries():
        for axisName, entry in registry.items():
            expected = {
                f.name
                for f in dataclasses.fields(entry)
                if f.name not in _AXIS_IGNORE_FIELDS and getattr(entry, f.name, None) is not None
            }
            got = set(_declaredAxisFields(entry))
            assert got == expected, f"{prefix}.{axisName}: 선언 누락 {expected - got} / 유령 {got - expected}"


def testSpineAtomsDeclareReturnTypeAndListFn():
    """카탈로그 원자 3축은 returnType + listFn 을 선언한다 (lane=척추의 순수함수 입력)."""
    entries = _reflect()
    for key in SPINE_ATOMS:
        declared = entries[key].get("declared", {})
        assert declared.get("returnType") == "DataFrame", f"{key} returnType 미선언"
        assert declared.get("listFn"), f"{key} listFn 미선언 (카탈로그 원자 식별 불가)"


def testFalseIsPreservedNotDropped():
    """targetRequired=False 는 유효 선언(전종목 벌크 안전)이라 None 처럼 버리지 않는다."""
    entries = _reflect()
    falses = [
        k
        for k, v in entries.items()
        if isinstance(v.get("declared"), dict) and v["declared"].get("targetRequired") is False
    ]
    assert falses, "targetRequired=False 선언이 하나도 안 실렸다 (False 가 None 처럼 버려짐)"


def testKeysAreStableAndAdditive():
    """키는 '{engine}.{axis}' 로 불변이고 기존 필드(kind/summary)는 그대로 남는다."""
    entries = _reflect()
    engines = {k.split(".", 1)[0] for k in entries}
    assert engines == {p for p, _, _ in _AXIS_REGISTRIES}
    for key, entry in entries.items():
        assert "." in key
        assert entry["kind"].endswith("_axis")
        assert "summary" in entry


def testNonDataclassEntryDoesNotCrash():
    """미래의 비-dataclass 레지스트리는 buildCapabilities 를 죽이지 않고 빈 declared 를 낸다."""

    class Plain:
        label = "x"

    assert _declaredAxisFields(Plain()) == {}
