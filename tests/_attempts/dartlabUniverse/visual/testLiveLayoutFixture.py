"""U0-V02 live bounded scene fixture 회귀 테스트."""

from __future__ import annotations

from tests._attempts.dartlabUniverse.visual.liveLayoutFixture import loadLiveLayoutFixtures


def testLiveLayoutFixtureReusesThreeBoundedScenes() -> None:
    """Live fixture가 세 bounded scene identity와 상한을 재사용하는지 검증한다.

    Capabilities
        Scene 순서, output node count, scene hash 형식을 회귀 검증한다.
    AIContext
        AI 역할: 별도 visual graph 사본 생성을 허용하지 않는다.
    Args
        없음.
    Returns
        없음.
    Guide
        U0-P01 bound가 의도적으로 바뀌면 projection 결과와 함께 갱신한다.
    When
        Live fixture adapter 또는 projection compiler가 바뀔 때 실행한다.
    How
        Current artifact를 load한 결과를 exact expected count와 비교한다.
    Requires
        Public map artifact 접근이 필요하다.
    Raises
        AssertionError: Scene identity, count, hash 계약이 다를 때 발생한다.
    Example
        ``pytest testLiveLayoutFixture.py``
    See Also
        :func:`loadLiveLayoutFixtures`.
    """

    fixtures = loadLiveLayoutFixtures()

    assert [fixture["sceneName"] for fixture in fixtures] == ["atlas", "industry", "company"]
    assert [fixture["outputNodeCount"] for fixture in fixtures] == [18, 26, 50]
    assert all(fixture["sourceSceneHash"].startswith("sha256:") for fixture in fixtures)


def testLiveLayoutFixturePreservesCandidateAndTimeGap() -> None:
    """Candidate lane과 valid time 결손이 그대로 보존되는지 검증한다.

    Capabilities
        Status, validOrder, semantic stage allowlist를 회귀 검증한다.
    AIContext
        AI 역할: current relation을 fact로 승격하거나 시간을 합성하지 않는다.
    Args
        없음.
    Returns
        없음.
    Guide
        Valid time source가 생기기 전 None expectation을 완화하지 않는다.
    When
        Live fixture 의미 변환 또는 source schema가 바뀔 때 실행한다.
    How
        세 scene node 전체의 lane과 time 값을 집계한다.
    Requires
        Public map artifact 접근이 필요하다.
    Raises
        AssertionError: Candidate 또는 time gap 계약이 손실될 때 발생한다.
    Example
        ``pytest testLiveLayoutFixture.py -k TimeGap``
    See Also
        :func:`loadLiveLayoutFixtures`.
    """

    fixtures = loadLiveLayoutFixtures()
    nodes = [node for fixture in fixtures for node in fixture["nodes"]]

    assert nodes
    assert {node["status"] for node in nodes} == {"candidate"}
    assert all(node["validOrder"] is None for node in nodes)
    assert {node["stage"] for node in nodes}.issubset({"upstream", "midstream", "downstream", "unknown"})
    assert any(node["stage"] != "unknown" for node in nodes)
