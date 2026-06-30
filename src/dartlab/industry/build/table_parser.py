"""Industry table parser compatibility helpers.

Industry edge extraction consumes the canonical DART table-row parser.  This
module preserves the historical ``industry.build.table_parser`` import path.
"""

from __future__ import annotations

from dartlab.providers.dart.tableRows import (
    extractCorpNames,
    findTableByHeaders,
    normalizeCorpName,
    parseAmount,
    parsePercent,
)

__all__ = [
    "extractCorpNames",
    "findTableByHeaders",
    "normalizeCorpName",
    "parseAmount",
    "parsePercent",
]
