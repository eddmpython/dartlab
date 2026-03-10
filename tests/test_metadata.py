"""metadata 모듈 테스트 — 데이터 구조 검증."""

import pytest

from dartlab.engines.ai.metadata import (
	MODULE_META,
	ColumnMeta,
	ModuleMeta,
	get_meta,
)


class TestModuleMeta:
	def test_core_modules_exist(self):
		"""핵심 모듈이 MODULE_META에 존재해야 한다."""
		core = ["BS", "IS", "CF", "audit", "dividend", "majorHolder", "employee",
				"executive", "segments", "fsSummary"]
		for name in core:
			assert name in MODULE_META, f"{name} missing from MODULE_META"

	def test_meta_fields_not_empty(self):
		"""모든 모듈의 label, description이 비어있지 않아야 한다."""
		for name, meta in MODULE_META.items():
			assert meta.label, f"{name}: label is empty"
			assert meta.description, f"{name}: description is empty"

	def test_get_meta(self):
		result = get_meta("BS")
		assert result is not None
		assert result.label == "재무상태표"

	def test_get_meta_none(self):
		result = get_meta("nonexistent_module")
		assert result is None

	def test_related_modules_valid(self):
		"""relatedModules의 값들이 MODULE_META 키에 존재해야 한다."""
		for name, meta in MODULE_META.items():
			for related in meta.relatedModules:
				assert related in MODULE_META, (
					f"{name}.relatedModules에 '{related}'가 있지만 MODULE_META에 없음"
				)

	def test_no_arbitrary_attrs(self):
		"""__slots__로 임의 속성 추가 차단 확인."""
		meta = get_meta("BS")
		with pytest.raises(AttributeError):
			meta.nonexistent_attr = "추가 시도"

	def test_column_meta_types(self):
		"""columns가 ColumnMeta 인스턴스의 tuple이어야 한다."""
		for name, meta in MODULE_META.items():
			assert isinstance(meta.columns, tuple), f"{name}: columns is not tuple"
			for col in meta.columns:
				assert isinstance(col, ColumnMeta), f"{name}: column is not ColumnMeta"

	def test_max_rows_positive(self):
		"""maxRows가 양수여야 한다."""
		for name, meta in MODULE_META.items():
			assert meta.maxRows > 0, f"{name}: maxRows={meta.maxRows}"
