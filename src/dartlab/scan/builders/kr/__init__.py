"""KR scan builder compatibility exports.

Capabilities:
    - Re-exports the historically public KR scan builder entry points.

Args:
    This package exposes imports only.

Returns:
    Builder functions imported from domain subpackages.

Example:
    >>> from dartlab.scan.builders.kr import buildScan, buildDocsIndex

Guide:
    Keep this package thin. Implementation belongs in ``core`` or domain packages such as
    ``docs``, ``finance``, and ``report``.

SeeAlso:
    ``core``, ``docs.index``, ``docs.changes``, ``finance.lite``, and ``report.fields``.

Requires:
    Domain modules import successfully.

AIContext:
    Preserves public builder imports while the codebase moves to a domain tree.

LLM Specifications:
    AntiPatterns: Do not add builder implementation logic here.
    OutputSchema: Re-exported builder callables.
    Prerequisites: Caller imports concrete functions.
    Freshness: No data access in package init.
    Dataflow: package import -> domain implementation import.
    TargetMarkets: KR scan builder public surface.
"""

from dartlab.scan.builders.kr.core import (  # noqa: F401
    buildAffiliateDocs,
    buildChanges,
    buildFinance,
    buildReport,
    buildScan,
)
from dartlab.scan.builders.kr.docs.index import (  # noqa: F401
    buildDocsIndex,
    buildEdgarDocsIndex,
    buildEdinetDocsIndex,
)
from dartlab.scan.builders.kr.valuationBuild import buildValuation  # noqa: F401
