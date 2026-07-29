"""데이터 공급자 자격증명 SSOT — env·토큰 해석 + 안내 단일 진입점 (core 강등).

gather 의 데이터 소스(공공데이터포털·FRED·ECOS·DART·KRX·HF…)가 제각각
``os.environ.get("XXX_API_KEY")`` 를 직접 읽고 에러 문구도 하드코딩하던 것을
하나의 *공급자 레지스트리* 로 모은다. core 에 두는 이유는 gather(L1) 뿐 아니라
core/dataLoader·pipeline 도 HF_TOKEN 등을 읽기 때문 — cross-cutting primitive.

설계 단위 = **공급자(provider)** 지 개별 API 가 아니다. 공공데이터포털은 단일
계정 키 하나(`DATA_GO_KR_KEY`)로 주가시세·관세청 무역통계·국민연금 가입사업장을
모두 호출한다 → 1 spec, 3 sources.

해석 우선순위 (``getKey``): 명시 인자 → 환경변수 → SecretStore(암호화 저장) → None.
``resolveKey`` 는 None 대신 레지스트리 기반 안내 메시지로 `CredentialError` 발생.

AI provider 키(GEMINI·ANTHROPIC…)는 별도 SSOT(`core/providers/registry.py` +
`dartlab setup`)가 관리한다 — 본 모듈은 *데이터 수집* 공급자만 다룬다.

See Also:
    core/providers/secrets.py (SecretStore 저장 백엔드) ·
    core/credentialLifecycle.py (만료 추적) ·
    gather/credentials.py (gather 측 facade 진입점).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


class CredentialError(RuntimeError):
    """데이터 공급자 자격증명 누락 또는 미등록 공급자."""


class CredentialWriteError(CredentialError):
    """자격증명 쓰기 실패 — ``committed``로 저장 완료 여부를 구분."""

    def __init__(self, message: str, *, committed: bool) -> None:
        super().__init__(message)
        self.committed = committed


@dataclass(frozen=True)
class DataProviderSpec:
    """단일 데이터 공급자의 자격증명 메타 — 레지스트리 항목.

    Attributes:
        id: 정식 공급자 id (camelCase). 예 ``"dataGoKr"``.
        label: 사람용 표시명.
        envKey: 정본 환경변수명 (SecretStore 저장 키로도 사용).
        altEnvKeys: 추가 허용 환경변수명 (예 DART 멀티키 ``DART_API_KEYS``).
        purpose: dartlab 내 용도 한 줄.
        signupUrl: 발급/신청 URL.
        sources: 이 키를 쓰는 gather 소스/모듈 이름들.
        activation: 추가 발급 절차 (예 data.go.kr 활용신청 목록).
        keyHint: 키 형태 주의 (예 Decoding 키).
        operatorOnly: 운영자 sync/build 에서만 필요(라이브러리 read 불필요)면 True.
    """

    id: str
    label: str
    envKey: str
    altEnvKeys: tuple[str, ...] = ()
    purpose: str = ""
    signupUrl: str = ""
    sources: tuple[str, ...] = ()
    activation: str = ""
    keyHint: str = ""
    operatorOnly: bool = True


# 데이터 수집 공급자 레지스트리 (SSOT). 새 외부 데이터 소스 추가 시 여기 등록.
_DATA_PROVIDERS: dict[str, DataProviderSpec] = {
    "dataGoKr": DataProviderSpec(
        id="dataGoKr",
        label="공공데이터포털 (data.go.kr)",
        envKey="DATA_GO_KR_KEY",
        purpose="금융위 주가시세 · 관세청 수출입 무역통계 · 국민연금 가입사업장",
        signupUrl="https://www.data.go.kr",
        sources=("gov", "customs", "pension"),
        activation=(
            "단일 계정 인증키 1개로 공통. 활용신청(자동승인): "
            "금융위_주식시세정보 · 관세청_품목별 수출입실적(15101609) · "
            "국민연금공단_국민연금 가입 사업장 내역(3046071)."
        ),
        keyHint="Decoding 키 사용 (httpx params 가 serviceKey 를 1회 URL-encode).",
    ),
    "fred": DataProviderSpec(
        id="fred",
        label="FRED (미 세인트루이스 연준)",
        envKey="FRED_API_KEY",
        purpose="미국 거시·산업 시계열 (macro/fred 패널)",
        signupUrl="https://fred.stlouisfed.org/docs/api/api_key.html",
        sources=("fred",),
        keyHint="콤마 구분 멀티키 지원 (429 시 자동 rotate).",
    ),
    "ecos": DataProviderSpec(
        id="ecos",
        label="한국은행 ECOS",
        envKey="ECOS_API_KEY",
        purpose="한국 거시 시계열 (macro/ecos 패널)",
        signupUrl="https://ecos.bok.or.kr/api/#/",
        sources=("ecos",),
    ),
    "dart": DataProviderSpec(
        id="dart",
        label="금융감독원 OpenDART",
        envKey="DART_API_KEY",
        altEnvKeys=("DART_API_KEYS",),
        purpose="한국 공시·재무 원본 (정기보고서·재무제표)",
        signupUrl="https://opendart.fss.or.kr/",
        sources=("dart",),
        keyHint="키 90일 만료 — 갱신 필요. 멀티키는 DART_API_KEYS(콤마 구분).",
    ),
    "krx": DataProviderSpec(
        id="krx",
        label="KRX 정보데이터시스템",
        envKey="KRX_API_KEY",
        purpose="한국거래소 시세 (제3자 재배포 금지 — 비공개 캐시 전용)",
        signupUrl="http://data.krx.co.kr",
        sources=("krx",),
    ),
    "hf": DataProviderSpec(
        id="hf",
        label="Hugging Face",
        envKey="HF_TOKEN",
        purpose="parquet 데이터셋 read(공개는 토큰 불필요) + 운영자 업로드",
        signupUrl="https://huggingface.co/settings/tokens",
        sources=("bulkData", "pipeline"),
    ),
    "openfigi": DataProviderSpec(
        id="openfigi",
        label="OpenFIGI (Bloomberg)",
        envKey="OPENFIGI_API_KEY",
        purpose="심볼로지 매핑 (선택 — 미설정 시 rate-limit 낮춤)",
        signupUrl="https://www.openfigi.com/api",
        sources=("symbology",),
    ),
    # 네이버 검색 API 는 ID+Secret 2 키 → provider 2개로 국소 등록 (전역 secretEnvKey
    # 필드 신설은 모든 provider 영향이라 회피). naverNews.py 만 둘을 함께 안다.
    "naver": DataProviderSpec(
        id="naver",
        label="네이버 검색 API (Client ID)",
        envKey="NAVER_CLIENT_ID",
        purpose="네이버 뉴스 검색 (제목+스니펫) — 언론사 저작권, 비공개 캐시 전용",
        signupUrl="https://developers.naver.com/apps/",
        sources=("naverNews",),
        keyHint="개발자센터 '검색' API 등록 시 발급. Client Secret 은 naverSecret 공급자.",
        operatorOnly=False,
    ),
    "naverSecret": DataProviderSpec(
        id="naverSecret",
        label="네이버 검색 API (Client Secret)",
        envKey="NAVER_CLIENT_SECRET",
        purpose="네이버 검색 API 시크릿 (naver 공급자와 쌍)",
        signupUrl="https://developers.naver.com/apps/",
        sources=("naverNews",),
        operatorOnly=False,
    ),
}


def getSpec(providerId: str) -> DataProviderSpec:
    """공급자 spec 조회.

    Args:
        providerId: 정식 공급자 id (예 ``"dataGoKr"``).

    Returns:
        DataProviderSpec — 레지스트리 항목.

    Raises:
        CredentialError: 미등록 공급자 id.

    Example:
        >>> getSpec("dataGoKr").envKey
        'DATA_GO_KR_KEY'
    """
    spec = _DATA_PROVIDERS.get(providerId)
    if spec is None:
        known = ", ".join(sorted(_DATA_PROVIDERS))
        raise CredentialError(f"미등록 데이터 공급자: {providerId!r} (등록됨: {known})")
    return spec


def allSpecs() -> list[DataProviderSpec]:
    """등록된 모든 데이터 공급자 spec (id 정렬).

    Returns:
        list[DataProviderSpec] — 레지스트리 전체.

    Raises:
        없음.

    Example:
        >>> [s.id for s in allSpecs()][:1]
        ['dart']
    """
    return [_DATA_PROVIDERS[k] for k in sorted(_DATA_PROVIDERS)]


def _fromSecretStore(envKey: str) -> str | None:
    """SecretStore(암호화 파일)에서 키 조회 — 저장소 실패는 CredentialError."""
    try:
        from dartlab.core.providers.secrets import SecretStoreError, getSecretStore

        value = getSecretStore().get(envKey)
    except SecretStoreError as exc:
        raise CredentialError(f"{envKey}: SecretStore 조회 실패") from exc
    return value.strip() if value and value.strip() else None


def getKey(providerId: str, explicit: str | None = None) -> str | None:
    """공급자 키 해석 — 명시 → 환경변수 → SecretStore → None.

    Capabilities: 모든 데이터 소스의 *단일 env 해석 진입점*. 소스가 직접
        ``os.environ.get`` 하지 않고 본 함수를 거쳐 SecretStore 폴백까지 일관 적용.

    Args:
        providerId: 정식 공급자 id.
        explicit: 호출자가 직접 전달한 키 (최우선). 빈 문자열/None 은 무시.

    Returns:
        해석된 키 문자열, 또는 미설정 시 None.

    Raises:
        CredentialError: 미등록 공급자 id 또는 SecretStore 조회 실패.

    Example:
        >>> import os; os.environ["DATA_GO_KR_KEY"] = "abc"
        >>> getKey("dataGoKr")
        'abc'
    """
    if explicit and explicit.strip():
        return explicit.strip()
    spec = getSpec(providerId)
    for env in (spec.envKey, *spec.altEnvKeys):
        value = os.environ.get(env, "").strip()
        if value:
            return value
    return _fromSecretStore(spec.envKey)


def isConfigured(providerId: str) -> bool:
    """공급자 키 설정 여부.

    Args:
        providerId: 정식 공급자 id.

    Returns:
        bool — 환경변수 또는 SecretStore 에 키가 있으면 True.

    Raises:
        CredentialError: 미등록 공급자 id 또는 SecretStore 조회 실패.

    Example:
        >>> isConfigured("dataGoKr")  # doctest: +SKIP
        True
    """
    return getKey(providerId) is not None


def missingKeyMessage(providerId: str) -> str:
    """키 미설정 시 표시할 레지스트리 기반 안내 문구.

    Args:
        providerId: 정식 공급자 id.

    Returns:
        str — 발급 URL·환경변수명·활용신청 절차를 담은 여러 줄 안내.

    Raises:
        CredentialError: 미등록 공급자 id (getSpec 경유).

    Example:
        >>> "DATA_GO_KR_KEY" in missingKeyMessage("dataGoKr")
        True
    """
    spec = getSpec(providerId)
    lines = [
        f"{spec.label} 자격증명이 없습니다.",
        f"  환경변수 {spec.envKey} 를 .env 에 설정하거나 호출 시 키 인자를 전달하세요.",
    ]
    if spec.signupUrl:
        lines.append(f"  발급: {spec.signupUrl}")
    if spec.activation:
        lines.append(f"  신청: {spec.activation}")
    if spec.keyHint:
        lines.append(f"  주의: {spec.keyHint}")
    lines.append('  쉬운 설정: dartlab.gather.setCredential("%s", "<키>")  (암호화 저장, .env 편집 불필요)' % spec.id)
    return "\n".join(lines)


def resolveKey(providerId: str, explicit: str | None = None) -> str:
    """공급자 키 해석 — 없으면 안내 메시지로 CredentialError.

    Capabilities: getKey + 미설정 시 일관된 안내 예외. 데이터 소스 클라이언트가
        ``os.environ.get`` + 자체 예외 대신 본 함수 한 줄로 키 확보.

    Args:
        providerId: 정식 공급자 id.
        explicit: 호출자가 직접 전달한 키 (최우선).

    Returns:
        해석된 키 문자열 (비어있지 않음 보장).

    Raises:
        CredentialError: 키 미설정, 미등록 공급자 또는 SecretStore 조회 실패.

    Example:
        >>> import os; os.environ["DATA_GO_KR_KEY"] = "abc"
        >>> resolveKey("dataGoKr")
        'abc'
    """
    key = getKey(providerId, explicit)
    if not key:
        raise CredentialError(missingKeyMessage(providerId))
    return key


def setCredential(providerId: str, value: str) -> None:
    """공급자 키를 SecretStore(암호화)에 저장 — .env 편집 없는 쉬운 세팅.

    Capabilities: SecretStore.set 으로 영구 저장 → 이후 getKey/resolveKey 가
        자동 해석. DART 는 만료 추적(credentialLifecycle)도 동행.

    Args:
        providerId: 정식 공급자 id.
        value: 키 문자열.

    Returns:
        None.

    Raises:
        CredentialError: 미등록 공급자 id, 빈 값, 저장 또는 만료 메타데이터 기록 실패.

    Example:
        >>> setCredential("dataGoKr", "mykey")  # doctest: +SKIP
    """
    spec = getSpec(providerId)
    if not value or not value.strip():
        raise CredentialError(f"{spec.label}: 빈 키는 저장할 수 없습니다.")
    from dartlab.core.providers.secrets import SecretStoreError, getSecretStore

    try:
        getSecretStore().set(spec.envKey, value.strip())
    except SecretStoreError as exc:
        committed = bool(getattr(exc, "committed", False))
        state = "저장은 완료됐지만 마무리 실패" if committed else "SecretStore 저장 실패"
        raise CredentialWriteError(f"{spec.label}: {state}", committed=committed) from exc
    if spec.id == "dart":
        try:
            from dartlab.core.credentialLifecycle import recordIssuance

            recordIssuance(spec.envKey, lifetimeDays=90)
        except Exception as exc:
            raise CredentialWriteError(
                f"{spec.label}: 키 저장은 완료됐지만 만료 메타데이터 기록에 실패했습니다",
                committed=True,
            ) from exc


@dataclass(frozen=True)
class CredentialStatus:
    """단일 공급자 자격증명 상태 스냅샷."""

    id: str
    label: str
    envKey: str
    configured: bool
    source: str  # "env" | "secret" | "missing"
    purpose: str = field(default="")


def _sourceOf(spec: DataProviderSpec, secretNames: set[str]) -> str:
    for env in (spec.envKey, *spec.altEnvKeys):
        if os.environ.get(env, "").strip():
            return "env"
    if spec.envKey in secretNames:
        return "secret"
    return "missing"


def credentialStatus() -> list[CredentialStatus]:
    """모든 데이터 공급자의 설정 상태 (doctor 용).

    Returns:
        list[CredentialStatus] — 공급자별 configured/source.

    Raises:
        CredentialError: SecretStore 조회 실패.

    Example:
        >>> isinstance(credentialStatus(), list)
        True
    """
    try:
        from dartlab.core.providers.secrets import SecretStoreError, getSecretStore

        specs = allSpecs()
        secretNames = getSecretStore().usableKeys(spec.envKey for spec in specs)
    except SecretStoreError as exc:
        raise CredentialError("자격증명 상태용 SecretStore 조회 실패") from exc

    out: list[CredentialStatus] = []
    for spec in specs:
        src = _sourceOf(spec, secretNames)
        out.append(
            CredentialStatus(
                id=spec.id,
                label=spec.label,
                envKey=spec.envKey,
                configured=src != "missing",
                source=src,
                purpose=spec.purpose,
            )
        )
    return out


def formatStatus() -> str:
    """데이터 공급자 자격증명 상태표 (사람용 한 화면 doctor).

    Returns:
        str — 공급자별 ✓/✗ + 출처 + 미설정 시 발급 힌트.

    Raises:
        CredentialError: SecretStore 조회 실패.

    Example:
        >>> "공급자" in formatStatus()
        True
    """
    rows = credentialStatus()
    lines = ["데이터 공급자 자격증명 상태:", ""]
    for st in rows:
        mark = "✓" if st.configured else "✗"
        srcLabel = {"env": ".env/환경변수", "secret": "암호화 저장", "missing": "미설정"}[st.source]
        lines.append(f"  {mark} {st.label:28s} {st.envKey:18s} [{srcLabel}]")
    missing = [getSpec(st.id) for st in rows if not st.configured]
    if missing:
        lines.append("")
        lines.append("미설정 발급 안내:")
        for spec in missing:
            lines.append(f"  · {spec.label}: {spec.signupUrl}")
    return "\n".join(lines)


def envTemplate() -> str:
    """레지스트리 기반 `.env.example` 본문 생성 (SSOT 파생).

    Returns:
        str — 공급자별 용도·발급 URL 주석 + ``KEY=`` 빈 줄.

    Raises:
        없음.

    Example:
        >>> "DATA_GO_KR_KEY=" in envTemplate()
        True
    """
    lines = [
        "# DartLab 데이터 공급자 자격증명 (.env)",
        "# 이 파일을 복사해 .env 로 두고 값을 채우세요. 또는:",
        '#   dartlab.gather.setCredential("dataGoKr", "<키>")  (암호화 저장)',
        "# 상태 확인: dartlab.gather.credentialStatus() / python -m dartlab.gather.credentials",
        "",
    ]
    for spec in allSpecs():
        lines.append(f"# [{spec.id}] {spec.label} — {spec.purpose}")
        lines.append(f"#   발급: {spec.signupUrl}")
        if spec.activation:
            lines.append(f"#   신청: {spec.activation}")
        if spec.keyHint:
            lines.append(f"#   주의: {spec.keyHint}")
        lines.append(f"{spec.envKey}=")
        if spec.altEnvKeys:
            for alt in spec.altEnvKeys:
                lines.append(f"# {alt}=   # (선택) 멀티키 — 콤마 구분")
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "CredentialError",
    "CredentialStatus",
    "CredentialWriteError",
    "DataProviderSpec",
    "allSpecs",
    "credentialStatus",
    "envTemplate",
    "formatStatus",
    "getKey",
    "getSpec",
    "isConfigured",
    "missingKeyMessage",
    "resolveKey",
    "setCredential",
]
