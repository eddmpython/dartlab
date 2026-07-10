"""Core messaging template catalog.

`dartlab.core.messaging` owns runtime formatting and emission. This module owns
static user-facing templates so adding copy does not grow the handler module.
"""

from __future__ import annotations

SIMPLE: dict[str, str] = {
    "download:start": "{stockCode} ({label}) \u2192 첫 사용: 자동 다운로드 중...",
    "download:done": "\u2713 {label} 다운로드 완료 ({sizeStr})",
    "download:done_short": "\u2713 다운로드 완료 ({sizeStr})",
    "download:exists": "\u2713 {stockCode} ({label}) 이미 존재",
    "download:progress": "{stockCode} ({label}) 다운로드 중...",
    "download:failed_single": "\u2717 {stockCode} ({label}) 다운로드 실패: {error}",
    "download:failed_item": "\u2717 {name} 실패: {error}",
    "download:refreshed": "\u2713 {stockCode} 데이터 갱신 완료",
    "collect:start": "{stockCode} ({label}) \u2192 로컬에 없음. DART API로 수집 중... ({keyCount}키 {mode})",
    "collect:done": "\u2713 {label} 수집 완료 ({sizeStr})",
    "collect:skip": "\u2713 {stockCode} ({label}) 이미 수집됨",
    "collect:no_key": "DART API 키가 있으면 자동 수집 가능합니다: dartlab setup dart-key",
    "collect:batch_start": "{stockCode} \u2192 로컬에 없음. {categories} {keyCount}키 병렬 수집 시작...",
    "collect:batch_done": "\u2713 {stockCode} 수집 완료 ({summary})",
    "collect:exhausted": "\u26a0 DART API 일일 한도 도달. 내일 다시 시도하거나 추가 키를 등록하세요.",
    "edgar:fallback": "사전 수집 데이터에 없음 \u2192 SEC EDGAR API에서 직접 수집 중... (최초 1회, 수 분 소요)",
    "edgar:sec_download": "{cik} (SEC EDGAR 재무 데이터) 로컬에 없음 \u2192 SEC API에서 다운로드 중...",
    "edgar:bulk_download_start": "[dartlab] SEC EDGAR 재무 데이터 전체 다운로드 중 (~1.37GB, 최초 1회 5~15분). companyfacts.zip",
    "edgar:bulk_download_done": "\u2713 companyfacts.zip 다운로드 완료 ({sizeMB:.0f}MB, {elapsedSec:.0f}s)",
    "edgar:bulk_convert_start": "[dartlab] companyfacts.zip \u2192 종목별 parquet 변환 중 (수 분 소요). {totalCiks}개 기업",
    "edgar:bulk_convert_done": "\u2713 EDGAR 재무 parquet 변환 완료 (converted={converted} / skipped={skipped} / failed={failed}, {elapsedSec:.0f}s)",
    "edgar:bulk_fresh": "\u2713 companyfacts.zip 최신 (TTL {ttlHours}h)",
    "edgar:bulk_quarterly_start": "[dartlab] SEC 분기 메타 벌크 다운로드 중 ({year}Q{quarter}, {sizeMB:.0f}MB)",
    "edgar:bulk_quarterly_done": "\u2713 {year}Q{quarter} sub/pre/tag parquet 생성 완료",
    "edgar:empty": "{cik} SEC API 응답이 비어있음 (데이터 없음)",
    "edgar:save_done": "저장 완료: {path}",
    "edgar:download_failed": "{cik} SEC API 다운로드 실패: {error}",
    "edgar:filing_limit": "{ticker} filing 수가 많아 최근 {maxFilings}건만 수집",
    "edgar:docs_start": "{ticker} EDGAR docs 원문 수집 시작 ({count} filings, since {sinceYear})",
    "edgar:docs_skip": "{ticker} filing {count}건 skip",
    "edgar:docs_save": "저장 완료: {path}",
    "edgar:batch_start": "EDGAR docs 배치 수집 시작 ({total} tickers, since {sinceYear})",
    "edgar:batch_progress": "{idx}건 처리 완료 \u2192 {cooldown:.1f}초 휴지",
    "edgar:batch_done": "\u2713 EDGAR 배치 수집 완료 (성공 {success} / 실패 {failed} / 총 {total})",
    "edgar:incremental_start": "{ticker} EDGAR docs 증분 업데이트 ({newCount}건 신규 filing)",
    "edgar:incremental_done": "\u2713 {ticker} EDGAR docs 증분 완료 ({newRows}행 추가)",
    "edgar:no_new": "\u2713 {ticker} EDGAR docs 최신 상태",
    "freshness:checking": "{stockCode} 최신 공시 확인 중...",
    "freshness:fresh": "\u2713 {stockCode} 최신 상태",
    "freshness:stale": "\u26a0 {stockCode} 새 공시 {count}건 발견 ({latestReport})",
    "freshness:noKey": "DART API 키 없음 \u2192 사전 수집 데이터 기준으로만 확인",
    "freshness:scanDone": "\u2713 {total}종목 스캔: {staleCount}종목에 새 공시",
    "listing:download": "KRX KIND 상장법인 목록 다운로드 중...",
    "listing:done": "{count}개 종목 로드 완료",
    "listing:krx:download": "KRX 상장법인 목록 다운로드 중...",
    "listing:krx:done": "{count}개 종목 로드 완료",
    "listing:dartlist:download": "DART 전체 법인 목록 다운로드 중 (HuggingFace)...",
    "listing:dartlist:done": "{count}개 법인 로드 완료",
    "scan:signal_start": "서술형 시그널 스캔: {count}사",
    "scan:network_health": "그룹 건전성 분석 중...",
    "scan:prebuild_check": "scan 프리빌드 데이터 확인 중... ({dir})",
    "scan:prebuild_missing": "scan 프리빌드 데이터 없음. 배치 prebuild 또는 collect 데이터가 필요합니다",
    # 브라우저(pyodide)는 첫 호출 때 finance-lite 를 내려받는다. 정상 경로라 "없음" 이 아니라 "받는 중" 이다.
    "scan:prebuild_download_lite": "전상장사 데이터를 처음 한 번 내려받습니다. 잠시 걸립니다.",
    "scan:prebuild_ready_lite": "✓ 전상장사 데이터 준비 완료 ({sizeStr})",
    "scan:prebuild_ready": "\u2713 scan 프리빌드 준비 완료 ({fileCount}개 파일)",
    "scan:prebuild_failed": "\u26a0 scan 프리빌드 다운로드 실패: {error}. 종목별 fallback 사용 (느림)",
    "scan:prebuild_incomplete": (
        "⚠ scan 프리빌드 불완전. 누락 파일: {missing}. 배치 prebuild 산출물 또는 collect 데이터가 필요합니다."
    ),
    "scan:fallback_insufficient": (
        "⚠ scan/finance.parquet 프리빌드가 없어 종목별 파일 {count}개만으로 fallback. "
        "전종목(~2700)이 아닌 부분 결과입니다. 배치 prebuild 산출물이 필요합니다."
    ),
    "edgar:bulk_start": "EDGAR {kind} 배치 수집 시작. {total}종목 (시간이 걸릴 수 있습니다)",
    "edgar:bulk_done": "\u2713 EDGAR {kind} 배치 완료 (성공 {success} / 실패 {failed} / {elapsedSec:.0f}초)",
    "edgar:bulk_partial": "\u26a0 EDGAR {kind} 배치 부분 완료 ({done}/{total}, 오류 {errors})",
    "edgar:bulk_empty": "EDGAR 배치: 수집할 ticker가 없습니다",
    "edgar:bulk_target": "EDGAR 배치 대상: {count}종목 ({tier}, mode={mode})",
    "stemindex:hf_start": "검색 인덱스 다운로드 중... HuggingFace ({repo})",
    "stemindex:hf_done": "\u2713 검색 인덱스 준비 완료 ({sizeStr})",
    "stemindex:hf_fail": "\u26a0 검색 인덱스 다운로드 실패: {error}",
    "stemindex:local": "\u2713 검색 인덱스 로컬 사용 ({path})",
    "data:stale_warning": "\u26a0 로컬 데이터가 {ageDays}일째 갱신되지 않았습니다. 네트워크 또는 HuggingFace 접근을 확인하세요.",
    "hint:market_data_needed": (
        "\u26a0 {category} 데이터가 로컬에 없습니다. {fn}은 전체 시장 데이터가 필요합니다.\n"
        "  dartlab.collect() 또는 배치 prebuild 데이터를 준비하세요."
    ),
    "edgar:universe_update": "SEC listed universe 갱신 중...",
    "edgar:universe_save": "저장 완료: {path}",
    "edgar:sections_save": "EDGAR {ticker} sections 저장: {periodsWritten}개 기간 / {totalRows}행",
    "edgar:collect_exhausted": "EDGAR 수집 키 소진. 일부 미수집 (재시도 권장)",
    "edgar:docs_skip_deprecated": "EDGAR {ticker} docs.parquet emit 생략 ({reason})",
    "hint:no_finance": "{stockCode} finance 데이터 없음 \u2192 {prop} 사용 불가. dartlab.collect('{stockCode}') 또는 Company 자동 다운로드 경로를 확인하세요.",
    "hint:no_report": "{stockCode} report 데이터 없음 \u2192 {prop} 사용 불가. dartlab.collect('{stockCode}') 또는 Company 자동 다운로드 경로를 확인하세요.",
    "hint:no_ai": "AI provider 미설정 \u2192 {fn} 사용 불가. dartlab.setup()으로 설정하세요.",
}


class StructuredMsg:
    """Structured message definition with key-aware action variants."""

    __slots__ = ("template", "actions", "actionsWithKey", "actionsWithoutKey")

    def __init__(
        self,
        template: str,
        actions: list[str] | None = None,
        actionsWithKey: list[str] | None = None,
        actionsWithoutKey: list[str] | None = None,
    ):
        self.template = template
        self.actions = actions or []
        self.actionsWithKey = actionsWithKey or []
        self.actionsWithoutKey = actionsWithoutKey or []


STRUCTURED: dict[str, StructuredMsg] = {
    "hint:missing_docs": StructuredMsg(
        template="{stockCode} ({label}) \u2192 사전 수집 데이터에 없습니다.",
        actionsWithKey=[
            "DART API 키가 설정되어 있으므로 직접 수집이 가능합니다:\n    dartlab collect {stockCode}",
        ],
        actionsWithoutKey=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n    dartlab setup dart-key\n    dartlab collect {stockCode}",
        ],
    ),
    "hint:missing_other": StructuredMsg(
        template="{stockCode} ({label}) \u2192 사전 수집 데이터에 없습니다.",
        actions=["해당 종목이 dartlab 데이터셋에 포함되어 있는지 확인하세요."],
        actionsWithKey=[
            "DART API 키가 설정되어 있으므로 직접 수집이 가능합니다:\n    dartlab collect {stockCode}\n    dartlab collect --batch {stockCode}  (전 카테고리 병렬)",
        ],
        actionsWithoutKey=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n    dartlab setup dart-key",
        ],
    ),
    "hint:newFilingsAvailable": StructuredMsg(
        template="{stockCode}. 새 공시 {count}건 발견 ({latestReport})",
        actionsWithKey=[
            "증분 수집: dartlab collect --incremental {stockCode}",
            "또는 Python: c.update()",
        ],
        actionsWithoutKey=[
            "DART API 키를 설정하면 자동 수집 가능:\n    dartlab setup dart-key",
        ],
    ),
    "hint:stale": StructuredMsg(
        template="{stockCode} docs 데이터가 {ageStr} 전 기준입니다.",
        actionsWithKey=["최신 공시 반영: dartlab collect {stockCode}"],
        actionsWithoutKey=[
            "갱신하려면 DART API 키 설정이 필요합니다:\n    dartlab setup dart-key",
        ],
    ),
    "error:download_failed": StructuredMsg(
        template="데이터 다운로드 실패 ({stockCode}, {label}): {error}",
        actions=[
            "인터넷 연결을 확인하세요",
            "해당 종목이 dartlab 데이터셋에 포함되어 있는지 확인하세요\n  \u2192 DART: 한국 상장기업 ~2,700개 / EDGAR: 미국 상장기업 ~970개",
        ],
        actionsWithKey=[
            "DART 공시 문서는 직접 수집 가능합니다:\n  dartlab collect {stockCode}",
        ],
        actionsWithoutKey=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n  dartlab setup dart-key\n  dartlab collect {stockCode}",
        ],
    ),
    "error:no_data": StructuredMsg(
        template="'{stockCode}' 데이터를 찾을 수 없습니다.",
        actions=[
            "종목코드가 올바른지 확인하세요 (6자리, 예: '005930')",
            "비상장 또는 dartlab 데이터셋에 미포함 종목일 수 있습니다",
            "인터넷 연결을 확인하세요 (첫 사용 시 자동 다운로드 필요)",
        ],
        actionsWithKey=[
            "DART API 키가 설정되어 있으므로 직접 수집이 가능합니다:\n  dartlab collect {stockCode}",
            "종목 검색: dartlab.searchName('삼성') 또는 dartlab.listing()",
        ],
        actionsWithoutKey=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n  dartlab setup dart-key\n  dartlab collect {stockCode}",
            "종목 검색: dartlab.searchName('삼성') 또는 dartlab.listing()",
        ],
    ),
}


KEY_REQUIREMENTS: dict[str, dict[str, str]] = {
    "dart": {
        "envKey": "DART_API_KEY",
        "label": "DART OpenAPI",
        "signupUrl": "https://opendart.fss.or.kr",
        "guide": "전자공시 API 키 (한국 상장기업 공시 직접 수집에 필요)",
        "setupCmd": 'dartlab.setup("dart-key")',
    },
    "fred": {
        "envKey": "FRED_API_KEY",
        "label": "FRED (미국 연방준비제도)",
        "signupUrl": "https://fred.stlouisfed.org/docs/api/api_key.html",
        "guide": "미국 거시경제 데이터 (금리, 실업률, GDP 등) 수집에 필요",
        "setupCmd": "FRED_API_KEY=... (.env에 직접 입력)",
    },
    "ecos": {
        "envKey": "ECOS_API_KEY",
        "label": "ECOS (한국은행 경제통계)",
        "signupUrl": "https://ecos.bok.or.kr/api/",
        "guide": "한국 거시경제 데이터 (기준금리, 환율, 물가 등) 수집에 필요",
        "setupCmd": "ECOS_API_KEY=... (.env에 직접 입력)",
    },
}


CLOUDFLARED_ERROR_HINTS: list[tuple[str, str]] = [
    ("1033", "DNS 전파 대기 중. 1~2분 후 다시 시도하세요."),
    ("1034", "Argo 터널이 활성화되지 않았습니다. cloudflared service start 또는 다시 실행해보세요."),
    (
        "530",
        "DNS route가 이 tunnel을 가리키지 않습니다. cloudflared tunnel route dns <id> <hostname>를 다시 실행하세요.",
    ),
    ("502", "로컬 서버가 응답하지 않습니다. dartlab 서버가 켜져 있는지 확인하세요."),
    ("certificate", "cert.pem이 없거나 만료되었습니다. cloudflared tunnel login으로 재인증하세요."),
    ("permission", "credentials 파일 권한 문제. ~/.cloudflared/*.json 의 권한을 확인하세요."),
]


__all__ = [
    "CLOUDFLARED_ERROR_HINTS",
    "KEY_REQUIREMENTS",
    "SIMPLE",
    "STRUCTURED",
    "StructuredMsg",
]
