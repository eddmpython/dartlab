"""계정 매핑 무결성 테스트.

accountMappings.json의 구조적 건전성과 핵심 계정 매핑 경로를 검증한다.
데이터 로드 없이 JSON + Python dict 검사만 수행 → unit 마커.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_MAPPER_DATA = (
    Path(__file__).resolve().parent.parent / "src" / "dartlab" / "providers" / "dart" / "finance" / "mapperData"
)
_MAPPINGS_PATH = _MAPPER_DATA / "accountMappings.json"


# ══════════════════════════════════════
# JSON 구조 검증
# ══════════════════════════════════════


class TestMappingJsonIntegrity:
    """accountMappings.json의 구조적 무결성."""

    @pytest.fixture(scope="class")
    def mapping_data(self):
        assert _MAPPINGS_PATH.exists(), f"{_MAPPINGS_PATH} not found"
        with open(_MAPPINGS_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_json_parseable(self, mapping_data):
        """JSON이 정상 파싱됨."""
        assert isinstance(mapping_data, dict)

    def test_has_mappings_key(self, mapping_data):
        """mappings 키 존재."""
        assert "mappings" in mapping_data
        assert isinstance(mapping_data["mappings"], dict)

    def test_mapping_count_baseline(self, mapping_data):
        """매핑 총 수가 기준선(34000) 이상 → 후퇴 감지."""
        count = len(mapping_data["mappings"])
        assert count >= 34_000, f"매핑 수 {count}개 < 34000 → 의도치 않은 후퇴"

    def test_all_values_are_strings(self, mapping_data):
        """모든 매핑 값(snakeId)이 문자열."""
        bad = [k for k, v in mapping_data["mappings"].items() if not isinstance(v, str)]
        assert len(bad) == 0, f"비문자열 값: {bad[:5]}"

    def test_no_empty_keys_or_values(self, mapping_data):
        """빈 키나 빈 값 없음."""
        empty_keys = [k for k in mapping_data["mappings"] if not k.strip()]
        empty_vals = [k for k, v in mapping_data["mappings"].items() if not v.strip()]
        assert len(empty_keys) == 0, f"빈 키: {empty_keys[:5]}"
        assert len(empty_vals) == 0, f"빈 값: {empty_vals[:5]}"

    def test_standard_accounts_exist(self, mapping_data):
        """standardAccounts 섹션 존재."""
        sa = mapping_data.get("standardAccounts", {})
        assert len(sa) >= 100, f"standardAccounts {len(sa)}개 < 100"


# ══════════════════════════════════════
# 핵심 계정 매핑 경로 검증
# ══════════════════════════════════════


# 이 계정들은 ratios.py, builder.py, grading.py 등에서 실제로 사용됨
_CRITICAL_SNAKE_IDS = [
    "sales",
    "operating_profit",
    "net_profit",
    "cost_of_sales",
    "gross_profit",
    "total_assets",
    "total_liabilities",
    "total_stockholders_equity",
    "owners_of_parent_equity",
    "current_assets",
    "current_liabilities",
    "cash_and_cash_equivalents",
    "inventories",
    "trade_and_other_receivables",
    "trade_and_other_payables",
    "operating_cashflow",
    "retained_earnings",
    "tangible_assets",
]


class TestCriticalAccounts:
    """핵심 18개 계정의 매핑 도달 가능성."""

    @pytest.fixture(scope="class")
    def target_snake_ids(self):
        with open(_MAPPINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return set(data["mappings"].values())

    @pytest.mark.parametrize("snake_id", _CRITICAL_SNAKE_IDS)
    def test_critical_account_reachable(self, snake_id, target_snake_ids):
        """핵심 계정 snakeId가 매핑 결과에 최소 1번 등장."""
        assert snake_id in target_snake_ids, f"핵심 계정 '{snake_id}'가 매핑 결과에 없음"


# ══════════════════════════════════════
# ID_SYNONYMS / ACCOUNT_NAME_SYNONYMS 검증
# ══════════════════════════════════════


class TestSynonyms:
    """동의어 사전 일관성 검증."""

    def test_id_synonyms_no_circular(self):
        """ID_SYNONYMS에 순환 참조 없음 (A→B, B→A 금지)."""
        from dartlab.providers.dart.finance.mapper import ID_SYNONYMS

        for key, val in ID_SYNONYMS.items():
            if val in ID_SYNONYMS:
                target = ID_SYNONYMS[val]
                assert target != key, f"순환 참조: {key}→{val}→{key}"

    def test_account_name_synonyms_no_circular(self):
        """ACCOUNT_NAME_SYNONYMS에 순환 참조 없음."""
        from dartlab.providers.dart.finance.mapper import ACCOUNT_NAME_SYNONYMS

        for key, val in ACCOUNT_NAME_SYNONYMS.items():
            if val in ACCOUNT_NAME_SYNONYMS:
                target = ACCOUNT_NAME_SYNONYMS[val]
                assert target != key, f"순환 참조: {key}→{val}→{key}"

    def test_id_synonyms_values_exist(self):
        """ID_SYNONYMS의 값이 빈 문자열이 아님."""
        from dartlab.providers.dart.finance.mapper import ID_SYNONYMS

        empty = [k for k, v in ID_SYNONYMS.items() if not v.strip()]
        assert len(empty) == 0, f"빈 값 동의어: {empty[:5]}"


# ══════════════════════════════════════
# AccountMapper 기본 동작 (mock 없이)
# ══════════════════════════════════════


class TestMapperBasic:
    """AccountMapper의 기본 매핑 동작."""

    def test_revenue_maps(self):
        """'매출액'이 'sales'로 매핑."""
        from dartlab.providers.dart.finance.mapper import AccountMapper

        m = AccountMapper.get()
        result = m.map("", "매출액")
        assert result == "sales", f"'매출액' → {result}"

    def test_total_assets_maps(self):
        """'자산총계'가 'total_assets'로 매핑."""
        from dartlab.providers.dart.finance.mapper import AccountMapper

        m = AccountMapper.get()
        result = m.map("", "자산총계")
        assert result == "total_assets", f"'자산총계' → {result}"

    def test_ifrs_prefix_stripped(self):
        """IFRS prefix가 제거되고 올바르게 매핑."""
        from dartlab.providers.dart.finance.mapper import AccountMapper

        m = AccountMapper.get()
        result = m.map("ifrs-full_Revenue", "")
        # Revenue → sales (ID_SYNONYMS 경유)
        assert result is not None

    def test_unmapped_returns_none(self):
        """존재하지 않는 계정은 None."""
        from dartlab.providers.dart.finance.mapper import AccountMapper

        m = AccountMapper.get()
        result = m.map("", "이상한계정명_절대없을거야_abc123")
        assert result is None
