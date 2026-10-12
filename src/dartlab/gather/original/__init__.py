"""공시 오리지널 수집 — DART(정기+비정기) document.xml zip 원본 백업.

``gather ↛ providers`` 규칙을 지킨다. DART HTTP 는 같은 gather 층의 공용
``gather.dart.client.DartClient`` 를 쓴다. 2026-06-03 에는 providers 의존을 피하려 client 를 복제했지만
같은 날 DartClient 가 gather 로 옮겨 와 복제할 이유가 사라졌고, 복제본에는 재시도가 없었다(2026-10-12 통합).
DART 산출은 ``data/original/`` 로컬 백업(HF 미공개, publish-ready-gated)이며, parquet 운영 방향을 바꿀 때
ground truth 재파생 테스트용이다.
EDGAR 는 raw ``.txt`` 를 저장하지 않고 panel 빌드 경로에서 메모리 fetch 후 즉시
``edgar/panel`` 로 쓴다.

진입점::

    from dartlab.gather.original import archiveDartOriginals
    archiveDartOriginals("20260601", "20260603", scope="nonperiodic")

    # CLI
    python -m dartlab.gather.original dart --start 20260601 --end 20260603 --scope nonperiodic
"""

from __future__ import annotations

from .dart import archiveDartOriginals
from .paths import dartDocsDir, dartFilingsDir, originalRoot

__all__ = [
    "archiveDartOriginals",
    "originalRoot",
    "dartDocsDir",
    "dartFilingsDir",
]
