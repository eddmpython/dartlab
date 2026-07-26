"""Production immutable generation store facade."""

from __future__ import annotations

from .maintenance import MaterializationMaintenance


class MaterializationStore(MaterializationMaintenance):
    """Immutable Data Workbench generation store."""
