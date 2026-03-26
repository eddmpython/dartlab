"""AI 지원 플러그인 패키지 자동 생성.

LLM이 사용자 요청에 따라 완전한 플러그인 패키지 구조를 자동 생성한다.
진입장벽 제거 — "ESG 플러그인 만들어줘"로 즉시 시작 가능.
"""

from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent

from dartlab.ai.tools.plugin import tool


def _sanitize_name(name: str) -> str:
    """플러그인 이름을 안전한 형식으로 변환."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:50] if len(s) > 50 else s


def _to_module_name(name: str) -> str:
    """하이픈 이름 → 언더스코어 모듈명."""
    return name.replace("-", "_")


@tool(name="create_plugin", category="system", requires_company=False)
def create_plugin(
    name: str,
    description: str,
    plugin_type: str = "data",
    topic_name: str = "",
    author: str = "community",
) -> str:
    """사용자 요청에 맞는 dartlab 플러그인 패키지를 자동 생성한다.

    name: 플러그인 이름 (예: "esg-scores")
    description: 플러그인 설명 (예: "ESG 등급 및 세부 점수 분석")
    plugin_type: 플러그인 유형 — "data" (Company.show 토픽), "tool" (AI 도구), "engine" (분석 엔진)
    topic_name: data 플러그인의 토픽 이름 (예: "esgScore"). 비어있으면 name에서 자동 생성.
    author: 작성자 이름
    """
    safe_name = _sanitize_name(name)
    if len(safe_name) < 3:
        return f"오류: 플러그인 이름이 너무 짧습니다: '{name}'"

    module_name = _to_module_name(safe_name)
    pkg_dir_name = f"dartlab-plugin-{safe_name}"
    pkg_module = f"dartlab_plugin_{module_name}"

    if not topic_name and plugin_type == "data":
        topic_name = re.sub(r"[-_](.)", lambda m: m.group(1).upper(), safe_name)

    # 출력 디렉토리
    output_dir = Path.cwd() / pkg_dir_name
    if output_dir.exists():
        return f"오류: '{pkg_dir_name}' 디렉토리가 이미 존재합니다."

    src_dir = output_dir / "src" / pkg_module
    src_dir.mkdir(parents=True, exist_ok=True)

    # 1. pyproject.toml
    pyproject_content = dedent(f"""\
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [project]
        name = "{pkg_dir_name}"
        version = "0.1.0"
        description = "{description}"
        requires-python = ">=3.12"
        dependencies = ["dartlab"]

        [project.entry-points."dartlab.plugins"]
        {safe_name} = "{pkg_module}:register"

        [tool.hatch.build.targets.wheel]
        packages = ["src/{pkg_module}"]
    """)
    (output_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # 2. __init__.py (register 함수)
    if plugin_type == "data":
        init_content = _gen_data_init(pkg_module, safe_name, description, topic_name, author)
    elif plugin_type == "tool":
        init_content = _gen_tool_init(pkg_module, safe_name, description, author)
    else:
        init_content = _gen_engine_init(pkg_module, safe_name, description, topic_name, author)

    (src_dir / "__init__.py").write_text(init_content, encoding="utf-8")

    # 3. 로직 파일
    if plugin_type == "data":
        logic_content = _gen_data_logic(topic_name)
        (src_dir / f"{topic_name}.py").write_text(logic_content, encoding="utf-8")
    elif plugin_type == "tool":
        logic_content = _gen_tool_logic()
        (src_dir / "tools.py").write_text(logic_content, encoding="utf-8")
    else:
        logic_content = _gen_engine_logic(topic_name or "analyze")
        (src_dir / "engine.py").write_text(logic_content, encoding="utf-8")

    # 결과 안내
    lines = [
        f"✅ 플러그인 패키지 '{pkg_dir_name}' 생성 완료!",
        "",
        "📁 구조:",
        f"  {pkg_dir_name}/",
        "  ├── pyproject.toml",
        f"  └── src/{pkg_module}/",
        "      ├── __init__.py    (register 함수)",
    ]
    if plugin_type == "data":
        lines.append(f"      └── {topic_name}.py  (데이터 로직)")
    elif plugin_type == "tool":
        lines.append("      └── tools.py        (AI 도구 로직)")
    else:
        lines.append("      └── engine.py       (분석 엔진 로직)")

    lines.extend(
        [
            "",
            "🚀 설치 및 사용:",
            f"  cd {pkg_dir_name}",
            "  uv pip install -e .",
            "",
            "  import dartlab",
        ]
    )
    if plugin_type == "data":
        lines.append(f'  dartlab.Company("005930").show("{topic_name}")')
    lines.extend(
        [
            "  dartlab.plugins()  # 로드된 플러그인 확인",
            "",
            "📝 다음 단계:",
            f"  1. src/{pkg_module}/ 안의 로직 파일을 수정하세요",
            "  2. uv pip install -e . 로 재설치",
            "  3. PyPI 또는 GitHub에 공유!",
        ]
    )

    return "\n".join(lines)


def _gen_data_init(pkg_module: str, name: str, desc: str, topic: str, author: str) -> str:
    return dedent(f'''\
        """dartlab 플러그인 — {desc}."""

        from dartlab.core.plugins import PluginContext, PluginMeta
        from dartlab.core.registry import DataEntry

        _META = PluginMeta(
            name="{name}",
            version="0.1.0",
            author="{author}",
            description="{desc}",
            plugin_type="data",
        )


        def register(ctx: PluginContext) -> None:
            ctx.add_data_entry(
                DataEntry(
                    name="{topic}",
                    label="{desc}",
                    category="plugin",
                    dataType="dataframe",
                    description="{desc}",
                    modulePath="{pkg_module}.{topic}",
                    funcName="{topic}",
                    aiExposed=True,
                    aiHint="{desc}",
                ),
                meta=_META,
            )
    ''')


def _gen_tool_init(pkg_module: str, name: str, desc: str, author: str) -> str:
    return dedent(f'''\
        """dartlab 플러그인 — {desc}."""

        from dartlab.core.plugins import PluginContext, PluginMeta

        _META = PluginMeta(
            name="{name}",
            version="0.1.0",
            author="{author}",
            description="{desc}",
            plugin_type="tool",
        )


        def register(ctx: PluginContext) -> None:
            from {pkg_module}.tools import analyze

            ctx.add_tool(
                analyze,
                meta=_META,
                name="{name.replace("-", "_")}",
                category="plugin",
            )
    ''')


def _gen_engine_init(pkg_module: str, name: str, desc: str, topic: str, author: str) -> str:
    func_name = topic or "analyze"
    return dedent(f'''\
        """dartlab 플러그인 — {desc}."""

        from dartlab.core.plugins import PluginContext, PluginMeta

        _META = PluginMeta(
            name="{name}",
            version="0.1.0",
            author="{author}",
            description="{desc}",
            plugin_type="engine",
        )


        def register(ctx: PluginContext) -> None:
            from {pkg_module}.engine import {func_name}

            ctx.add_engine(
                "{func_name}",
                {func_name},
                meta=_META,
                label="{desc}",
                description="{desc}",
            )
    ''')


def _gen_data_logic(topic: str) -> str:
    return dedent(f'''\
        """데이터 모듈 — Company.show("{topic}")에서 호출됨."""

        from __future__ import annotations


        def {topic}(stockCode: str, **kwargs) -> dict | None:
            """TODO: 여기에 데이터 로직을 구현하세요.

            Args:
                stockCode: 종목코드.

            Returns:
                dict, DataFrame, 또는 None.
            """
            return {{"stockCode": stockCode, "message": "구현 필요"}}
    ''')


def _gen_tool_logic() -> str:
    return dedent('''\
        """AI 도구 — LLM이 호출하는 함수."""

        from __future__ import annotations


        def analyze(query: str) -> str:
            """TODO: 여기에 분석 로직을 구현하세요.

            Args:
                query: 사용자 질문.

            Returns:
                분석 결과 텍스트.
            """
            return f"분석 결과: {query}"
    ''')


def _gen_engine_logic(func_name: str) -> str:
    return dedent(f'''\
        """분석 엔진 — L2 레벨 분석 모듈."""

        from __future__ import annotations


        def {func_name}(stockCode: str, **kwargs) -> dict | None:
            """TODO: 여기에 분석 로직을 구현하세요.

            Args:
                stockCode: 종목코드.

            Returns:
                분석 결과 dict 또는 None.
            """
            return {{"stockCode": stockCode, "score": 0}}
    ''')
