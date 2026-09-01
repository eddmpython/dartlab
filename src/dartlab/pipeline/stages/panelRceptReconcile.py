"""panelRceptReconcile stage. DART 정기 rcept 와 HF panel 보유 rcept 를 대조해 누락분만 fetch+merge 한다.

forward ``dartZip`` 은 7일 전진 윈도만 본다. 그 윈도 안에 run 실패/timeout 이 끼면 해당 zip 은 panel 에
영영 안 들어온다(finance 의 60일+rcept 대조 자가치유와 비대칭). 본 stage 는 85일 윈도(``DART_PANEL_RECONCILE_DAYS``)
의 "있어야 할 정기 rcept" 와 HF panel ``rceptNo`` 차집합을 구해 그것만 회복한다. seed·번들·merge 헬퍼는
``dartZip`` 의 것을 그대로 쓴다(데이터손실 가드 상속). heal 은 ``_HEAL_CHUNK`` 종목씩 "원본 tar 먼저, panel 다음"
순으로 닫고 panel 업로드는 checkpoint 라, 분기 마감 뒤 수천 종목 backlog 가 job timeout 에 통째로 증발하지 않는다.

``dartZip`` 에서 분리한 이유는 파일 크기 규칙(800 LoC)과 관심사(전진 수집 vs 사후 대조)가 다르기 때문이다.
"""

from __future__ import annotations

import os
import time
from datetime import date, timedelta
from pathlib import Path

from dartlab.pipeline.stages import dartZip as _forward
from dartlab.pipeline.types import PipelineMode, StageResult

# reconcile heal chunk(종목 수). chunk 마다 원본 tar, panel 순으로 닫고 역사 zip 을 비워 디스크를 묶는다.
_HEAL_CHUNK = 200


def _pruneHistoryZips(docsBase: Path, codes: list[str], *, keep: dict[str, list[Path]]) -> int:
    """번들이 끝난 종목의 전이력 zip 을 지우고 이번 run 이 받은 zip(keep)만 남긴다(러너 디스크 반환).

    Args:
        docsBase: ``data/original/dart/docs``.
        codes: 정리할 종목코드.
        keep: ``{code: [남길 zip Path]}``. 이번 run 의 신규/heal zip(뒤따르는 panel 빌드 입력).

    Returns:
        지운 zip 수.

    Raises:
        OSError: zip 삭제가 거부될 때(권한 등). 정리 실패는 숨기지 않는다.

    Example:
        >>> _pruneHistoryZips(Path("data/original/dart/docs"), ["005930"], keep={"005930": [p]})  # doctest: +SKIP
        41
    """
    removed = 0
    for code in codes:
        keepNames = {path.name for path in keep.get(code) or []}
        companyDir = docsBase / code
        if not companyDir.is_dir():
            continue
        for zipPath in companyDir.glob("*.zip"):
            if zipPath.name in keepNames:
                continue
            zipPath.unlink(missing_ok=True)
            removed += 1
    return removed


# 정기보고서명 매칭(정정 prefix 허용) — syncRecent 와 동일 필터(panel 이 커버하는 보고서 한정).
_PERIODIC_RE = r"^(?:\[(?:기재정정|첨부정정|첨부추가)\]\s*)*(사업보고서|반기보고서|분기보고서)"


def _rceptsFromParquet(parquet) -> set[str]:
    """열린 panel parquet 의 보유 rcept 집합. footer 통계만으로 복원하고, 못 믿는 row group 만 실제로 읽는다.

    panel 작성기(``artifactWriter``)는 rcept 단위 stage 를 row group 으로 이어 붙이므로 한 row group 은
    한 rcept 의 행만 담고, ``write_statistics=True`` 라 footer 에 ``rceptNo`` min/max 가 실린다. 그래서
    footer 한 번(HTTP range 1~2 회)으로 집합이 정확히 나온다. 통계가 없거나 min 과 max 가 다른 row group 은
    그 group 의 ``rceptNo`` 컬럼만 읽어 보탠다. 2026-09-01 실측: 12 종목 738 row group 전부 통계와
    실제 컬럼이 일치했고, 컬럼 range-read 는 종목당 7~29 초였던 것이 footer 만 읽으면 1.7 초다.

    Args:
        parquet: ``pyarrow.parquet.ParquetFile``.

    Returns:
        보유 rcept 집합.

    Raises:
        없음 (pyarrow 예외는 호출자가 격리).

    Example:
        >>> import pyarrow.parquet as pq  # doctest: +SKIP
        >>> _rceptsFromParquet(pq.ParquetFile("005930.parquet"))  # doctest: +SKIP
        {'20240514001234', ...}
    """
    metadata = parquet.metadata
    columnIndex = next((i for i in range(metadata.num_columns) if metadata.schema.column(i).name == "rceptNo"), None)
    if columnIndex is None:
        return set()
    owned: set[str] = set()
    fallbackGroups: list[int] = []
    for groupIndex in range(metadata.num_row_groups):
        stats = metadata.row_group(groupIndex).column(columnIndex).statistics
        if stats is None or not stats.has_min_max or stats.min != stats.max:
            fallbackGroups.append(groupIndex)
            continue
        if stats.min:  # 빈 문자열 group 은 컬럼 경로와 같이 보유로 세지 않는다
            owned.add(str(stats.min))
    for groupIndex in fallbackGroups:
        column = parquet.read_row_group(groupIndex, columns=["rceptNo"]).column("rceptNo")
        owned.update(str(x) for x in column.to_pylist() if x)
    return owned


def _panelRceptsFromHf(repo: str, relDir: str, code: str, *, token: str | None) -> set[str] | None:
    """HF panel parquet 의 보유 rcept 집합 (full download 회피).

    ``HfFileSystem`` 파일핸들 위에서 footer 만 HTTP Range 로 읽고 ``_rceptsFromParquet`` 로 집합을
    복원한다. reconcile 탐지(수천 종목)와 신선도 감사(정기보고서 마감 주 2,700 종목)를 예산 안에서
    전수로 끝내는 핵심.

    Args:
        repo: HF dataset repo id (``repoFor("panel")``).
        relDir: panel 카테고리 상대 디렉터리 (``dart/panel``).
        code: 종목코드.
        token: HF 토큰.

    Returns:
        보유 rcept 집합. panel 미존재(404)는 **빈 set** (보유 0 = 윈도 rcept 전부 누락으로
        판정되어 heal 대상), 일시 실패는 ``None`` (탐지 대상 제외 = 안전 skip).

    Raises:
        없음. 모든 예외를 None 으로 격리해 한 종목 실패가 reconcile 전체를 막지 않는다.

    Example:
        >>> _panelRceptsFromHf("eddmpython/dartlab-data", "dart/panel", "005930", token=None)  # doctest: +SKIP
        {'20240514001234', ...}
    """
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    path = f"datasets/{repo}/{relDir}/{code}.parquet"
    try:
        fs = HfFileSystem(token=token)
        with fs.open(path, "rb") as fh:
            return _rceptsFromParquet(pq.ParquetFile(fh))
    except FileNotFoundError:
        # panel 미존재 = 보유 rcept 0. None(=skip) 으로 두면 "panel 이 한 번도 없던 종목" 은
        # 영구히 heal 대상 밖이라 신규 상장·과거 누락분이 절대 복구되지 않는다(실측: 178600·185190).
        # 빈 set 이면 윈도 rcept 전부가 누락으로 잡히고, len(have)=0 이 truncation 의심에도 걸려
        # 전이력까지 회복된다.
        return set()
    # 일시 실패는 skip 후 다음 run 회복
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] dartZip panel rcept 조회 실패: {type(exc).__name__}: {exc}", flush=True)
        return None


def _fullPeriodicRcepts(client, code: str) -> set[str]:
    """종목 전이력 정기보고서(사업/반기/분기) rcept 집합 — listFilings corp 지정 전기간 조회.

    truncation(history 파괴) 회복용: 85일 윈도로는 못 보는 옛 분기까지 "있어야 할 rcept" 전체.
    corp 지정 시 DART list.json 이 전 기간(3개월 cap 우회) 조회 가능 → 단일 호출 누적 매니페스트.
    report_nm 필터로 비정기 A 공시 제외. 개별 조회 실패는 빈 set(다음 run 재시도).

    Args:
        client: 인증된 DartClient.
        code: 종목코드.

    Returns:
        전이력 정기 rcept ``set`` (조회/필터 실패 시 빈 set).

    Raises:
        없음 (개별 종목 조회 실패는 빈 set 으로 격리).

    Example:
        >>> _fullPeriodicRcepts(client, "043260")  # doctest: +SKIP
        {'20160330002098', ...}
    """
    import polars as pl

    from dartlab.gather.dart.disclosure import listFilings

    try:
        df = listFilings(client, code, start="20110101", filingType="A", fetchAll=True)
    # 개별 종목 실패는 빈 set 후 다음 run 회복
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] dartZip 정기보고서 rcept 조회 실패: {type(exc).__name__}: {exc}", flush=True)
        return set()
    if df.is_empty() or "report_nm" not in df.columns or "rcept_no" not in df.columns:
        return set()
    return set(df.filter(pl.col("report_nm").str.contains(_PERIODIC_RE)).select("rcept_no").to_series().to_list())


def runPanelRceptReconcile(
    *,
    category: str = "dartOriginal",
    mode: PipelineMode = "incremental",
    codes: list[str] | None = None,
    upload: bool = True,
    token: str | None = None,
) -> StageResult:
    """rcept 단위(파일 내) panel reconcile — DART 에 있는 정기 rcept 가 panel 에 빠졌으면 자가치유.

    forward ``dartZip`` 은 7일 전진 윈도만 본다 → 그 윈도 안에 run 실패/타임아웃이면 해당 zip 이
    영구 누락된다(finance 의 60일+rcept 대조 자가치유와의 구조적 비대칭). 기존 ``panelReconcile``
    은 *파일집합* 차분뿐이라 "파일은 있는데 안에 분기 rcept 만 빠진" 갭을 못 잡는다. 본 stage 가
    그 갭을 메운다:

        listFilings(A, 윈도) "있어야 할 정기 rcept" − HF panel ``rceptNo`` "보유 rcept"
          = 누락 rcept → 그것만 fetch → 검증된 dartZip 헬퍼로 merge·번들·push.

    ``_seedChangedFromHf``(원본 tar full 이력 복원 후 superset 재번들)·``_buildPanelIncremental``
    (panel HF merge base seed 후 신규 분기만 merge)·``_bundleAndUpload`` 를 그대로 재사용해
    forward 와 동일한 데이터손실 가드(404 vs 일시실패 분기·부분추출 차단)를 상속한다. 탐지는
    HfFileSystem 컬럼 range-read 라 싸고, heal 은 누락 rcept 만 fetch 한다.

    Args:
        category: 미사용("dartOriginal" 고정).
        mode: 미사용.
        codes: 한정할 종목코드(없으면 윈도 내 전 정기 filer 후보). 지정 시 그 종목만 점검.
        upload: HF 업로드 여부.
        token: HF 토큰.

    Returns:
        StageResult (changedFiles=재빌드된 panel 종목, uploaded=원본 tar 수).

    Raises:
        없음 (listFilings/탐지/heal 예외는 StageResult 로 격리).

    Example:
        >>> runPanelRceptReconcile(upload=False)  # doctest: +SKIP
        StageResult(category='dartOriginal', ...)
    """
    import polars as pl

    import dartlab.config as cfg
    from dartlab.core.dataConfig import DATA_RELEASES, repoFor
    from dartlab.gather.dart.client import DartClient
    from dartlab.gather.dart.disclosure import listFilings
    from dartlab.gather.dart.document import iterZipsParallel
    from dartlab.pipeline.hfUpload import _resolveHfToken

    # corp 생략 list.json 은 DART 가 3개월(~92일) 윈도 제한 → 기본 85 일(현 백로그 커버·cap 안쪽).
    days = int(os.environ.get("DART_PANEL_RECONCILE_DAYS") or "85")
    today = date.today()
    start = (today - timedelta(days=days - 1)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    res = StageResult(category="dartOriginal")
    codeFilter = set(codes) if codes else None

    client = DartClient()
    try:
        df = listFilings(client, corp=None, start=start, end=end, filingType="A", fetchAll=True)
    except Exception as exc:  # noqa: BLE001 — 공시목록 조회 실패 격리
        res.report.err = 1
        res.report.failures.append(f"panelRceptReconcile listFilings: {type(exc).__name__}: {exc}")
        return res

    if df.is_empty() or "rcept_no" not in df.columns or "stock_code" not in df.columns:
        res.report.ok = 1
        print(f"[pipeline] panelRceptReconcile {start}~{end}: 정기공시 0", flush=True)
        return res

    filt = df.filter(
        pl.col("report_nm").str.contains(_PERIODIC_RE)
        & pl.col("stock_code").is_not_null()
        & (pl.col("stock_code").str.strip_chars() != "")
    )
    cand: dict[str, set[str]] = {}
    for sc, rc in filt.select(["stock_code", "rcept_no"]).iter_rows():
        sc = (sc or "").strip()
        if not sc or not rc:
            continue
        if codeFilter is not None and sc not in codeFilter:
            continue
        cand.setdefault(sc, set()).add(str(rc))

    if not cand:
        res.report.ok = 1
        print(f"[pipeline] panelRceptReconcile {start}~{end}: 후보 0", flush=True)
        return res

    # 탐지 1 — HF panel rceptNo 컬럼만 병렬 range-read → 종목별 보유 rcept.
    from concurrent.futures import ThreadPoolExecutor, as_completed

    repo = repoFor("panel")
    relDir = DATA_RELEASES["panel"]["dir"]
    tok = _resolveHfToken(token)
    truncSuspect = int(os.environ.get("DART_PANEL_TRUNC_SUSPECT") or "6")
    panelHave: dict[str, set[str]] = {}
    newOrFlaky = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_panelRceptsFromHf, repo, relDir, sc, token=tok): sc for sc in cand}
        for fut in as_completed(futs):
            sc = futs[fut]
            have = fut.result()
            if have is None:
                newOrFlaky += 1  # 조회 일시 실패 · 다음 run 재시도(미존재는 빈 set 으로 heal 대상)
                continue
            panelHave[sc] = have

    missingByCode: dict[str, set[str]] = {}
    # ② 최신 분기 누락(025560-class) — 윈도 정기 rcept − panel 보유.
    for sc, have in panelHave.items():
        miss = cand[sc] - have
        if miss:
            missingByCode[sc] = set(miss)
    # ③ history 파괴(043260-class) — panel 보유 rcept 가 비정상적으로 적은 종목은 전이력 대조
    #    (윈도로는 옛 분기를 못 봄). 신규 상장은 전이력도 적어 fullMiss≈∅ → 오회복 0.
    suspects = sorted(sc for sc, have in panelHave.items() if len(have) <= truncSuspect)
    truncated = 0
    for sc in suspects:
        fullMiss = _fullPeriodicRcepts(client, sc) - panelHave[sc]
        if len(fullMiss) > len(missingByCode.get(sc, set())):
            truncated += 1
        if fullMiss:
            missingByCode.setdefault(sc, set()).update(fullMiss)
    res.report.ok = 1
    missRcepts = sum(len(v) for v in missingByCode.values())
    print(
        f"[pipeline] panelRceptReconcile {start}~{end}: 후보 {len(cand)}종목 · 조회실패 {newOrFlaky} · "
        f"truncation의심 {len(suspects)}(회복 {truncated}) · 누락 {len(missingByCode)}종목 {missRcepts}rcept",
        flush=True,
    )
    if not missingByCode:
        return res

    # heal. 누락 rcept 를 _HEAL_CHUNK 종목씩 "zip fetch, 원본 tar, panel" 순으로 닫는다. 분기 마감 뒤에는 누락이
    # 수천 종목이라 한 덩어리로 돌리면 (a) 첫 체크포인트가 수천 zip 의 일괄 fetch 뒤에야 나와 DART 가 느린 날엔
    # timeout 까지 아무것도 남지 않고(2026-08-22 실측: 탐지 뒤 2시간 24분 fetch 무응답, 취소) (b) 전 종목 tar
    # 이력 + panel seed 가 러너 디스크에 동시에 쌓인다. chunk 마다 tar 를 먼저 올려 원본 SSOT 를 panel 보다
    # 앞세우고, 번들이 끝난 역사 zip(디스크의 대부분)은 지워 그 몫을 chunk 크기로 묶는다.
    docsBase = Path(cfg.dataDir) / "original" / "dart" / "docs"
    fetchWorkers = int(os.environ.get("DART_FETCH_WORKERS") or "4")
    codes = sorted(missingByCode)
    totalTargets = sum(len(v) for v in missingByCode.values())
    fetchedTotal = 0
    built: list[str] = []
    for offset in range(0, len(codes), _HEAL_CHUNK):
        chunkCodes = codes[offset : offset + _HEAL_CHUNK]
        label = f"chunk {offset + len(chunkCodes)}/{len(codes)}종목"
        targets = [(sc, rc) for sc in chunkCodes for rc in sorted(missingByCode[sc])]
        newZipsByCode: dict[str, list[Path]] = {}
        startedAt = time.monotonic()
        for index, (sc, rc, ok, _n) in enumerate(
            iterZipsParallel(client, targets, outDir=docsBase, workers=fetchWorkers), start=1
        ):
            if ok:
                newZipsByCode.setdefault(sc, []).append(docsBase / sc / f"{rc}.zip")
            if index % 100 == 0:  # 진행 로그. 긴 fetch 가 멈춘 것인지 느린 것인지 로그만으로 가른다.
                print(
                    f"[pipeline] panelRceptReconcile: {label} zip fetch {index}/{len(targets)} "
                    f"({time.monotonic() - startedAt:.0f}s)",
                    flush=True,
                )
        fetched = sum(len(v) for v in newZipsByCode.values())
        fetchedTotal += fetched
        print(
            f"[pipeline] panelRceptReconcile: {label} zip fetch {fetched}/{len(targets)} "
            f"({time.monotonic() - startedAt:.0f}s)",
            flush=True,
        )
        chunk = sorted(newZipsByCode)
        if not chunk:
            continue
        if upload:
            # 원본 tar: full 이력 복원(_seedChangedFromHf) 후 superset 재번들(부분이력 truncation 가드).
            try:
                _seeded, archiveSafe = _forward._seedChangedFromHf(chunk, token=token)
                res.uploaded += _forward._bundleAndUpload(sorted(set(chunk) & archiveSafe), token=token)
            except Exception as exc:  # noqa: BLE001 (원본 업로드 실패 격리. panel 은 별도 push)
                res.report.fail = 1
                res.report.failures.append(f"panelRceptReconcile original upload: {type(exc).__name__}: {exc}")
            if os.environ.get("DART_ZIP_SEED", "1") == "1":  # CI 러너(이력 0 전제)만 정리. 로컬 전체 이력은 보존.
                _pruneHistoryZips(docsBase, chunk, keep=newZipsByCode)
        # 빌드. forward 와 동일 within-company 증분(panel HF merge base seed 후 신규 분기만 merge) + checkpoint 업로드.
        built.extend(
            _forward._buildPanelIncremental(
                chunk, newZipsByCode, res, token=token, uploadEvery=_forward._PANEL_UPLOAD_EVERY if upload else None
            )
        )
        print(f"[pipeline] panelRceptReconcile: {label} · 누적 재빌드 {len(built)}", flush=True)
    if totalTargets and fetchedTotal == 0:
        res.report.fail = 1
        res.report.failures.append(f"panelRceptReconcile: zip fetch 0/{totalTargets} (다음 run 재시도)")
    res.changedFiles = built
    print(
        f"[pipeline] panelRceptReconcile: panel 재빌드 {len(built)}/{len(codes)}종목 · zip fetch {fetchedTotal}/{totalTargets}",
        flush=True,
    )
    return res
