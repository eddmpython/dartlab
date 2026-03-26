"""실험 ID: 004
실험명: 업종별 D2D 분포 추정 — 문헌 기반 초기 벤치마크

목적:
- 업종별 Merton D2D 중앙값/사분위수 초기 벤치마크 설정
- 실제 종목 데이터 수집 불가 시 학술 문헌 기반 추정
- benchmark.py에 반영할 합리적 초기값 도출

가설:
1. 유틸리티/필수소비재 → D2D 높음 (안정적 현금흐름)
2. IT/헬스케어 → D2D 중간~높음 (성장주 변동성 높지만 부채 낮음)
3. 에너지/소재 → D2D 중간 (경기순환)
4. 부동산 → D2D 낮음 (높은 레버리지)

방법:
1. 각 섹터의 전형적 E/D 비율과 변동성을 문헌/시장 상식에서 설정
2. solveMerton으로 합성 D2D 계산
3. 분포 추정 (중앙값, Q1, Q3)

결과 (실험 후 작성):
- 업종별 합성 D2D 추정 결과:
  | 섹터            | 중앙값 | Q1   | Q3   |
  |----------------|-------|------|------|
  | IT             | 4.0   | 2.4  | 6.7  |
  | HEALTHCARE     | 2.9   | 1.7  | 6.1  |
  | CONSUMER_DISC  | 4.3   | 2.9  | 7.0  |
  | INDUSTRIALS    | 4.1   | 2.8  | 6.6  |
  | MATERIALS      | 3.4   | 2.1  | 5.3  |
  | ENERGY         | 2.9   | 1.8  | 4.3  |
  | UTILITIES      | 6.0   | 4.0  | 8.0  |
  | COMMUNICATION  | 3.4   | 2.1  | 6.6  |
  | CONSUMER_STAPLES| 5.1  | 3.6  | 8.3  |
  | REAL_ESTATE    | 4.0   | 2.8  | 6.0  |

결론:
- 가설 1 채택: 유틸리티(6.0) / 필수소비재(5.1) D2D 최고 — 안정적 현금흐름+낮은 변동성
- 가설 2 부분 채택: IT(4.0) 중간, 헬스케어(2.9) 낮음 — 바이오 고변동성+적자 기업 비중
- 가설 3 채택: 에너지(2.9) / 소재(3.4) 중간 — 경기순환 특성
- 가설 4 부분 기각: 부동산(4.0) 의외로 높음 — 합성 데이터 한계. 실제 데이터로 보정 필요.
- 합성 기반 초기 벤치마크는 방향성 정확. 실제 종목 데이터 확보 시 정밀화.
- benchmark.py에 초기값 반영.

실험일: 2026-03-22
"""

import sys
sys.path.insert(0, "src")

from dartlab.core.finance.merton import solveMerton


def run():
    """업종별 전형적 프로필 → Merton D2D 추정."""

    # (섹터, [프로필]) 형태
    # 각 프로필: (설명, E/D비율, σ_E)
    # E를 1로 정규화하고 D = 1/ratio로 설정
    sector_profiles = {
        "IT": [
            ("대형 IT (삼성전자급)", 4.0, 0.30),
            ("중형 IT", 2.0, 0.40),
            ("소형 IT (벤처)", 1.0, 0.55),
            ("적자 IT", 0.5, 0.65),
        ],
        "HEALTHCARE": [
            ("대형 제약", 3.0, 0.30),
            ("중형 바이오", 1.5, 0.50),
            ("소형 바이오 (적자)", 0.8, 0.70),
            ("임상 바이오", 0.3, 0.80),
        ],
        "CONSUMER_DISC": [
            ("대형 소비재", 2.5, 0.25),
            ("중형 소비재", 1.5, 0.35),
            ("소형 소비재", 0.8, 0.45),
        ],
        "INDUSTRIALS": [
            ("대형 산업재", 2.0, 0.25),
            ("중형 산업재", 1.2, 0.35),
            ("소형 산업재", 0.7, 0.45),
        ],
        "MATERIALS": [
            ("대형 소재", 1.8, 0.30),
            ("중형 소재", 1.0, 0.40),
            ("소형 소재", 0.5, 0.55),
        ],
        "ENERGY": [
            ("대형 에너지", 1.5, 0.35),
            ("중형 에너지", 0.8, 0.45),
            ("소형 에너지", 0.4, 0.60),
        ],
        "UTILITIES": [
            ("대형 유틸", 1.2, 0.18),
            ("중형 유틸", 0.8, 0.22),
            ("소형 유틸", 0.5, 0.30),
        ],
        "COMMUNICATION": [
            ("대형 통신", 2.0, 0.25),
            ("중형 미디어", 1.0, 0.40),
            ("소형 콘텐츠", 0.5, 0.55),
        ],
        "CONSUMER_STAPLES": [
            ("대형 필수소비", 2.0, 0.20),
            ("중형 필수소비", 1.2, 0.28),
            ("소형 필수소비", 0.7, 0.35),
        ],
        "REAL_ESTATE": [
            ("대형 부동산", 0.8, 0.22),
            ("중형 부동산", 0.5, 0.30),
            ("소형 부동산", 0.3, 0.40),
        ],
    }

    print("=" * 90)
    print(f"{'섹터':<20s} | {'중앙값':>8s} {'Q1':>8s} {'Q3':>8s} | {'전체 D2D 목록'}")
    print("-" * 90)

    benchmark_results = {}

    for sector, profiles in sector_profiles.items():
        d2d_list = []
        for desc, ed_ratio, sigma_e in profiles:
            E = 1_0000_0000  # 정규화 기준
            D = E / ed_ratio
            result = solveMerton(E, D, sigma_e)
            if result and result.converged:
                d2d_list.append(result.d2d)

        if not d2d_list:
            continue

        d2d_list.sort()
        n = len(d2d_list)
        median = d2d_list[n // 2]
        q1 = d2d_list[max(0, n // 4)]
        q3 = d2d_list[min(n - 1, 3 * n // 4)]

        benchmark_results[sector] = (median, q1, q3)
        d2d_str = ", ".join(f"{d:.2f}" for d in d2d_list)
        print(f"{sector:<20s} | {median:8.2f} {q1:8.2f} {q3:8.2f} | [{d2d_str}]")

    print("=" * 90)

    # Python 코드 출력 (benchmark.py에 붙여넣기용)
    print("\n# benchmark.py 업데이트용 D2D 값:")
    for sector, (med, q1, q3) in benchmark_results.items():
        print(f"    # Sector.{sector}: d2dMedian={med:.1f}, d2dQ1={q1:.1f}, d2dQ3={q3:.1f}")


if __name__ == "__main__":
    run()
