"""횡단면·패널 회귀 매출 예측 엔진.

횡단면 회귀: 같은 시점에 전 상장사 데이터를 모아 매출 성장률을 설명.
패널 회귀: 여러 연도를 쌓아 기업 고정효과(fixed effect)로 기업 특성 통제.

모든 구현은 순수 Python (외부 ML 라이브러리 의존 없음).
사전 적합(pre-fit) 후 JSON 캐시 → 개별 기업 예측은 즉시 계산.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from dartlab.core.finance.ols import olsMulti as _olsMulti

log = logging.getLogger(__name__)

_MODEL_CACHE_DIR = Path.home() / ".dartlab" / "models"

# 횡단면 회귀 피처 목록 (순서 고정)
FEATURES = [
    "per",
    "pbr",
    "lnMarketCap",
    "operatingMargin",
    "capexRatio",
    "debtRatio",
    "foreignHoldingRatio",
    "revenueGrowthLag",
]


@dataclass
class CrossSectionModel:
    """횡단면 회귀 모델 — 사전 적합 결과."""

    year: int
    coefficients: list[float]  # [intercept, β1, β2, ..., β_sector1, ...]
    featureNames: list[str]  # FEATURES + 섹터 더미 이름
    rSquared: float
    adjRSquared: float
    nObs: int
    sectorNames: list[str]  # 섹터 더미로 사용된 섹터 목록 (첫 번째 제외 = reference)
    warnings: list[str] = field(default_factory=list)

    def predict(self, features: dict[str, float], sector: str = "") -> float | None:
        """개별 기업의 매출 성장률 예측 (%).

        features dict 키: FEATURES 목록과 동일.
        sector: WICS 업종명 (sectorNames에 있으면 해당 더미 1, 아니면 0).
        """
        if not self.coefficients:
            return None

        x = []
        for fname in FEATURES:
            v = features.get(fname)
            if v is None:
                return None
            x.append(v)

        # 섹터 더미
        for sname in self.sectorNames:
            x.append(1.0 if sector == sname else 0.0)

        if len(x) + 1 != len(self.coefficients):
            log.debug("피처 수 불일치: x=%d, coeffs=%d", len(x) + 1, len(self.coefficients))
            return None

        # intercept + β·x
        pred = self.coefficients[0]
        for i, xi in enumerate(x):
            pred += self.coefficients[i + 1] * xi

        return pred


@dataclass
class PanelModel:
    """패널 회귀 모델 (기업 고정효과)."""

    coefficients: list[float]  # [β1, β2, ...] (절편 없음 — demeaned)
    featureNames: list[str]
    rSquared: float
    nObs: int
    nFirms: int
    firmIntercepts: dict[str, float]  # 기업별 절편 (고정효과)
    grandMean: float  # 전체 평균 성장률

    def predict(self, stockCode: str, features: dict[str, float]) -> float | None:
        """기업 고정효과 + 변수 효과 → 매출 성장률 예측."""
        x = []
        for fname in self.featureNames:
            v = features.get(fname)
            if v is None:
                return None
            x.append(v)

        if len(x) != len(self.coefficients):
            return None

        alpha = self.firmIntercepts.get(stockCode, self.grandMean)
        pred = alpha
        for i, xi in enumerate(x):
            pred += self.coefficients[i] * xi
        return pred


@dataclass
class CompanyFeatures:
    """횡단면/패널 회귀에 사용할 기업별 피처."""

    stockCode: str
    year: int
    sector: str
    revenueGrowth: float  # 종속변수: 매출 성장률 (%)
    per: float
    pbr: float
    lnMarketCap: float
    operatingMargin: float
    capexRatio: float
    debtRatio: float
    foreignHoldingRatio: float
    revenueGrowthLag: float  # 전년 매출 성장률

    def toFeatureDict(self) -> dict[str, float]:
        """FEATURES 순서에 맞는 dict 반환."""
        return {
            "per": self.per,
            "pbr": self.pbr,
            "lnMarketCap": self.lnMarketCap,
            "operatingMargin": self.operatingMargin,
            "capexRatio": self.capexRatio,
            "debtRatio": self.debtRatio,
            "foreignHoldingRatio": self.foreignHoldingRatio,
            "revenueGrowthLag": self.revenueGrowthLag,
        }

    def toFeatureVector(self) -> list[float]:
        """FEATURES 순서의 float 리스트."""
        d = self.toFeatureDict()
        return [d[f] for f in FEATURES]


# ══════════════════════════════════════════════════════════
# 횡단면 회귀 적합
# ══════════════════════════════════════════════════════════


def fitCrossSection(
    observations: list[CompanyFeatures],
    *,
    minObs: int = 30,
    winsorize: float = 0.02,
) -> CrossSectionModel | None:
    """전 상장사 횡단면 회귀 적합.

    Parameters
    ----------
    observations : 같은 연도의 CompanyFeatures 리스트
    minObs : 최소 관측치 수
    winsorize : 양쪽 꼬리 절사 비율 (기본 2%)
    """
    if len(observations) < minObs:
        return None

    year = observations[0].year

    # 이상치 제거 (winsorize)
    obs = _winsorizeObs(observations, winsorize)

    # 섹터 더미 구성
    sectors = sorted({o.sector for o in obs if o.sector})
    sectorRef = sectors[0] if sectors else ""
    sectorDummies = sectors[1:] if len(sectors) > 1 else []

    # X, y 구성
    X: list[list[float]] = []
    y: list[float] = []
    for o in obs:
        row = o.toFeatureVector()
        # 섹터 더미 추가
        for sd in sectorDummies:
            row.append(1.0 if o.sector == sd else 0.0)
        X.append(row)
        y.append(o.revenueGrowth)

    # OLS 적합
    result = _olsMulti(X, y, addIntercept=True)
    if result is None:
        return None

    featureNames = list(FEATURES) + sectorDummies
    warnings: list[str] = []
    if result.rSquared < 0.05:
        warnings.append(f"R² 매우 낮음 ({result.rSquared:.3f}) — 예측력 제한적")

    return CrossSectionModel(
        year=year,
        coefficients=result.coefficients,
        featureNames=featureNames,
        rSquared=result.rSquared,
        adjRSquared=result.adjRSquared,
        nObs=result.nObs,
        sectorNames=sectorDummies,
        warnings=warnings,
    )


# ══════════════════════════════════════════════════════════
# 패널 회귀 적합 (기업 고정효과)
# ══════════════════════════════════════════════════════════


def fitPanel(
    observations: list[CompanyFeatures],
    *,
    minObs: int = 50,
    minYears: int = 3,
) -> PanelModel | None:
    """패널 회귀 (within estimator — 기업 고정효과).

    각 변수에서 기업 평균을 빼고(demean) OLS 적합.
    기업별 절편(αi) = 기업 평균 y - β · 기업 평균 X.
    """
    if len(observations) < minObs:
        return None

    years = {o.year for o in observations}
    if len(years) < minYears:
        return None

    # 기업별 그룹핑
    firmObs: dict[str, list[CompanyFeatures]] = {}
    for o in observations:
        firmObs.setdefault(o.stockCode, []).append(o)

    # 기업별 평균 계산 + demeaning
    xDemeaned: list[list[float]] = []
    yDemeaned: list[float] = []
    firmMeanY: dict[str, float] = {}
    firmMeanX: dict[str, list[float]] = {}

    for code, oList in firmObs.items():
        if len(oList) < 2:
            continue

        # 기업 평균
        nF = len(FEATURES)
        meanX = [0.0] * nF
        meanY = 0.0
        for o in oList:
            vec = o.toFeatureVector()
            for j in range(nF):
                meanX[j] += vec[j]
            meanY += o.revenueGrowth
        cnt = len(oList)
        meanX = [v / cnt for v in meanX]
        meanY /= cnt

        firmMeanY[code] = meanY
        firmMeanX[code] = meanX

        # demeaning
        for o in oList:
            vec = o.toFeatureVector()
            xDemeaned.append([vec[j] - meanX[j] for j in range(nF)])
            yDemeaned.append(o.revenueGrowth - meanY)

    if len(xDemeaned) < minObs:
        return None

    # demeaned OLS (절편 없음)
    result = _olsMulti(xDemeaned, yDemeaned, addIntercept=False)
    if result is None:
        return None

    # 기업별 절편 복원: αi = meanY_i - β · meanX_i
    firmIntercepts: dict[str, float] = {}
    for code in firmMeanY:
        alpha = firmMeanY[code]
        for j, beta in enumerate(result.coefficients):
            alpha -= beta * firmMeanX[code][j]
        firmIntercepts[code] = alpha

    grandMean = sum(firmMeanY.values()) / len(firmMeanY) if firmMeanY else 0.0

    return PanelModel(
        coefficients=result.coefficients,
        featureNames=list(FEATURES),
        rSquared=result.rSquared,
        nObs=result.nObs,
        nFirms=len(firmMeanY),
        firmIntercepts=firmIntercepts,
        grandMean=grandMean,
    )


# ══════════════════════════════════════════════════════════
# 모델 캐시 (일 1회 사전 적합 → JSON → 즉시 로드)
# ══════════════════════════════════════════════════════════


def saveModel(model: CrossSectionModel) -> Path:
    """횡단면 모델 JSON 저장."""
    _MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _MODEL_CACHE_DIR / f"crossSection_{model.year}.json"
    data = {
        "year": model.year,
        "coefficients": model.coefficients,
        "featureNames": model.featureNames,
        "rSquared": model.rSquared,
        "adjRSquared": model.adjRSquared,
        "nObs": model.nObs,
        "sectorNames": model.sectorNames,
        "warnings": model.warnings,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("CrossSection 모델 저장: %s (%d obs, R²=%.3f)", path, model.nObs, model.rSquared)
    return path


def loadModel(year: int) -> CrossSectionModel | None:
    """캐시된 횡단면 모델 로드."""
    path = _MODEL_CACHE_DIR / f"crossSection_{year}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return CrossSectionModel(**data)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        log.debug("CrossSection 모델 로드 실패: %s — %s", path, e)
        return None


def savePanelModel(model: PanelModel) -> Path:
    """패널 모델 JSON 저장."""
    _MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _MODEL_CACHE_DIR / "panel_latest.json"
    data = {
        "coefficients": model.coefficients,
        "featureNames": model.featureNames,
        "rSquared": model.rSquared,
        "nObs": model.nObs,
        "nFirms": model.nFirms,
        "firmIntercepts": model.firmIntercepts,
        "grandMean": model.grandMean,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Panel 모델 저장: %s (%d obs, %d firms)", path, model.nObs, model.nFirms)
    return path


def loadPanelModel() -> PanelModel | None:
    """캐시된 패널 모델 로드."""
    path = _MODEL_CACHE_DIR / "panel_latest.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return PanelModel(**data)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        log.debug("Panel 모델 로드 실패: %s — %s", path, e)
        return None


# ══════════════════════════════════════════════════════════
# 내부 유틸
# ══════════════════════════════════════════════════════════


def _winsorizeObs(
    obs: list[CompanyFeatures],
    pct: float,
) -> list[CompanyFeatures]:
    """종속변수(revenueGrowth) 양쪽 꼬리 절사."""
    if pct <= 0 or len(obs) < 10:
        return obs

    growths = sorted(o.revenueGrowth for o in obs)
    n = len(growths)
    loIdx = max(int(n * pct), 1)
    hiIdx = min(int(n * (1 - pct)), n - 1)
    lo = growths[loIdx]
    hi = growths[hiIdx]

    return [o for o in obs if lo <= o.revenueGrowth <= hi]
