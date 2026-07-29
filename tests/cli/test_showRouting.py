"""c.panel() 라우팅 회귀 테스트 — Phase D 근본 수정 방어.

========================================
이 파일이 잡는 버그 클래스 (2026-04-20~21 사고):
========================================
`_showImpl` 가 "registry 에는 등록됐는데 sections DataFrame 에 없고, fallback
_showDirectTopic 도 None 리턴" 상황에서 일괄 `ValueError: '...' 찾을 수 없습니다`
를 raise 했다. 이로 인해 bond/business/fundraising/companyOverviewDetail 같은
합법적으로 "데이터 없는" 회사에서도 `c.panel("bond")` 가 크래시.

Phase D 수정: registered-but-empty 는 None 리턴, truly-unknown 만 warn+None.

이 테스트는 해당 동작을 전수 parametrize 로 보장한다. 새 topic 추가 시 자동
iterate 범위에 포함.
"""

from __future__ import annotations

import warnings

import polars as pl
import pytest

from tests.conftest import SAMSUNG, _has_data, requires_samsung

pytestmark = [pytest.mark.integration, requires_samsung]


def _registeredTopics() -> list[str]:
    """registry 에 등록된 report/disclosure topic 전수."""
    from dartlab.providers.dart.company import _getModuleEntries

    return sorted(e.funcName for e in _getModuleEntries() if e.category in ("report", "disclosure"))


REGISTERED_TOPICS = _registeredTopics()


@pytest.fixture(scope="module")
def samsungCompany():
    """삼성전자 Company — 모듈 scope 로 재사용."""
    import gc

    if not _has_data(SAMSUNG, "panel"):
        pytest.skip("삼성전자 panel 데이터 없음")
    from dartlab import Company

    c = Company(SAMSUNG)
    yield c
    del c
    gc.collect()


@pytest.mark.parametrize("topic", REGISTERED_TOPICS)
def test_show_registeredTopic_noValueError(samsungCompany, topic):
    """registry 에 등록된 모든 topic 에 대해 show(topic) 이 ValueError 없이 동작.

    데이터가 없는 경우 (fixture 한계 등) 는 None 리턴 OK. ValueError 는 오직
    truly-unknown topic (registry 미등록) 에 대해서만 허용.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            result = samsungCompany.panel(topic)
        except ValueError as e:
            pytest.fail(f"show({topic!r}) ValueError — registry 에 등록된 topic 인데도 라우팅 실패: {e}")
        except NotImplementedError:
            pytest.skip(f"show({topic!r}) 미구현")
        except Exception as e:
            pytest.fail(f"show({topic!r}) 예상 외 크래시: {type(e).__name__}: {e}")

    # None 또는 DataFrame 모두 허용 — ValueError 안 나면 OK.
    assert result is None or isinstance(result, pl.DataFrame)


def test_show_unknownTopic_warnsButNoCrash(samsungCompany):
    """registry 에 없는 topic 은 warning + None (크래시 없음)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            result = samsungCompany.panel("definitely_not_a_real_topic_xyz123")
        except Exception as e:
            pytest.fail(f"unknown topic 에서 예상 외 크래시: {type(e).__name__}: {e}")
        # 결과는 None, warning 이 발생했을 수 있음 (엄격히 요구하진 않음)
    assert result is None
