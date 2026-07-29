"""dartlab 수집 파이프라인 — in-library L4 sink 오케스트레이션.

흩어진 ``.github/scripts/sync/*`` 의 fetch(gather)→build(providers)→upload(HF) 조합을
테스트 가능한 라이브러리 코드로 모은 단일 SSOT. 로컬 CLI(`dartlab sync`)와 CI
워크플로(`python -m dartlab.pipeline <stage>`)가 동일 진입점을 호출한다.

⛔ 레이어: 본 패키지는 ``gather/``·``providers/`` 폴더 *밖*의 L4 sink 라 둘을 동시
import 하는 게 합법(`test_l1_no_cross_import` 무위반). sink 자격은 두 가드에 등록돼
보장된다 — Guard Index ``LAYER_OF`` 의 L4 선언 +
``tests/audit/cycleScan.py`` PRIMARY_PACKAGES. 단방향: ``cli → pipeline`` 만,
``pipeline ↛ cli``.

orchestrator/stages 는 후속 웨이브에서 채운다(W0 = 타입·매니페스트·해시 기반).
"""

from __future__ import annotations

from dartlab.pipeline.changed import changedPath, readChanged, writeChanged
from dartlab.pipeline.hashing import diffChanged, fileHash, snapshotHashes
from dartlab.pipeline.hfUpload import uploadCategoryToHf
from dartlab.pipeline.orchestrator import describeStages, listStages, runPipeline, runStage
from dartlab.pipeline.seed import seedCategoriesFromHf
from dartlab.pipeline.types import PipelineMode, StageReport, StageResult, StageSpec

__all__ = [
    "PipelineMode",
    "StageReport",
    "StageResult",
    "StageSpec",
    "changedPath",
    "readChanged",
    "writeChanged",
    "fileHash",
    "snapshotHashes",
    "diffChanged",
    "uploadCategoryToHf",
    "seedCategoriesFromHf",
    "runStage",
    "runPipeline",
    "listStages",
    "describeStages",
]
