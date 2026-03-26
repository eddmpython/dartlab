from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

_log = logging.getLogger(__name__)

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
    (re.compile(r"^\d+-\d+[,.]?사업의개요-시장여건및영업의개황등\(상세\)$"), "businessOverview"),
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
        re.compile(
            r"^(?:해외생산설비현황\(상세\)|(?:(?:\[.+?\]|\(.+?\))\s*)*물류부문영업설비현황\((?:국내|국외|해외)\))$"
        ),
        "rawMaterial",
    ),
    (re.compile(r"^\d+-\d+[,.]?사업의개요-생산설비의현황\(상세\)$"), "rawMaterial"),
    (re.compile(r"^(?:감사보고서|독립된감사인의감사보고서)$"), "audit"),
    (re.compile(r"^외부감사실시내용$"), "audit"),
    (re.compile(r"^\(첨부\)연결재무제표$"), "financialNotes"),
    (re.compile(r"^주석$"), "financialNotes"),
    (re.compile(r"^연결내부회계관리제도감사또는검토의견$"), "internalControl"),
    # --- 054 추가: 전 기간 스캔에서 발견된 패턴 ---
    (re.compile(r"^연구개발(?:활동|현황|진행현황)$"), "majorContractsAndRnd"),
    (re.compile(r"^연구개발실적\[상세\]$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:주요)?연구개발(?:과제및실적|진행현황)\(상세\)$"), "majorContractsAndRnd"),
    (re.compile(r"^사업의내용\(.+업\)$"), "businessOverview"),
    (re.compile(r"^사업의내용과관련된사항(?:\(상세\))?$"), "businessOverview"),
    (re.compile(r"^주요(?:모바일|홈서비스)요금제\(상세\)$"), "productService"),
    (re.compile(r"^주요종속회사.+요금제\(상세\)$"), "productService"),
    (re.compile(r"^Wrap수수료율\(상세\)$"), "productService"),
    (re.compile(r"^투자운용인력현황\(.+\)$"), "productService"),
    (re.compile(r"^.+생산설비의?현황\(상세\)$"), "rawMaterial"),
    (re.compile(r"^수주상황_.+(?:\(상세\))?$"), "salesOrder"),
    (re.compile(r"^모집형태별원수보험료\(상세\)$"), "productService"),
    (re.compile(r"^「주식회사등의외부감사에관한법률」.+$"), "internalControl"),
    (re.compile(r"^(?:반기|분기)?(?:연결)?재무제표(?:검토)?보고서$"), "audit"),
    (re.compile(r"^내부(?:감시장치|회계관리제도).+$"), "internalControl"),
    (re.compile(r"^(?:반기|분기)(?:연결)?재무제표에대한주석$"), "financialNotes"),
    (re.compile(r"^\(첨부\).+재무제표$"), "financialStatements"),
    (re.compile(r"^(?:반기|분기)(?:대차대조표|손익계산서|현금흐름표)$"), "financialStatements"),
    (re.compile(r"^국내(?:,|및)해외계열회사현황\(상세\)$"), "affiliateGroupDetail"),
    (re.compile(r"^.+보고서제출기한연장신고(?:서)?$"), "reportCover"),
    # --- 055 추가: 전체 시장 (2,547종목) 스캔에서 발견된 패턴 ---
    # 바이오/제약 상세
    (re.compile(r"^핵심연구인력(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^라이센스(?:아웃|인)\(License-(?:out|in)\)계약(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^신약등?과제개발진행현황표?(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:주요)?연구개발(?:주요)?(?:진행현황|실적|실적현황)(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^연구개발인력현황(?:\(상세\))?$"), "majorContractsAndRnd"),
    # 특허/지재권 변형
    (re.compile(r"^(?:연결실체의)?(?:주요)?특허(?:권)?(?:보유)?현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^(?:주요)?산업재산권현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^상표권(?:의주요내용|세부내역|보유현황|현황)?(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^지(?:적|식)재(?:산|선)권등록/?출원현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^국내외특허보유현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^특허권등$"), "intellectualProperty"),
    (re.compile(r"^기타참고사항.?지(?:적|식)재(?:산|선)권.+$"), "intellectualProperty"),
    (re.compile(r"^당사의핵심및주변기술(?:\[상세\]|\(상세\))?$"), "intellectualProperty"),
    # 설비/생산
    (re.compile(r"^(?:영업용|기타영업용)?설비(?:변동사항)?현황(?:\(상세\))?$"), "operatingFacilities"),
    (re.compile(r"^(?:국내|해외)?(?:생산)?설비(?:변동사항)?현황(?:\(상세\))?$"), "rawMaterial"),
    (re.compile(r"^생산기지연도별설비현황(?:\(상세\))?$"), "rawMaterial"),
    (re.compile(r"^.+생산설비현황$"), "rawMaterial"),
    (re.compile(r"^해외토지및건물임차현황(?:\(상세\))?$"), "operatingFacilities"),
    (re.compile(r"^지점설치현황-.+(?:\(상세\))?$"), "operatingFacilities"),
    (re.compile(r"^원자재및생산설비(?:\(상세\))?$"), "rawMaterial"),
    # 금융 상세
    (re.compile(r"^투자금융현황\(.+\)$"), "productService"),
    (re.compile(r"^금융투자상품(?:의투자중개및수수료현황|위탁매매현황)(?:\(상세\))?$"), "productService"),
    (re.compile(r"^투자(?:매매|중개)업무-.+$"), "productService"),
    (re.compile(r"^주요제품\(.+\)$"), "productService"),
    (re.compile(r"^공사및용역서비스(?:\(상세\))?$"), "productService"),
    (re.compile(r"^아티스트전속계약현황(?:\(상세\))?$"), "productService"),
    (re.compile(r"^산업현황및보유기술(?:\(상세\))?$"), "businessOverview"),
    (re.compile(r"^시장현황및경쟁현황(?:\(상세\))?$"), "businessOverview"),
    # 매출/수주
    (re.compile(r"^사업부문별매출현황(?:\(상세\))?$"), "salesOrder"),
    (re.compile(r"^수주상황-.+(?:\(상세\))?$"), "salesOrder"),
    # 기타/참조
    (re.compile(r"^기술도입계약(?:및상표계약)?(?:\(.+\)|\[.+\])?$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:관련)?용어(?:정리|설명)$"), "otherReference"),
    (re.compile(r"^사업관련용어Appendix$"), "otherReference"),
    (re.compile(r"^그밖에투자의사결정에필요한사항(?:\(상세\))?$"), "otherInvestmentDecisionMatters"),
    (re.compile(r"^환경및안전관련허가/?신고사항(?:\(상세\))?$"), "environmentRegulation"),
    (re.compile(r"^\d+-\d+\.?사업의내용과관련된사항$"), "businessOverview"),
    # 지재권 넓은 캐치: 특허, 상표, 디자인, 실용신안 변형
    (
        re.compile(r"^(?:.*)?특허권?(?:등록현황|보유(?:세부)?현황|세부내역|등)(?:_.+)?(?:\(상세\)|\[상세\])?$"),
        "intellectualProperty",
    ),
    (re.compile(r"^(?:.*)?상표(?:권|등록)(?:현황|세부내역|의주요내용)(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^(?:.*)?디자인(?:개발)?등록현황(?:\(상세\))?$"), "intellectualProperty"),
    (
        re.compile(r"^지(?:적|식)재(?:산|선)권(?:보유(?:현황|내역)|소유내역|세부목록|등|상세)(?:\[상세\]|\(상세\))?$"),
        "intellectualProperty",
    ),
    (re.compile(r"^(?:보유기술)?특허현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^사업과관련된.+지(?:적|식)재(?:산|선)권.+$"), "intellectualProperty"),
    (re.compile(r"^특허.+지(?:적|식)재(?:산|선)권현황\(.+\)$"), "intellectualProperty"),
    # 연구/계약 변형
    (re.compile(r"^주요(?:연구개발)?(?:성과|실적)(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^연구개발인력구성및현황(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^주요기술협력계약$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:기타)?주요계약(?:상세)?현황(?:\(.+\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^경영상의주요계약현황(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^.+연구개발(?:주요)?(?:진행현황|활동)(?:\(상세\))?$"), "majorContractsAndRnd"),
    # 금융 상세
    (re.compile(r"^투자일임업무-.+$"), "productService"),
    (re.compile(r"^신탁업-.+$"), "financialNotes"),
    (re.compile(r"^(?:손익계산서|재무제표)\(신탁계정.+\)$"), "financialNotes"),
    (re.compile(r"^주요(?:유/?무선)?요금제(?:\(상세\))?$"), "productService"),
    (re.compile(r"^매출실적현황(?:\(상세\))?$"), "salesOrder"),
    # 설비 추가
    (re.compile(r"^영업장현황(?:\(상세\))?$"), "operatingFacilities"),
    (re.compile(r"^기타영업용설비(?:\(상세\))?$"), "operatingFacilities"),
    (re.compile(r"^생산설비\(.+\)에관한사항(?:\(상세\))?$"), "rawMaterial"),
    # 기타
    (re.compile(r"^(?:주요)?용어(?:정리|설명표?)$"), "otherReference"),
    (re.compile(r"^사업의개요-용어의정의(?:\(상세\))?$"), "otherReference"),
    (re.compile(r"^외화표시화폐성자산및화폐성부채.+(?:\(상세\))?$"), "liquidityRisk"),
    (re.compile(r"^각종인증현황$"), "intellectualProperty"),
    (re.compile(r"^주요제품에관한설명$"), "productService"),
    (re.compile(r"^상표및프로그램등록현황(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^주요국내판매계약(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^주요연구개발활동(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^재무제표에대한주석$"), "financialNotes"),
    (re.compile(r"^연결대상종속회사현황\(해당사항없음\)$"), "subsidiaryDetail"),
    (re.compile(r"^계열회사현황\(해당사항없음\)$"), "affiliateGroupDetail"),
    (re.compile(r"^장내파생상품거래현황및손익(?:\(상세\))?$"), "riskDerivative"),
    (re.compile(r"^지역냉난방사업자별.+$"), "productService"),
    # --- 055 4차: 넓은 캐치 패턴 (1사 회사특화 상세표 커버) ---
    # 지재권 최종 캐치: 특허/상표/디자인/저작권/실용신안 키워드 포함
    (
        re.compile(
            r"^(?:.*)?(?:특허|상표|디자인|저작권|실용신안)(?:권)?(?:.*)?(?:현황|내역|목록|리스트|보유|등록|출원|명칭)(?:.*)?$"
        ),
        "intellectualProperty",
    ),
    (re.compile(r"^지(?:적|식)재(?:산|선)권(?:.*)?$"), "intellectualProperty"),
    (re.compile(r"^상세표-\d+\.?지(?:적|식)재(?:산|선)권$"), "intellectualProperty"),
    (re.compile(r"^(?:.*)?보유특허현황$"), "intellectualProperty"),
    (re.compile(r"^산업재산권보유현황(?:\(상세\))?$"), "intellectualProperty"),
    # 연구개발 최종 캐치
    (re.compile(r"^(?:.*)?연구개발(?:과제)?(?:완료|활동)?(?:실적|현황|상세)(?:.*)?$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:.*)?연구(?:및)?개발(?:관련)?(?:.*)?지(?:적|식)재(?:산|선)권(?:.*)?$"), "intellectualProperty"),
    # 생산설비 최종 캐치
    (re.compile(r"^(?:.*)?생산(?:설비|능력)(?:.*)?(?:\(상세\))?$"), "rawMaterial"),
    # 금융 최종 캐치
    (re.compile(r"^(?:준법감시인|내부통제)(?:.*)?$"), "internalControl"),
    (re.compile(r"^주요펀드상품$"), "productService"),
    (re.compile(r"^주요판매계약$"), "majorContractsAndRnd"),
    # 기타 캐치
    (re.compile(r"^(?:주요)?용어해설$"), "otherReference"),
    (re.compile(r"^상세표-\d+\.?용어설명표$"), "otherReference"),
    (re.compile(r"^매출(?:실적)?현황(?:\(상세\))?$"), "salesOrder"),
    (re.compile(r"^중소기업기준검토표등$"), "smeStatus"),
    (re.compile(r"^라이센스(?:아웃|인)\(Licese?-(?:out|in)\)계약(?:\(상세\))?$"), "majorContractsAndRnd"),
    # 해당사항없음/기재생략 suffix 캐치
    (re.compile(r"^연결대상종속회사현황(?:\(상세\))?.?해당사항없음$"), "subsidiaryDetail"),
    (re.compile(r"^타법인출자현황(?:\(상세\))?.?기재생략$"), "otherReference"),
    # 회사명- prefix 캐치 (회사명-topic 패턴)
    (re.compile(r"^.+(?:주요제품등의현황|주요제품의현황)(?:\(상세\))?$"), "productService"),
    # --- 055 5차: 잔여 10+ 빈도 캐치 ---
    (re.compile(r"^특허권$"), "intellectualProperty"),
    (re.compile(r"^특허권(?:에대한사항)?(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^(?:주요)?연구실적(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^.+-주요지(?:적|식)재(?:산|선)권보유\(.+\)$"), "intellectualProperty"),
    (re.compile(r"^주요지(?:적|식)재(?:산|선)권보유(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^연구개발담당보직(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^연구개발활동등$"), "majorContractsAndRnd"),
    (re.compile(r"^당(?:분기|반기|기)중취득한주요특허권$"), "intellectualProperty"),
    (re.compile(r"^.+수주상황.+(?:\(상세\))?$"), "salesOrder"),
    (re.compile(r"^판매계약(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^투자중개업무(?:\(상세\))?$"), "productService"),
    (re.compile(r"^정부과제수행실적(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^사업부문별매출실적현황(?:\[상세\]|\(상세\))?$"), "salesOrder"),
    (re.compile(r"^공동연구계약(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^게임별아이템판매가격(?:\[상세\]|\(상세\))?$"), "productService"),
    (re.compile(r"^계열회사현황(?:\(상세\))?.?해당사항없음$"), "affiliateGroupDetail"),
    (re.compile(r"^파생상품(?:계약)?현황(?:\(상세\))?$"), "riskDerivative"),
    (re.compile(r"^.+지점설치현황-.+(?:\(상세\))?$"), "operatingFacilities"),
    (re.compile(r"^.+매출실적(?:\(상세\))?$"), "salesOrder"),
    (re.compile(r"^주요논문실적(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^.+주요사업장현황(?:\(상세\))?$"), "operatingFacilities"),
    (re.compile(r"^(?:주요)?용어정의$"), "otherReference"),
    (re.compile(r"^주요제품에대한설명$"), "productService"),
    (re.compile(r"^재무상태표\(신탁계정.+\)$"), "financialNotes"),
    (re.compile(r"^경영상의주요계약-.+(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^사업의(?:개요|내용)(?:\[상세\]|\(상세\))?$"), "businessOverview"),
    (re.compile(r"^사업의(?:개요|내용)(?:과관련된사항)?\(.+\)$"), "businessOverview"),
    (re.compile(r"^사업의개요-용의의정의(?:\(상세\))?$"), "otherReference"),
    (re.compile(r"^.+부문\[상세\]$"), "businessOverview"),
    (re.compile(r"^상세표-지(?:적|식)재(?:산|선)권$"), "intellectualProperty"),
    (re.compile(r"^주요국가별허가등록현황(?:\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^.+보유특허(?:\(상세\))?$"), "intellectualProperty"),
    (re.compile(r"^.+파생상품계약(?:\(상세\))?$"), "riskDerivative"),
    (re.compile(r"^(?:글로벌)?신약개발부문(?:\[상세\]|\(상세\))?$"), "majorContractsAndRnd"),
    (re.compile(r"^(?:.+)?종속회사(?:.+)?(?:\(상세\))?$"), "subsidiaryDetail"),
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


_DETAIL_SUFFIX_RE = re.compile(r"\(상세\)$")
_COMPANY_SUFFIX_RE = re.compile(r"_.+$")


def mapSectionTitle(title: str) -> str:
    normalized = normalizeSectionTitle(title)
    mapped = loadSectionMappings().get(normalized)
    if mapped:
        return mapped
    for pattern, topic in _PATTERN_MAPPINGS:
        if pattern.match(normalized):
            return topic
    # fallback: (상세) suffix 제거 후 재시도
    if "(상세)" in normalized:
        stripped = _DETAIL_SUFFIX_RE.sub("", normalized).strip()
        m = loadSectionMappings().get(stripped)
        if m:
            return m
        for pattern, topic in _PATTERN_MAPPINGS:
            if pattern.match(stripped):
                return topic
    # fallback: _회사명 suffix 제거 후 재시도 (예: 수주상황(상세)_주요자회사...)
    if "_" in normalized:
        stripped = _COMPANY_SUFFIX_RE.sub("", normalized).strip()
        m = loadSectionMappings().get(stripped)
        if m:
            return m
        if "(상세)" in stripped:
            stripped2 = _DETAIL_SUFFIX_RE.sub("", stripped).strip()
            m2 = loadSectionMappings().get(stripped2)
            if m2:
                return m2
    return normalized


def measureMappingRate(titles: list[str]) -> dict:
    """section title 리스트의 매핑률을 측정.

    Returns:
        {"total": N, "mapped": M, "rate": float, "unmapped_top": [...]}
    """
    total = len(titles)
    unmapped: dict[str, int] = {}
    mapped = 0

    for title in titles:
        normalized = normalizeSectionTitle(title)
        result = mapSectionTitle(title)
        if result != normalized:
            mapped += 1
        else:
            unmapped[normalized] = unmapped.get(normalized, 0) + 1

    rate = (mapped / total * 100) if total > 0 else 100.0
    top_unmapped = sorted(unmapped.items(), key=lambda x: -x[1])[:10]

    _log.info(
        "section 매핑률: %d/%d (%.1f%%), 미매핑 고유 %d개",
        mapped,
        total,
        rate,
        len(unmapped),
    )
    for title, cnt in top_unmapped[:5]:
        _log.info("  미매핑 상위: '%s' (%d회)", title, cnt)

    return {
        "total": total,
        "mapped": mapped,
        "rate": rate,
        "unmapped_top": [{"title": t, "count": c} for t, c in top_unmapped],
    }
