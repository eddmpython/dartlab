"""폐기 예정 접근자의 안내가 실제로 도는 경로를 가리킨다는 계약.

예전 문구는 `report.dividend → panel('dividend')` 처럼 영문 축을 권했는데 그 축은
없어서 `panel` 이 None 을 돌려준다. 실측으로 dividend·employee·majorHolder·executive
넷 다 옛 접근자는 실데이터(40·84·167·8 행)를 주고 권장 경로는 None 이었다. 안내를
따르면 자료를 잃는다. panel 의 공시 본문과 이 API 표는 애초에 다른 것이라 옮겨 갈
자리가 아니었다.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

_DEPRECATED = ("dividend", "employee", "majorHolder", "executive", "audit")


def test_hint_namesAContractCall():
    """안내 문구가 계약 호출을 가리킨다."""
    from dartlab.providers.dart.accessor.reportAccessor import _deprecationHint

    hint = _deprecationHint("dividend", "c.capital() (DPS·배당수익률)")

    assert "report.dividend" in hint
    assert "c.capital()" in hint


def test_hints_doNotPointAtEnglishPanelAxis():
    """영문 panel 축을 권하지 않는다. 그 축은 존재하지 않아 None 이 나온다.

    경고를 내는 줄만 본다. 설명 docstring 은 옛 문구를 인용하므로 대상이 아니다.
    """
    import pathlib

    from dartlab.providers.dart.accessor import reportAccessor

    lines = pathlib.Path(reportAccessor.__file__).read_text(encoding="utf-8").splitlines()
    warnLines = [ln for ln in lines if "warnings.warn(" in ln]
    assert warnLines, "경고 호출을 못 찾았다"
    for name in _DEPRECATED:
        bad = [ln for ln in warnLines if f"panel('{name}')" in ln]
        assert not bad, f"report.{name} 안내가 없는 영문 축을 권한다: {bad}"
