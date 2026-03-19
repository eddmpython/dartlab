"""dartlab 빠른 확인 스크립트.

sections / show / trace / diff / 재무제표 / 비율을 한번에 확인한다.
실행: uv run python main.py
"""

import dartlab


def main():
    # 삼성전자
    c = dartlab.Company("005930")
    print(f"=== {c.corpName} ===\n")

    # sections: 회사 전체 맵 (topic × period)
    print("── sections ──")
    print(c.sections)
    print(f"topics: {len(c.topics)}개\n")

    # show: topic 열기
    print("── show('BS') ──")
    print(c.show("BS"))

    print("\n── show('companyOverview') ──")
    print(c.show("companyOverview"))

    # trace: 출처 확인
    print("\n── trace('BS') ──")
    print(c.trace("BS"))

    # diff: 텍스트 변화
    print("\n── diff() ──")
    print(c.diff())

    # 재무제표 바로가기
    print("\n── BS ──")
    print(c.BS)

    # 비율
    print("\n── ratios ──")
    print(c.ratios)

    # insights
    print("\n── insights ──")
    ins = c.insights
    if ins is not None:
        print(ins.grades())


if __name__ == "__main__":
    main()
