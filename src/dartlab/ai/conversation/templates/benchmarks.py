"""업종별 벤치마크 렌더링 + KRX 업종명 매핑.

데이터는 benchmarkData.py (BENCHMARK_DATA dict)에 분리.
이 모듈은 렌더링만 담당한다.
"""

from __future__ import annotations

from .benchmarkData import BENCHMARK_DATA


def render_benchmark(key: str) -> str:
    """BENCHMARK_DATA[key] → 프롬프트용 마크다운 텍스트 변환."""
    data = BENCHMARK_DATA.get(key)
    if data is None:
        return ""

    display_name = key
    lines: list[str] = [f"\n## {display_name} 업종 벤치마크"]

    # 지표 테이블
    metrics = data.get("지표", {})
    if metrics:
        lines.append("| 지표 | 우수 | 보통 | 주의 |")
        lines.append("|------|------|------|------|")
        for name, spec in metrics.items():
            unit = spec.get("unit", "")
            inverted = spec.get("invert", False)
            note = spec.get("note", "")
            good = spec["good"]
            low = spec["normal_low"]
            high = spec["normal_high"]

            if inverted:
                good_str = f"< {good}{unit}"
                normal_str = f"{low}-{high}{unit}"
                bad_str = f"> {high}{unit}"
            else:
                good_str = f"> {good}{unit}"
                normal_str = f"{low}-{high}{unit}"
                bad_str = f"< {low}{unit}"
                if note:
                    bad_str += f" 또는 {note}"

            lines.append(f"| {name} | {good_str} | {normal_str} | {bad_str} |")
        lines.append("")

    # 분석 포인트
    points = data.get("분석포인트", [])
    if points:
        lines.append(f"### {display_name} 핵심 분석 포인트")
        for p in points:
            lines.append(f"- {p}")

    # 회계 함정
    traps = data.get("회계함정", [])
    if traps:
        trap_label = "회계 함정" if len(traps) > 1 else "회계 함정"
        lines.append(f"- **{trap_label}**: {traps[0]}")
        for t in traps[1:]:
            lines.append(f"- **회계 함정**: {t}")

    # topic 확인
    topics = data.get("topic확인", [])
    if topics:
        lines.append(f"- **topic 확인**: {', '.join(topics)}")

    return "\n".join(lines) + "\n"


# 렌더링 캐시 — 기존 코드 호환용
_INDUSTRY_BENCHMARKS: dict[str, str] = {key: render_benchmark(key) for key in BENCHMARK_DATA}


# KRX 업종명 → 벤치마크 키 매핑
_SECTOR_MAP: dict[str, str] = {
    "반도체": "반도체",
    "반도체와반도체장비": "반도체",
    "디스플레이": "반도체",
    "제약": "제약/바이오",
    "바이오": "제약/바이오",
    "의약품": "제약/바이오",
    "생물공학": "제약/바이오",
    "건강관리장비와용품": "제약/바이오",
    "은행": "금융/은행",
    "시중은행": "금융/은행",
    "지방은행": "금융/은행",
    "보험": "금융/보험",
    "생명보험": "금융/보험",
    "손해보험": "금융/보험",
    "증권": "금융/증권",
    "투자증권": "금융/증권",
    "자본시장": "금융/증권",
    "자동차": "자동차",
    "자동차부품": "자동차",
    "화학": "화학",
    "석유화학": "화학",
    "정유": "화학",
    "철강": "철강",
    "비철금속": "철강",
    "금속": "철강",
    "건설": "건설",
    "건설업": "건설",
    "주택건설": "건설",
    "유통": "유통",
    "백화점": "유통",
    "대형마트": "유통",
    "편의점": "유통",
    "소프트웨어": "IT/소프트웨어",
    "IT서비스": "IT/소프트웨어",
    "인터넷": "IT/소프트웨어",
    "게임": "IT/소프트웨어",
    "통신": "통신",
    "무선통신": "통신",
    "유선통신": "통신",
    "전력": "전력/에너지",
    "에너지": "전력/에너지",
    "가스": "전력/에너지",
    "식품": "식품",
    "음료": "식품",
    "식료품": "식품",
    "섬유": "섬유/의류",
    "의류": "섬유/의류",
    "패션": "섬유/의류",
}
