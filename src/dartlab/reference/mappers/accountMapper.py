"""AccountMapper — accountMappings.json 읽기 전용 래퍼.

본 래퍼는 ``MapperEngine`` 인터페이스 (``BaseMapper.lookup``) 어댑터.
실제 매핑 로직은 단일 소유 엔진 ``core.accounts.AccountNormalizer`` (12 단계
fallback, 역인덱스 3 종, suffix 흡수) 에 *직결 위임* (facade 우회 X — owner 직접).
같은 사전 위 두 가지 매칭 로직 분산 = SSOT 위반 차단.
"""

from __future__ import annotations

from dartlab.core.mapperEngine import BaseMapper, MapperStats


class AccountMapper(BaseMapper):
    """accountMappings.json (34,000+ 매핑) 래퍼."""

    @property
    def name(self) -> str:
        """Return mapper registry name.

        Args:
            None.

        Returns:
            Registry key for this mapper.

        Requires:
            None.

        Raises:
            None.

        Example:
            >>> AccountMapper().name
            'account'
        """
        return "account"

    def _data(self) -> dict:
        from dartlab.core.accounts.data import loadAccounts

        return loadAccounts()

    def _mappings(self) -> dict[str, str]:
        """korName → snakeId 매핑."""
        return self._data().get("mappings", {})

    def _standardAccounts(self) -> dict[str, dict]:
        """{snakeId: {korName, code, level, sj}}."""
        return self._data().get("standardAccounts", {})

    def lookup(self, key: str) -> dict | None:
        """한국어 계정명·영문 ID·snakeId 조회 (본진 12 단계 fallback 위임).

        본진 ``providers.dart.finance.mapper.AccountMapper`` 의 ``map()``
        에 위임 — synonym · 공백/괄호/하이픈 변형 · 액 suffix 흡수 까지
        12 단계 fallback 일관 적용. snakeId 직접 조회는 본진이 흡수 못
        하므로 ``standardAccounts`` fallback 으로 보완.

        Capabilities:
            Account mapping lookup by Korean label, IFRS/dart ID, or snakeId.
        AIContext:
            Used when natural-language finance labels must resolve to stable account ids.
        Guide:
            Prefer this over reading ``accountMappings.json`` directly.
        When:
            Called by mapper engine consumers during account normalization.
        How:
            Delegates to engine ``map()`` for korean/id input; falls back to
            ``standardAccounts`` direct lookup for snakeId input.
        Args:
            key: Korean account name, IFRS/dart account ID, or snakeId.
        Returns:
            Account detail dict (``{snakeId, ...}``) or ``None``.
        Requires:
            Bundled account mapping data.
        Raises:
            Propagates mapping data load errors.
        Example:
            >>> AccountMapper().lookup("__missing__") is None
            True
        SeeAlso:
            ``korToSnakeId`` and ``snakeIdToKor`` ·
            ``providers.dart.finance.mapper.AccountMapper.map``.
        """
        from dartlab.core.accounts import AccountNormalizer

        norm = AccountNormalizer.get()
        standards = self._standardAccounts()

        # 1. key 를 한글명으로 시도 — owner 12 단계 fallback 흡수
        snakeId = norm.normalize("", key)
        # 2. None 이면 영문 id 로 재시도 (synonym + prefix 정규화)
        if snakeId is None:
            snakeId = norm.normalize(key, "")
        # 3. 둘 다 None 이면 key 가 이미 snakeId 인 경우
        if snakeId is None and key in standards:
            return {"snakeId": key, **standards[key]}
        if snakeId is None:
            return None
        return {"snakeId": snakeId, **standards.get(snakeId, {})}

    def stats(self) -> MapperStats:
        """Return account mapper statistics.

        Capabilities:
            Reports mapping entry counts and metadata freshness.
        AIContext:
            Helps audits summarize mapper coverage.
        Guide:
            Use for diagnostics, not per-row mapping.
        When:
            Called by ``MapperEngine.summary`` and audit tests.
        How:
            Counts mapping and standard account entries from the bundled data.
        Args:
            None.
        Returns:
            ``MapperStats`` for account mappings.
        Requires:
            Bundled account mapping data.
        Raises:
            Propagates mapping data load errors.
        Example:
            >>> AccountMapper().stats().name
            'account'
        SeeAlso:
            ``MapperStats``.
        """
        data = self._data()
        mappings = data.get("mappings", {})
        standards = data.get("standardAccounts", {})
        meta = data.get("_metadata", {})
        return MapperStats(
            name=self.name,
            totalEntries=len(mappings),
            mappedEntries=len(mappings),
            coverage=1.0 if mappings else 0.0,
            lastUpdated=meta.get("lastUpdate", ""),
        )

    def allKeys(self) -> list[str]:
        """Return all Korean account names.

        Args:
            None.

        Returns:
            Korean account name list.

        Requires:
            Bundled account mapping data.

        Raises:
            Propagates mapping data load errors.

        Example:
            >>> isinstance(AccountMapper().allKeys(), list)
            True
        """
        return list(self._mappings().keys())

    def snakeIds(self) -> list[str]:
        """등록된 모든 snakeId.

        Args:
            None.

        Returns:
            Registered snakeId list.

        Requires:
            Bundled standard account data.

        Raises:
            Propagates mapping data load errors.

        Example:
            >>> isinstance(AccountMapper().snakeIds(), list)
            True
        """
        return list(self._standardAccounts().keys())

    def korToSnakeId(self, korName: str) -> str | None:
        """한국어 계정명 → snakeId.

        본 모듈의 SSOT 선언대로 매칭은 ``AccountNormalizer`` 한 곳만 소유한다. 예전에는
        같은 사전을 raw dict 조회로 한 번 더 훑어, ``lookup`` 이 해소하는 한글명(공백·
        괄호·하이픈 변형, synonym, "액" 접미 흡수)을 여기서는 ``None`` 으로 돌려줬다.

        Args:
            korName: Korean account name.

        Returns:
            snakeId or ``None``.

        Requires:
            Bundled account mapping data.

        Raises:
            Propagates mapping data load errors.

        Example:
            >>> AccountMapper().korToSnakeId("__missing__") is None
            True
        """
        from dartlab.core.accounts import AccountNormalizer

        return AccountNormalizer.get().normalize("", korName)

    def snakeIdToKor(self, snakeId: str) -> str | None:
        """snakeId → 한국어 계정명.

        Args:
            snakeId: Canonical account snakeId.

        Returns:
            Korean account name or ``None``.

        Requires:
            Bundled standard account data.

        Raises:
            Propagates mapping data load errors.

        Example:
            >>> AccountMapper().snakeIdToKor("__missing__") is None
            True
        """
        info = self._standardAccounts().get(snakeId)
        return info.get("korName") if info else None
