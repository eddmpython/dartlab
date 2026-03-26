"""EDINET sections — 유가증권보고서 section 수평화."""

from dartlab.providers.edinet.docs.sections.mapper import (
    mapSectionTitle,
    normalizeSectionTitle,
)

__all__ = ["normalizeSectionTitle", "mapSectionTitle"]
