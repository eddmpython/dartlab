"""기업분석 보고서 발간 파이프라인.

review 엔진(6막 서사 + 스토리 템플릿)으로 생성한 기업분석보고서를
블로그 포스트 형태로 blog/05-company-reports/에 저장한다.

credit/publisher.py와 동일 패턴이지만 보고서 성격이 다르다:
- credit: 7축 신용등급 + 12섹션 정량 보고서
- review: 6막 인과 서사 + 업종별 스토리 템플릿 기반 종합 분석
"""

from __future__ import annotations

import gc
import json
from datetime import datetime
from pathlib import Path

_BLOG_DIR = Path("blog/05-company-reports")
_REGISTRY_PATH = _BLOG_DIR / "_registry.json"


def publishReport(
    stockCode: str,
    *,
    template: str = "auto",
    basePeriod: str | None = None,
) -> Path:
    """기업분석 보고서 발간.

    1. Company 로드 + 스토리 템플릿 자동 판별
    2. review(template=template, detail=True) 빌드
    3. frontmatter + 보고서 헤더 + 본문 마크다운 생성
    4. blog/05-company-reports/{순번}-{종목코드}-{기업명}/index.md 저장
    5. _registry.json 업데이트
    """
    from dartlab import Company

    company = Company(stockCode)
    path = publishReportFromCompany(company, template=template, basePeriod=basePeriod)
    del company
    gc.collect()
    return path


def publishReportFromCompany(
    company,
    *,
    template: str = "auto",
    basePeriod: str | None = None,
) -> Path:
    """Company 객체로 보고서 생성 + 블로그 포스트 저장."""
    from dartlab.review.registry import buildReview

    rv = buildReview(company, template=template, detail=True, basePeriod=basePeriod)

    corpName = getattr(company, "corpName", "") or ""
    stockCode = getattr(company, "stockCode", "") or ""
    sector = _extractSector(company)

    # credit 등급 참조 (실패해도 계속)
    grade = _extractCreditGrade(company)

    # 마크다운 생성
    md = _buildFullReport(rv, corpName, stockCode, sector, grade, basePeriod)

    # 블로그 포스트 저장
    order, slug = _resolveSlug(stockCode, corpName)
    postDir = _BLOG_DIR / f"{order:02d}-{slug}"
    postDir.mkdir(parents=True, exist_ok=True)
    path = postDir / "index.md"
    path.write_text(md, encoding="utf-8")

    # 레지스트리 업데이트
    _updateRegistry(stockCode, corpName, order, slug, rv, grade)

    return path


def publishBatch(
    stockCodes: list[str],
    *,
    template: str = "auto",
    basePeriod: str | None = None,
) -> list[Path]:
    """배치 발간 (순차 — 메모리 안전)."""
    paths = []
    for i, code in enumerate(stockCodes):
        try:
            path = publishReport(code, template=template, basePeriod=basePeriod)
            paths.append(path)
            if (i + 1) % 5 == 0:
                print(f"[review] {i + 1}/{len(stockCodes)} 발간 완료")
        except (ValueError, KeyError, TypeError, FileNotFoundError) as e:
            print(f"[review] {code} 발간 실패: {e}")
        gc.collect()
    print(f"[review] 배치 완료: {len(paths)}/{len(stockCodes)} 성공")
    return paths


# ── 내부 함수 ──


def _buildFullReport(
    review,
    corpName: str,
    stockCode: str,
    sector: str,
    grade: str,
    basePeriod: str | None,
) -> str:
    """frontmatter + 보고서 헤더 + 본문 마크다운 결합."""
    templateName = getattr(review, "template", None) or ""
    today = datetime.now().strftime("%Y-%m-%d")
    periodLabel = basePeriod or "최신"

    # frontmatter
    title = f"{corpName} — {_makeTitle(templateName, corpName)}"
    description = f"{corpName} 6막 재무 서사 — 수익구조부터 가치평가까지."
    if templateName:
        from dartlab.review.templates import STORY_TEMPLATES

        tmplDesc = STORY_TEMPLATES.get(templateName, {}).get("description", "")
        if tmplDesc:
            description += f" {tmplDesc}."

    fm = (
        "---\n"
        f'title: "{title}"\n'
        f"date: {today}\n"
        f'description: "{description}"\n'
        f"category: company-reports\n"
        f"series: company-reports\n"
        f'stockCode: "{stockCode}"\n'
        f'corpName: "{corpName}"\n'
    )
    if templateName:
        fm += f'storyTemplate: "{templateName}"\n'
    if sector:
        fm += f'sector: "{sector}"\n'
    if grade:
        fm += f'grade: "{grade}"\n'
    fm += "---\n\n"

    # 보고서 헤더
    header = f"> **{templateName or '종합'}** | {sector or '—'} | {today} 기준\n"
    header += f"> 데이터: {periodLabel} 연결 | 엔진: dartlab review\n"
    header += "\n---\n"

    # 본문
    body = review.toMarkdown()

    # credit 보고서 링크 (있으면)
    creditLink = ""
    creditPostDir = Path("blog/04-credit-reports")
    if creditPostDir.exists():
        for d in creditPostDir.iterdir():
            if d.is_dir() and stockCode in d.name:
                creditLink = f"\n\n---\n\n> 상세 신용분석: [{corpName} dCR 보고서](/blog/credit-reports/{stockCode})\n"
                break

    # 면책
    disclaimer = (
        "\n\n---\n\n"
        "*이 보고서는 dartlab 엔진이 공시 데이터를 분석하여 자동 생성한 것입니다. "
        "투자 권유가 아니며, 투자 판단의 참고 자료로만 활용하십시오. "
        "모든 수치는 공시 기준이며, 실제 투자 시 추가 검증이 필요합니다.*"
    )

    return fm + header + "\n" + body + creditLink + disclaimer


def _makeTitle(templateName: str, corpName: str) -> str:
    """보고서 제목 생성."""
    _TITLE_MAP = {
        "사이클": "사이클의 파도 위에서",
        "프랜차이즈": "안정의 기계",
        "턴어라운드": "반전의 시작",
        "성장": "성장의 질을 묻다",
        "자본집약": "자산의 무게",
        "지주": "포트폴리오의 합",
        "현금부자": "현금의 선택",
    }
    return _TITLE_MAP.get(templateName, "6막 재무 서사")


def _extractSector(company) -> str:
    """Company에서 업종 정보 추출."""
    try:
        ratios = company.finance.ratios
        sector = getattr(ratios, "sector", None) or ""
        industryGroup = getattr(ratios, "industryGroup", None) or ""
        if sector and industryGroup:
            return f"{sector} > {industryGroup}"
        return sector or industryGroup or ""
    except (AttributeError, ValueError):
        return ""


def _extractCreditGrade(company) -> str:
    """Credit 등급 참조 (실패 시 빈 문자열)."""
    try:
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        if result:
            return result.get("grade", "")
    except (ImportError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return ""


def _resolveSlug(stockCode: str, corpName: str) -> tuple[int, str]:
    """블로그 포스트 순번과 slug 결정."""
    registry = _loadRegistry()

    # 기존 레지스트리에서 찾기
    for entry in registry:
        if entry.get("stockCode") == stockCode:
            return entry["order"], entry["slug"]

    # 새 순번 계산
    existingOrders = [e.get("order", 0) for e in registry]
    nextOrder = max(existingOrders, default=0) + 1

    # 기존 디렉토리에서도 확인
    if _BLOG_DIR.exists():
        for d in _BLOG_DIR.iterdir():
            if d.is_dir() and d.name[0].isdigit():
                try:
                    dirOrder = int(d.name.split("-")[0])
                    if dirOrder >= nextOrder:
                        nextOrder = dirOrder + 1
                    if stockCode in d.name:
                        slug = d.name[len(d.name.split("-")[0]) + 1 :]
                        return dirOrder, slug
                except (ValueError, IndexError):
                    pass

    # slug 생성 (종목코드-영문명)
    slug = f"{stockCode}-{_toSlug(corpName)}"
    return nextOrder, slug


def _toSlug(name: str) -> str:
    """한글 기업명 → URL slug."""
    import re

    _SLUG_MAP = {
        "삼성전자": "samsung-electronics",
        "SK하이닉스": "sk-hynix",
        "LG화학": "lg-chem",
        "네이버": "naver",
        "카카오": "kakao",
        "현대차": "hyundai-motor",
        "기아": "kia",
        "셀트리온": "celltrion",
        "한국전력": "kepco",
        "SK텔레콤": "skt",
        "LG전자": "lg-electronics",
        "KT&G": "ktng",
        "한화": "hanwha",
        "삼양식품": "samyang-foods",
        "코스맥스": "cosmax",
        "대한항공": "korean-air",
        "크래프톤": "krafton",
        "BGF리테일": "bgf-retail",
        "코웨이": "coway",
        "현대건설": "hyundai-ec",
    }
    if name in _SLUG_MAP:
        return _SLUG_MAP[name]
    ascii_name = re.sub(r"[^a-zA-Z0-9]", "-", name.lower()).strip("-")
    return ascii_name or "company"


def _loadRegistry() -> list[dict]:
    """레지스트리 로드."""
    if _REGISTRY_PATH.exists():
        try:
            return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _updateRegistry(
    stockCode: str,
    corpName: str,
    order: int,
    slug: str,
    review,
    grade: str,
) -> None:
    """레지스트리 업데이트."""
    registry = _loadRegistry()
    today = datetime.now().strftime("%Y-%m-%d")
    templateName = getattr(review, "template", None) or ""

    entry = {
        "stockCode": stockCode,
        "corpName": corpName,
        "order": order,
        "slug": slug,
        "template": templateName,
        "grade": grade,
        "publishedAt": today,
    }

    # 기존 항목 업데이트
    updated = False
    for i, e in enumerate(registry):
        if e.get("stockCode") == stockCode:
            registry[i] = entry
            updated = True
            break

    if not updated:
        registry.append(entry)

    registry.sort(key=lambda e: e.get("order", 0))

    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
