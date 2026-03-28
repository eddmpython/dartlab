"""scan Super Tool -- 전종목 횡단분석 dispatcher.

dartlab.scan() 공개 API 13축과 1:1 대응.
market.py를 대체한다 (scan 관련 action만 흡수).
"""

from __future__ import annotations

from typing import Callable

from ..defaults.helpers import df_to_md, format_tool_value


def registerScanTool(registerTool: Callable) -> None:
    """scan Super Tool 등록."""

    def _runAxis(axis: str, code: str = "", target: str = "", **_kw) -> str:
        """scan registry 기반 동적 축 실행."""
        try:
            import dartlab

            result = dartlab.scan(axis, target or None)
            if result is None:
                return f"[데이터 없음] scan('{axis}') 결과 없음."

            # dict (network 등)
            if isinstance(result, dict):
                return format_tool_value(result, max_rows=30, max_chars=4000)

            # DataFrame
            if code and hasattr(result, "filter"):
                codes = [c.strip() for c in code.split(",")]
                filtered = result.filter(result["stockCode"].is_in(codes))
                if len(filtered) == 0:
                    return f"[데이터 없음] {code}의 scan('{axis}') 결과 없음."
                return df_to_md(filtered, max_rows=30, max_chars=4000)

            return df_to_md(result, max_rows=30, max_chars=4000)
        except ValueError as e:
            return f"[오류] {e}"
        except (ImportError, AttributeError, KeyError, TypeError, FileNotFoundError, OSError) as e:
            return f"[오류] scan('{axis}') 실패: {e}"

    def _positioning(code: str = "", **_kw) -> str:
        """종목 시장 포지셔닝 조회 (ratio 기반 경량 판정)."""
        if not code:
            return "code(종목코드)를 지정하세요."
        try:
            import dartlab

            c = dartlab.Company(code)
            from dartlab.ai.context.company_adapter import get_headline_ratios

            r = get_headline_ratios(c)
            if r is None:
                return f"[데이터 없음] {code} 재무비율 계산 불가."
            lines = [f"## {getattr(c, 'corpName', code)} 시장 포지셔닝"]

            try:
                from dartlab.scan.rank import getRank

                rank = getRank(code)
                if rank is not None:
                    pctile = getattr(rank, "percentile", None)
                    if pctile is not None:
                        lines.append(f"- 시총순위: 상위 {pctile:.0f}%")
            except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError):
                pass

            if r.roe is not None:
                lines.append(f"- ROE: {r.roe:.1f}%")
            if r.debtRatio is not None:
                lines.append(f"- 부채비율: {r.debtRatio:.1f}%")
            if r.currentRatio is not None:
                lines.append(f"- 유동비율: {r.currentRatio:.1f}%")
            pf = getattr(r, "piotroskiFScore", None)
            if pf is not None:
                lines.append(f"- Piotroski F-Score: {pf}/9")
            az = getattr(r, "altmanZScore", None)
            if az is not None:
                zone = "안전" if az > 2.99 else ("회색" if az >= 1.81 else "부실위험")
                lines.append(f"- Altman Z-Score: {az:.2f} ({zone})")
            if r.fcf is not None:
                from dartlab.ai.context.formatting import _format_won

                lines.append(f"- FCF: {_format_won(r.fcf)}")
            return "\n".join(lines)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 포지셔닝 조회 실패: {e}"

    # ── action 빌드: scan._AXIS_REGISTRY에서 동적 생성 ──

    from dartlab.scan import _AXIS_REGISTRY as _scanRegistry

    _SCAN_AXES = list(_scanRegistry.keys())
    _AXIS_LABELS = {k: v.label for k, v in _scanRegistry.items()}

    _ACTIONS: dict[str, object] = {}
    for axis in _SCAN_AXES:
        _ACTIONS[axis] = lambda code="", target="", _a=axis, **_kw: _runAxis(_a, code, target, **_kw)
    _ACTIONS["positioning"] = _positioning

    def scan(action: str, code: str = "", target: str = "") -> str:
        """전종목 횡단분석 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(code=code, target=target)

    # action enum 설명 빌드
    axisDescs = ", ".join(f"{a}={_AXIS_LABELS[a]}" for a in _SCAN_AXES)
    actionDesc = f"{axisDescs}, positioning=종목포지셔닝"

    registerTool(
        "scan",
        scan,
        "전종목 횡단분석 -- dartlab.scan() 13축 1:1 대응.\n"
        "\n"
        "## scan 축 (전종목 DataFrame 반환)\n"
        "- governance: 지배구조 (지분율, 사외이사, 보수, 감사의견)\n"
        "- workforce: 인력/급여 (직원수, 평균급여, 근속년수)\n"
        "- capital: 주주환원 (배당, 자사주, 증자/감자)\n"
        "- debt: 부채구조 (사채만기, 부채비율, ICR, 위험등급)\n"
        "- cashflow: 현금흐름 (OCF/ICF/FCF + 패턴 분류)\n"
        "- audit: 감사리스크 (감사의견, 감사인변경, 특기사항)\n"
        "- insider: 내부자지분 (최대주주변동, 자기주식, 경영권 안정성)\n"
        "- quality: 이익의 질 (Accrual Ratio, CF/NI)\n"
        "- liquidity: 유동성 (유동비율, 당좌비율)\n"
        "- digest: 전종목 공시 변화 다이제스트\n"
        "- network: 상장사 관계 네트워크 (출자/지분/계열)\n"
        "\n"
        "## 파라미터 필요 축\n"
        "- account: 전종목 단일 계정 시계열. target 필수 (예: sales, operatingIncome)\n"
        "- ratio: 전종목 단일 비율 시계열. target 필수 (예: roe, debtRatio)\n"
        "\n"
        "## 기타\n"
        "- positioning: 종목 포지셔닝 (시총순위+핵심지표). code 필수\n"
        "\n"
        "code: 종목코드 (특정 종목 필터링, 쉼표 구분 복수 가능).\n"
        "target: account/ratio 축에서 계정ID 또는 비율명.\n"
        "기업 비교 패턴: scan(action='account', target='sales', code='005930,000660')\n"
        "\n"
        "반환: 마크다운 텍스트. 실패 시 '[오류]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": _SCAN_AXES + ["positioning"],
                    "description": actionDesc,
                },
                "code": {
                    "type": "string",
                    "description": "종목코드 (예: 005930). 쉼표 구분으로 복수 종목 필터링 가능",
                    "default": "",
                },
                "target": {
                    "type": "string",
                    "description": "account/ratio 축에서 계정ID(snakeId) 또는 비율명(ratioName)",
                    "default": "",
                },
            },
            "required": ["action"],
        },
        category="global",
        questionTypes=("투자", "종합", "지배구조", "리스크"),
        priority=70,
    )
