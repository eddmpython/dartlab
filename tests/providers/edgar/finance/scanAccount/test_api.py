"""scanAccount 공개 호출 계약 회귀.

값 경로의 두터운 회귀는 ``tests/providers/edgar/finance/test_scanAccount.py`` 가
합성 shard 로 이미 덮는다. 여기서는 1,272 LoC 단일 모듈을 폴더로 가른 뒤에도
공개 표면과 위임 경계가 그대로인지 고정한다.
"""

from __future__ import annotations

import inspect

import pytest

import dartlab.providers.edgar.finance.scanAccount as pkg
from dartlab.providers.edgar.finance.scanAccount import api

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("name", ["scanAccount", "scanAccounts", "scanRatio"])
def testPublicCallablesStayOnPackageRoot(name: str) -> None:
    """소비자(scan router·builders)가 부르는 경로는 패키지 루트 그대로다."""
    assert callable(getattr(pkg, name))
    assert getattr(pkg, name) is getattr(api, name)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("scanAccount", "(dartSnakeId: 'str', *, freq: 'str' = 'Q') -> 'pl.DataFrame'"),
        ("scanRatio", "(ratioName: 'str', *, freq: 'str' = 'Q') -> 'pl.DataFrame'"),
        ("scanAccounts", "(dartSnakeIds: 'list[str]', *, freq: 'str' = 'Q') -> 'dict[str, pl.DataFrame]'"),
    ],
)
def testPublicSignaturesUnchangedBySplit(name: str, expected: str) -> None:
    """분할 전 실측한 시그니처와 한 글자도 다르지 않다."""
    assert str(inspect.signature(getattr(pkg, name))) == expected


def testErrorContractIsPublicOnPackage() -> None:
    """오류 계약은 패키지 공개 표면이다. 소비자가 하나로 잡을 수 있어야 한다."""
    assert issubclass(pkg.EdgarScanExecutionError, pkg.EdgarScanError)
    assert issubclass(pkg.EdgarScanMappingError, pkg.EdgarScanError)
    assert issubclass(pkg.EdgarScanStorageError, pkg.EdgarScanError)


def testApiDelegatesInsteadOfReimplementing() -> None:
    """api 는 실행과 이름 해소를 소유하지 않고 pipeline·taxonomy 에 위임한다."""
    source = inspect.getsource(api)

    assert "_scanAccountDuckDb" in source
    assert "_buildEdgarTagKeys" in source
    # SQL 본문과 파일 처리기는 api 가 소유하지 않는다.
    assert "GROUP BY" not in source
    assert "class _EdgarFileProcessor" not in source
