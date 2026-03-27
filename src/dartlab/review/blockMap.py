"""BlockMap -- 블록 사전의 사용자 친화 래퍼.

영문 key, 한글 label 모두로 접근 가능.
오타 시 유사 블록 제안. Jupyter tab-complete 지원.
찍으면 카탈로그 테이블 출력.

사용법::

    b = blocks(c)
    b["매출 성장률"]          # 한글 label로 접근
    b["growth"]              # 영문 key로 접근
    b.growth                 # attribute 접근 (tab-complete)
    b                        # 카탈로그 테이블 출력
"""

from __future__ import annotations


class BlockMap:
    """dict-like 블록 사전 -- 한글 label 접근 + tab-complete + pretty repr."""

    __slots__ = ("_data", "_labelToKey")

    def __init__(self, data: dict[str, list]):
        self._data = data
        from dartlab.review.catalog import _LABEL_TO_KEY

        self._labelToKey = _LABEL_TO_KEY

    # ── dict 프로토콜 ──

    def __getitem__(self, keyOrLabel: str) -> list:
        """영문 key 또는 한글 label로 블록 접근."""
        if keyOrLabel in self._data:
            return self._data[keyOrLabel]
        mapped = self._labelToKey.get(keyOrLabel)
        if mapped and mapped in self._data:
            return self._data[mapped]
        from dartlab.review.catalog import _suggest

        raise KeyError(f"'{keyOrLabel}' 블록을 찾을 수 없습니다{_suggest(keyOrLabel)}")

    def __contains__(self, keyOrLabel: str) -> bool:
        if keyOrLabel in self._data:
            return True
        mapped = self._labelToKey.get(keyOrLabel)
        return mapped is not None and mapped in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get(self, keyOrLabel: str, default=None):
        """영문 key 또는 한글 label로 블록 조회."""
        if keyOrLabel in self._data:
            return self._data[keyOrLabel]
        mapped = self._labelToKey.get(keyOrLabel)
        if mapped and mapped in self._data:
            return self._data[mapped]
        return default

    # ── attribute 접근 (tab-complete) ──

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._data:
            return self._data[name]
        from dartlab.review.catalog import _suggest

        raise AttributeError(
            f"'{name}' 블록을 찾을 수 없습니다{_suggest(name)}"
        )

    def __dir__(self):
        return list(self._data.keys()) + list(super().__dir__())

    def _ipython_key_completions_(self):
        """Jupyter에서 b["<TAB>"] 시 한글 label 포함 전체 키 제안."""
        return list(self._data.keys()) + list(self._labelToKey.keys())

    # ── 표시 ──

    def __repr__(self) -> str:
        from dartlab.review.catalog import getBlockMeta, listSections

        lines = []
        sectionKeys = {s.key for s in listSections()}
        bySection: dict[str, list[str]] = {}
        for key in self._data:
            meta = getBlockMeta(key)
            sec = meta.section if meta else "기타"
            bySection.setdefault(sec, []).append(key)

        for sec in listSections():
            blockKeys = bySection.get(sec.key, [])
            if not blockKeys:
                continue
            lines.append(f"\n  [{sec.key}] {sec.title}")
            for key in blockKeys:
                meta = getBlockMeta(key)
                label = meta.label if meta else key
                hasData = bool(self._data.get(key))
                marker = "  " if hasData else "x "
                lines.append(f"    {marker}{key:25s} {label}")

        header = f"BlockMap ({len(self._data)} blocks)"
        return header + "".join(lines) + "\n"

    def _repr_html_(self) -> str:
        """Jupyter HTML 렌더링."""
        from dartlab.review.catalog import getBlockMeta, listSections

        rows = []
        for sec in listSections():
            rows.append(
                f'<tr><td colspan="3" style="font-weight:bold;'
                f'padding-top:8px">{sec.key} -- {sec.title}</td></tr>'
            )
            for key in self._data:
                meta = getBlockMeta(key)
                if not meta or meta.section != sec.key:
                    continue
                hasData = bool(self._data.get(key))
                color = "#333" if hasData else "#ccc"
                rows.append(
                    f"<tr style='color:{color}'>"
                    f"<td><code>{key}</code></td>"
                    f"<td>{meta.label}</td>"
                    f"<td>{meta.description}</td></tr>"
                )

        return (
            "<table style='font-size:13px;border-collapse:collapse'>"
            "<thead><tr><th>key</th><th>label</th><th>description</th></tr></thead>"
            "<tbody>" + "".join(rows) + "</tbody></table>"
        )
