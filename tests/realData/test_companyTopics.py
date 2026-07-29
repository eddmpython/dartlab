"""Company.panel(topic) 전수 스모크 — registry 등록된 모든 topic 을 iterate.

core/registry 는 37개+ topic 을 자동 등록한다. 이 파일은 매 topic 을
`c.panel(topic)` 으로 호출해 크래시/silent-None 을 잡는다.

과거 회귀: topic/panel 표면이 silent None → 후속 .columns 접근 크래시.
"""

from __future__ import annotations

import pytest


def _allTopics() -> list[str]:
    """registry 에서 자동 수집된 모든 topic 이름."""
    from dartlab.providers.dart.company import _getModuleEntries

    return sorted({e.funcName for e in _getModuleEntries()})


ALL_TOPICS = _allTopics()


# 데이터 부재 시 None/빈 DataFrame 이 허용되는 topic.
# 비상장 성격/소규모 회사에서는 특정 공시 파트가 비어있을 수 있음.
_TOPIC_NONE_ALLOWED: frozenset[str] = frozenset(
    {
        "bond",  # 채무증권 발행 이력 없을 수 있음
        "sanction",  # 제재 이력 없을 수 있음
        "contingentLiability",  # 우발부채 없을 수 있음
        "fundraising",  # 증자감자 이벤트 없을 수 있음
        "investmentInOther",  # 타법인 출자 없을 수 있음
        "riskDerivative",  # 파생상품 없을 수 있음
        "relatedPartyTx",  # 관계자 거래 없을 수 있음
        "affiliate",  # 관계기업 투자 없을 수 있음
        "executivePay",  # 임원보수 공시 안한 경우
        "dividend",  # 무배당 회사
        "otherFinance",  # 기타 재무 없음 가능
        # fixture 한계로 None 허용 (로컬 실데이터에서는 데이터 존재)
        "business",  # 사업의내용 — fixture panel 데이터 한계
        "companyOverviewDetail",  # 회사개요 상세 — 동일
    }
)

# 2026-04-21 Phase D: show() 가 registered-but-empty topic 을 ValueError 대신 None
# 으로 리턴하도록 수정 → 해당 frozenset 비움 (xfail 불필요).
_SHOW_ROUTING_KNOWN_ISSUES: frozenset[str] = frozenset()


@pytest.mark.realData
@pytest.mark.integration
@pytest.mark.parametrize("topic", ALL_TOPICS)
def test_show_topicNoSilentFail(samsungRealData, topic):
    """c.panel(topic) 이 각 topic 에서 크래시하지 않고, None 은 허용 topic 에서만."""
    try:
        result = samsungRealData.panel(topic)
    except NotImplementedError:
        pytest.skip(f"show({topic}) 미구현")
    except ValueError as e:
        if topic in _SHOW_ROUTING_KNOWN_ISSUES and "찾을 수 없습니다" in str(e):
            pytest.xfail(f"show({topic!r}) 기존 라우팅 버그 — registry 등록됐으나 show() 가 ValueError")
        pytest.fail(f"show({topic!r}) 크래시: {type(e).__name__}: {e}")
    except Exception as e:
        pytest.fail(f"show({topic!r}) 크래시: {type(e).__name__}: {e}")

    if result is None:
        if topic in _TOPIC_NONE_ALLOWED:
            return
        pytest.fail(
            f"show({topic!r}) None — 화이트리스트에 없음. "
            f"삼성전자는 충분히 큰 회사여서 빈 topic 이 의심스럽다. "
            f"정말 데이터 없음이 정상이면 _TOPIC_NONE_ALLOWED 에 추가."
        )


@pytest.mark.realData
@pytest.mark.integration
@pytest.mark.parametrize("topic", ALL_TOPICS)
def test_trace_topicNoSilentFail(samsungRealData, topic):
    """c.trace(topic) — 데이터 출처 추적. show 쌍둥이 커버."""
    try:
        result = samsungRealData.trace(topic)
    except NotImplementedError:
        pytest.skip(f"trace({topic}) 미구현")
    except Exception as e:
        pytest.fail(f"trace({topic!r}) 크래시: {type(e).__name__}: {e}")

    # fixture 환경에서는 trace 데이터가 제한적이므로 None 허용 폭을 관대하게.
    # 로컬 실데이터 환경에서만 엄격 검증.
    import os

    inFixtureEnv = "fixtures" in os.environ.get("DARTLAB_DATA_DIR", "")
    if inFixtureEnv:
        return
    # 로컬: show 기반 핵심 topic 만 엄격 검증
    if result is None and topic in {"sections", "business", "mdna", "rnd"}:
        pytest.fail(f"trace({topic!r}) None — 핵심 topic 에서 trace 실종")
