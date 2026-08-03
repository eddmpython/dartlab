"""industry gather 표준 axis-dispatch — 옛 호출 ≡ 신 호출 backward-compat 골든.

industry 를 gather(axis, target) 표준으로 통일하되 옛 형식(industryId-first + 플래그 + 메서드)이
계속 동작하는지 고정. 신 형식 industry("summary","semiconductor") == 옛 industry("semiconductor",
summary=True) 동치.
"""

from __future__ import annotations

import pytest

from dartlab.industry import _AXIS_REGISTRY, Industry


def test_axis_registry_covers_flags_and_methods():
    """_AXIS_REGISTRY 가 옛 플래그 6종 + 메서드 3종(edges/map/theme)을 축으로 포함."""
    axes = set(_AXIS_REGISTRY)
    assert {"summary", "timeline", "lifecycle", "concentration", "dynamics", "polarization"} <= axes
    assert {"edges", "map", "theme"} <= axes


@pytest.mark.requires_data
def test_guide_and_backward_compat_industryId():
    """industry() 산업목록 가이드(불변) + industry("semiconductor") 옛 형식 동작."""
    ind = Industry()
    guide = ind()
    assert set(guide.columns) >= {"산업ID", "산업명", "공정수"}  # 옛 가이드 불변
    assert ind("semiconductor").height > 0  # 옛 industryId-first


@pytest.mark.requires_data
def test_old_flag_equals_new_axis():
    """옛 플래그 ≡ 신 축 — 동일 DataFrame."""
    ind = Industry()
    for axis in ("summary", "timeline", "lifecycle", "concentration", "dynamics", "polarization"):
        old = ind("semiconductor", **{axis: True})  # 옛: industry(id, flag=True)
        new = ind(axis, "semiconductor")  # 신: industry(axis, target)
        assert old.equals(new), f"{axis} 옛≠신"


@pytest.mark.requires_data
def test_method_equals_axis():
    """메서드 ≡ 축 — edges/theme 동일."""
    ind = Industry()
    assert ind.edges("semiconductor").equals(ind("edges", "semiconductor"))
    assert ind.theme("secondaryBattery").equals(ind("theme", "secondaryBattery"))
    assert ind.theme(stockCode="051910").equals(ind("theme", stockCode="051910"))


@pytest.mark.requires_data
def test_old_stage_positional_preserved():
    """옛 2번째 positional = stage 유지 — industry("semiconductor", "<stage>")."""
    ind = Industry()
    full = ind("semiconductor")
    stage = full["공정"][0] if "공정" in full.columns and full.height else None
    if stage:
        filtered = ind("semiconductor", stage)  # 옛: (industryId, stage)
        assert filtered.height <= full.height


def test_korean_axis_label_resolves_like_macro():
    """가이드가 광고하는 한글 라벨(집중도 등)이 축으로 해소된다.

    실측 회귀: industry("집중도", "semiconductor") 가 registry 미스로
    backward-compat industryId 경로에 새서 조용한 빈 DataFrame 을 냈다.
    """
    from dartlab.industry import _AXIS_LABEL_TO_KEY

    assert _AXIS_LABEL_TO_KEY["집중도"] == "concentration"
    assert set(_AXIS_LABEL_TO_KEY.values()) == set(_AXIS_REGISTRY)


@pytest.mark.requires_data
def test_korean_label_and_english_key_dispatch_identically():
    ind = Industry()
    assert ind("집중도", "semiconductor").equals(ind("concentration", "semiconductor"))


def test_unknown_first_arg_rejected_with_guidance():
    """미지 축·industryId 는 조용한 빈 결과 대신 유효 목록과 함께 거절된다."""
    ind = Industry()
    with pytest.raises(ValueError, match="등록된 industryId"):
        ind("없는축이름", "semiconductor")
