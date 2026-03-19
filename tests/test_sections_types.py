"""sections 타입 유틸 회귀 테스트."""

from dartlab.engines.dart.docs.sections.types import SectionChunk, SectionResult, YearSections


def _section_result_fixture() -> SectionResult:
    return SectionResult(
        corpName="테스트",
        periods=["2024", "2023"],
        yearSections={
            "2024": YearSections(
                year="2024",
                chunks=[
                    SectionChunk(
                        majorNum=1,
                        majorTitle="I",
                        subTitle="주요 경로",
                        path=r"I. 주요 경로\세부(안)",
                        textContent="2024 내용",
                        tableCount=0,
                        tableRowCount=0,
                        tableSummary="",
                        totalChars=5,
                        textChars=5,
                        kind="text",
                    )
                ],
            ),
            "2023": YearSections(
                year="2023",
                chunks=[
                    SectionChunk(
                        majorNum=1,
                        majorTitle="I",
                        subTitle="주요 경로",
                        path=r"I. 주요 경로\세부(안)",
                        textContent="2023 내용",
                        tableCount=0,
                        tableRowCount=0,
                        tableSummary="",
                        totalChars=5,
                        textChars=5,
                        kind="text",
                    )
                ],
            ),
        },
    )


def test_section_result_compare_treats_path_as_literal():
    result = _section_result_fixture()

    compared = result.compare("2024", "2023", path="경로\\세부(안)")

    assert compared.height == 1
    assert compared["path"].to_list() == [r"I. 주요 경로\세부(안)"]


def test_section_result_diff_treats_path_as_literal():
    result = _section_result_fixture()

    diffed = result.diff("2024", "2023", path="경로\\세부(안)")

    assert diffed.height == 2
    assert sorted(diffed["status"].to_list()) == ["added", "removed"]
