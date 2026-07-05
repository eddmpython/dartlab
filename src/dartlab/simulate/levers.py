"""엣지 레버 원장 : 문헌 근거 레버를 1급 표면으로 선언 (L2.5 simulate).

06 §3 전수 등재를 대체하지 않는다 (등재는 여전히 카탈로그 자동 전수). 본 원장은 문헌이 방향·
정제·우선순위 근거를 주는 표면들의 선언 원장이며(10), 각 레버를 개별 표면(lever.<id>)으로 내
인증 깔때기(certify)가 도태시킨다. 방향은 문헌 prior 가 아니라 데이터(deriveEventDirections
게이트)가 정한다. 문헌 방향은 red-flag(회피) 분류·refs 용 prior 일 뿐이다. do-not-build 레버
(US PEAD 사망·US 지수효과 붕괴)는 원장에 status="doNotBuild" 로 남기되 판독을 발행하지 않는다
(문헌이 죽었다고 실증된 것을 굽지 않는다). 비용 바닥 전제 = 왕복 ~1.0%/주, 회피 신호는 비용 0.

- ``LEVER_LEDGER`` : 레버 선언 원장 (leverId·이벤트타입·문헌방향·정제·status·근거).
- ``leverSurfaces`` : 수확 가능 레버의 SurfaceSpec (인증 대상 등재).
- ``leverReadings`` : 이벤트에서 레버별 판독(surface=lever.<id>) 발행 (봉인·채점 계약 동일).

Layer: L2.5 simulate. surfaces·reading 만 의존 (하향). 신규 데이터 수집 0 (allFilings 재조합).
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from dartlab.simulate.reading import SurfaceSpec


@dataclass(frozen=True)
class LeverSpec:
    """레버 선언 1행 (10 §1). 문헌 방향은 prior, 실방향은 데이터 게이트가 정한다.

    Args:
        leverId: 레버 식별자 (표면 id = "lever.<leverId>").
        label: 사람 라벨.
        eventTypes: 매칭할 v2 정규화 이벤트 타입 (allFilings). 빈 튜플 = 파생 신호(가격·재무).
        literatureDirection: "long" | "avoid" | "feature" 문헌 prior (red-flag 분류·refs 용).
        refinement: 정제 규율 (예 "취득만·역할·군집·비정기").
        status: "harvestable"(오늘 데이터로 판독) | "awaitingMeasurement"(정제 데이터 대기) |
            "doNotBuild"(문헌 사망 실증, 굽지 않음).
        provenance: 문헌·원천 근거.
    """

    leverId: str
    label: str
    eventTypes: tuple[str, ...]
    literatureDirection: str
    refinement: str
    status: str
    provenance: str


# 10 §1~§1b 레버 원장 (문헌 검증 [V]/[K] 는 provenance 에). do-not-build 은 실증된 사망만.
LEVER_LEDGER: tuple[LeverSpec, ...] = (
    LeverSpec(
        "insiderBuy",
        "임원·주요주주 매수 정제",
        ("임원ㆍ주요주주특정증권등소유상황보고서",),
        "long",
        "취득만·역할(CEO/CFO)·규모/시총·복수내부자 군집·비정기 필터",
        "awaitingMeasurement",
        "Cohen-Malloy-Pomorski JF2012 [V]. Form4 P/S 코드(US 직행)",
    ),
    LeverSpec(
        "treasuryAcquire",
        "자사주 직접취득·소각",
        ("자기주식취득결정",),
        "long",
        "직접>신탁, 소각 최강",
        "harvestable",
        "KR 3일 CAR +1.60% [V]",
    ),
    LeverSpec(
        "treasuryDispose",
        "자사주 처분",
        ("자기주식처분결정",),
        "avoid",
        "처분은 red flag",
        "harvestable",
        "KR 자사주 처분 음(-) [V]",
    ),
    LeverSpec(
        "cbChain",
        "CB/BW 사슬 래더",
        ("전환사채권발행결정", "신주인수권부사채권발행결정", "전환청구권행사"),
        "avoid",
        "리픽싱 조항·연쇄 발행사 = 가치파괴. 단마다 판독",
        "harvestable",
        "KR 전환청구 -2.7%/5d 실측 [V]",
    ),
    LeverSpec(
        "rightsOffering",
        "유상증자 희석",
        ("유상증자결정",),
        "avoid",
        "자금조달 이력 조건부(CB 이력 = 드리프트 1.5배)",
        "harvestable",
        "사내 실측 유상증자 -2.0~3.6%/D10",
    ),
    LeverSpec(
        "capitalReduction", "감자 연쇄", ("감자결정",), "avoid", "감자=자본잠식 신호", "harvestable", "KR 실증 [K]"
    ),
    LeverSpec(
        "bonusIssueFade",
        "무상증자 사슬",
        ("무상증자결정",),
        "avoid",
        "발표 pop(D0~1)은 포기, 권리락 후 fade 만",
        "harvestable",
        "신흥시장 ~6d 지속 [V]",
    ),
    LeverSpec(
        "supplyContract",
        "단일판매·공급계약",
        ("단일판매ㆍ공급계약체결",),
        "long",
        "계약 규모/시총 비율, 이후 fade",
        "harvestable",
        "공급계약 프리미엄 [K]",
    ),
    LeverSpec(
        "adminIssue", "관리종목 지정 예측", ("관리종목지정",), "avoid", "지정 = 상폐 선행", "harvestable", "KR 실증 [K]"
    ),
    LeverSpec(
        "embezzlement",
        "횡령·배임 회피",
        ("횡령ㆍ배임혐의발생", "횡령ㆍ배임사실확인"),
        "avoid",
        "영구 회피(비복구)",
        "harvestable",
        "거버넌스 red flag [K]",
    ),
    LeverSpec(
        "majorHolderChange",
        "최대주주 변경",
        ("최대주주변경",),
        "avoid",
        "지배구조 불안정",
        "harvestable",
        "거버넌스 [K]",
    ),
    LeverSpec(
        "auditDelay",
        "감사지연 red flag",
        (),
        "avoid",
        "법정기한 대비 접수 지연 = 의견거절·관리종목 선행. 타임스탬프 파생",
        "awaitingMeasurement",
        "US NT 10-K/10-Q 대응 [K]. 사내 실측 선행",
    ),
    LeverSpec(
        "lockupExpiry",
        "락업 만료 회피",
        ("증권신고서",),
        "avoid",
        "발행 주 + 표준 락업(26주) = 만료 주 회피 (leverRefine, 정밀 확약 파싱은 미보유)",
        "harvestable",
        "Field-Hanka 계열 [V/K]",
    ),
    LeverSpec(
        "maxLottery",
        "MAX/복권 회피",
        (),
        "avoid",
        "가격만(일별 MAX). 롱북 스크린",
        "awaitingMeasurement",
        "Bali-Cakici-Whitelaw JFE2011 + KR Nartea [V]",
    ),
    LeverSpec(
        "indexInclusion",
        "지수 편입 예측",
        (),
        "long",
        "시총 랭크 편입 경계 밴드 근방 = 편입 후보 (leverRefine.indexInclusionReadings)",
        "harvestable",
        "KR +11.5% 실무 [V]",
    ),
    LeverSpec(
        "insiderCluster",
        "내부자 매수 군집 정제",
        ("임원ㆍ주요주주특정증권등소유상황보고서",),
        "long",
        "복수내부자 군집·비정기 = 공시 빈도로 도출 (leverRefine, P/S 코드는 미보유)",
        "harvestable",
        "Cohen-Malloy-Pomorski JF2012 [V]",
    ),
    LeverSpec(
        "earSueCombo",
        "실적 서프라이즈 (SUE+EAR)",
        (),
        "long",
        "SRW SUE + 발표창 초과수익 ABR. EAR 만 생존",
        "awaitingMeasurement",
        "PEAD-lite 무조건부 [V]",
    ),
    # do-not-build: 문헌 사망 실증 (굽지 않음).
    LeverSpec(
        "usPead",
        "US PEAD",
        (),
        "long",
        "대형주 2006~ 사망·2016~ 반전",
        "doNotBuild",
        "Martineau 계열 = do-not-build [V]",
    ),
    LeverSpec(
        "usIndexInclusion",
        "US 지수효과",
        (),
        "long",
        "+7.4%->1% 붕괴",
        "doNotBuild",
        "Greenwood-Sammon = do-not-build [V]",
    ),
)


def leverSurfaces() -> list[SurfaceSpec]:
    """수확 가능(harvestable) 레버의 SurfaceSpec (인증 대상 등재). do-not-build·대기는 제외."""
    out = []
    for lv in LEVER_LEDGER:
        if lv.status != "harvestable" or not lv.eventTypes:
            continue
        out.append(
            SurfaceSpec(
                surface=f"lever.{lv.leverId}",
                axis="event",
                kind="directional",
                directional=None,  # 방향은 deriveEventDirections 게이트가 채운다 (데이터 우선)
                naturalHorizon=5,
                provenance=("dart.allFilings", lv.provenance),
            )
        )
    return out


def leverReadings(eventMatrix: pl.DataFrame, directionByType: dict[str, int] | None = None) -> pl.DataFrame:
    """이벤트 → 레버별 판독 (surface=lever.<id>). 각 레버가 개별 표면 = 인증 깔때기 대상.

    Args:
        eventMatrix: (code, week, reportType) v2 정규화.
        directionByType: {reportType: +1|-1} 데이터 방향 사전 (없으면 문헌 prior 로 회피 신호만).

    Returns:
        (code, week, surface, direction, score). 레버마다 매칭 이벤트 타입 발생 시 발행. 방향은
        데이터 게이트 우선, 미도출 타입은 문헌 avoid prior 로 -1 (red-flag). do-not-build 레버 무발행.
    """
    dbt = directionByType or {}
    out = []
    for lv in LEVER_LEDGER:
        if lv.status == "doNotBuild" or not lv.eventTypes:
            continue
        sub = eventMatrix.filter(pl.col("reportType").is_in(list(lv.eventTypes)))
        if sub.height == 0:
            continue
        prior = -1 if lv.literatureDirection == "avoid" else (1 if lv.literatureDirection == "long" else 0)
        typeDir = {t: dbt.get(t) for t in lv.eventTypes}
        agg = (
            sub.with_columns(dir=pl.col("reportType").replace_strict(typeDir, default=None).fill_null(prior))
            .group_by(["code", "week"])
            .agg(direction=pl.col("dir").sum().sign().cast(pl.Int64))
        )
        out.append(
            agg.with_columns(surface=pl.lit(f"lever.{lv.leverId}"), score=(pl.col("direction") + 1) / 2).select(
                "code", "week", "surface", "direction", "score"
            )
        )
    if not out:
        return pl.DataFrame(
            schema={"code": pl.Utf8, "week": pl.Int64, "surface": pl.Utf8, "direction": pl.Int64, "score": pl.Float64}
        )
    return pl.concat(out)
