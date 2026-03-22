"""dartlab 플러그인 예제.

설치::

    cd examples/dartlab-plugin-example
    uv pip install -e .

사용::

    import dartlab
    c = dartlab.Company("005930")
    c.show("customScore")       # 커스텀 점수
    dartlab.plugins()            # [PluginMeta(name="example-score", ...)]
"""

from dartlab.core.plugins import PluginContext, PluginMeta
from dartlab.core.registry import DataEntry

_META = PluginMeta(
    name="example-score",
    version="0.1.0",
    author="dartlab-team",
    description="예제 커스텀 점수 플러그인",
    plugin_type="data",
    stability="experimental",
)


def register(ctx: PluginContext) -> None:
    """dartlab 플러그인 등록 — entry_point에서 자동 호출됨."""
    ctx.add_data_entry(
        DataEntry(
            name="customScore",
            label="커스텀점수",
            category="plugin",
            dataType="dataframe",
            description="예제 커스텀 분석 점수 (수익성 + 안정성 종합).",
            modulePath="dartlab_plugin_example.score",
            funcName="customScore",
            aiExposed=True,
            aiHint="커스텀 종합 점수, 수익성/안정성 가중합",
        ),
        meta=_META,
    )
