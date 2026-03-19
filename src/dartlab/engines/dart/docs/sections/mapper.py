from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")
_MULTISPACE_RE = re.compile(r"\s+")
_LEAF_PREFIX_RE = re.compile(r"^\s*(?:(?:\d+|[가-힣])[.)]\s*|\(\d+\)\s*|[①-⑳]\s*)+")
_TRAILING_PUNCT_RE = re.compile(r"[-–—:：;,]+$")
_ROMAN_PREFIX_RE = re.compile(r"^(?:X{0,3}(?:IX|IV|V?I{0,3}))[.\s]+")
_PATTERN_MAPPINGS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^지적재산권보유현황\(.+\)$"), "intellectualProperty"),
    (re.compile(r"^연구개발실적\(.+\)$"), "majorContractsAndRnd"),
    (re.compile(r"^주요지적재산권현황\(상세\)$"), "intellectualProperty"),
    (re.compile(r"^(?:.+)?(?:주요)?연구개발실적(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^연구개발(?:실적|진행현황)-.+$"), "majorContractsAndRnd"),
    (re.compile(r"^핵심연구인력현황-.+$"), "majorContractsAndRnd"),
    (re.compile(r"^연구개발담당조직\(상세\)$"), "majorContractsAndRnd"),
    (re.compile(r"^연구개발실적\(상세\)-.+$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:연구개발현황|연구개발활동)\(상세\)$"), "majorContractsAndRnd"),
    (re.compile(r"^수주(?:상황|현황)\(상세\)$"), "salesOrder"),
    (re.compile(r"^수주현황$"), "salesOrder"),
    (re.compile(r"^.+수주(?:상황|현황)(?:\(상세\))?$"), "salesOrder"),
    (re.compile(r"^사업의내용-.+수주(?:상황|현황).+$"), "salesOrder"),
    (re.compile(r"^\d+-\d+[,.]?사업의개요-판매조건및경로,판매전략,주요매출처\(상세\)$"), "salesOrder"),
    (re.compile(r"^.*경영상의주요계약(?:\(상세\)|\[상세\])?$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:주요계약및연구개발활동|주요연구개발과제및실적)\(상세\)$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:.+)?(?:주요)?지(?:적|식)재(?:산|선)권(?:등)?보유현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^(?:.+)?(?:주요)?지(?:적|식)재(?:산|선)권(?:등)?보유현황-.+$"), "intellectualProperty"),
    (re.compile(r"^(?:.+)?지(?:적|식)재(?:산|선)권현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^지(?:적|식)재(?:산|선)권현황-.+$"), "intellectualProperty"),
    (re.compile(r"^주요특허현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^사업의내용-.+특허(?:보유현황|현황)$"), "intellectualProperty"),
    (
        re.compile(r"^(?:특허권보유현황\(상세\)|특허등지적재산권등록현황|지적재산권세부목록\(상세\))$"),
        "intellectualProperty",
    ),
    (
        re.compile(r"^(?:주요지적재산권내용|지적재산권\(상세\)|\d+-\d+[,.]?사업의개요-지적재산권\(상세\))$"),
        "intellectualProperty",
    ),
    (re.compile(r"^경영상의주요계약(?:\(|\[)상세(?:\)|\])$"), "majorContractsAndRnd"),
    (re.compile(r"^투자매매업무-장내파생상품거래현황\(상세\)$"), "riskDerivative"),
    (re.compile(r"^\(.+\)신용파생상품상세명세(?:\(상세\))?$"), "riskDerivative"),
    (re.compile(r"^(?:신용파생상품거래현황|장내파생상품거래현황)\(상세\)$"), "riskDerivative"),
    (re.compile(r"^(?:신용파생상품(?:상세)?명세|통화선도계약현황\(상세\))$"), "riskDerivative"),
    (re.compile(r"^이자율스왑의계약내용\(상세\)$"), "riskDerivative"),
    (re.compile(r"^\d+-\d+[,.]?사업의개요-위험관리(?:및파생거래)?\(상세\)$"), "riskDerivative"),
    (
        re.compile(r"^(?:투자매매업무-증권거래현황|투자중개업무-금융투자상품의위탁매매및수수료현황)\(상세\)$"),
        "productService",
    ),
    (re.compile(r"^증권거래현황\(상세\)$"), "productService"),
    (re.compile(r"^주유소현황-.+$"), "productService"),
    (re.compile(r"^주요모바일요금제-.+$"), "productService"),
    (re.compile(r"^일임형Wrap(?:상품)?\(상세\)$"), "productService"),
    (re.compile(r"^투자(?:일임)?운용인력현황(?:\(상세\)|\(요약\))$"), "productService"),
    (re.compile(r"^(?:예금상품별개요|신탁상품별개요|외환상품및서비스(?:개요)?)$"), "productService"),
    (re.compile(r"^주요상품,?서비스\(\d+\).+\(상세\)$"), "productService"),
    (re.compile(r"^\d+-\d*\.?주요상품및서비스(?:\(상세\))?-.+(?:\(상세\))?$"), "productService"),
    (re.compile(r"^주요상품및서비스\(상세\)$"), "productService"),
    (
        re.compile(
            r"^(?:\(.+\)(?:예금업무|대출업무|e-금융서비스|방카슈랑스|신용카드상품|대출상품|예금상품|외환/수출입서비스|기타업무-외환/수출입서비스|기타업무-e-금융서비스|상품및서비스개요|신탁업무)|투자일임업무-투자운용인력현황|투자운용인력현황)\(상세\)$"
        ),
        "productService",
    ),
    (re.compile(r"^(?:신탁업무-재무제표|신탁업무재무제표)\(상세\)$"), "financialNotes"),
    (re.compile(r"^기업집단에소속된회사\(상세\)$"), "affiliateGroupDetail"),
    (re.compile(r"^생산설비의현황\(상세\)$"), "rawMaterial"),
    (
        re.compile(r"^(?:해외생산설비현황\(상세\)|(?:(?:\[.+?\]|\(.+?\))\s*)*물류부문영업설비현황\((?:국내|국외|해외)\))$"),
        "rawMaterial",
    ),
    (re.compile(r"^\d+-\d+[,.]?사업의개요-생산설비의현황\(상세\)$"), "rawMaterial"),
    (re.compile(r"^(?:감사보고서|독립된감사인의감사보고서)$"), "audit"),
    (re.compile(r"^외부감사실시내용$"), "audit"),
    (re.compile(r"^\(첨부\)연결재무제표$"), "financialNotes"),
    (re.compile(r"^주석$"), "financialNotes"),
    (re.compile(r"^연결내부회계관리제도감사또는검토의견$"), "internalControl"),
)


def _mappingPath() -> Path:
    return Path(__file__).resolve().parent / "mapperData" / "sectionMappings.json"


def stripSectionPrefix(title: str) -> str:
    return _LEAF_PREFIX_RE.sub("", title.strip())


def normalizeSectionTitle(title: str) -> str:
    text = stripSectionPrefix(title)
    text = _INDUSTRY_PREFIX_RE.sub("", text)
    text = stripSectionPrefix(text)
    text = _ROMAN_PREFIX_RE.sub("", text)
    text = text.replace("ㆍ", ",")
    text = text.replace("·", ",")
    text = _MULTISPACE_RE.sub("", text)
    text = _TRAILING_PUNCT_RE.sub("", text)
    return text.strip()


@lru_cache(maxsize=1)
def loadSectionMappings() -> dict[str, str]:
    path = _mappingPath()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    expanded: dict[str, str] = {}
    for key, value in raw.items():
        expanded[normalizeSectionTitle(key)] = value
    return expanded


def mapSectionTitle(title: str) -> str:
    normalized = normalizeSectionTitle(title)
    mapped = loadSectionMappings().get(normalized)
    if mapped:
        return mapped
    for pattern, topic in _PATTERN_MAPPINGS:
        if pattern.match(normalized):
            return topic
    return normalized
