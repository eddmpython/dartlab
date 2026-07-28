"""`dartlab.data` 는 `dartlab.dataHub` 의 호환 별칭이다.

정본은 폴더·import·capability key·문서 전부 `dataHub` 다 (`operation.architecture`
L2.5). 여기서는 이름만 잇는다.

예전에는 이 파일이 `dataHub` 의 공개 심볼을 하나씩 복사하고 위임 전용 module 클래스를
따로 세웠다. 그래서 같은 이름이 두 객체를 줬다. `dartlab.data` 속성은 dataHub module
이고 `import dartlab.data` 는 이 호환 module 이라, 둘을 `is` 로 비교하면 달랐고 한쪽에만
심볼이 늘면 조용히 어긋났다. 이제 sys.modules 자리를 dataHub module 그 자체로 바꿔
두 문법이 같은 객체를 가리키게 한다. 복사할 심볼 목록도 위임 클래스도 필요 없다.
"""

from __future__ import annotations

import importlib
import sys

sys.modules[__name__] = importlib.import_module("dartlab.dataHub")
