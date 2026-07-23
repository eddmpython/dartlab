---
title: "양자컴퓨터는 왜 큐비트 수보다 오류의 사다리가 중요한가"
date: "2026-07-22"
description: "양자컴퓨터의 중첩과 오류정정부터 클라우드, QPU, 제어·냉각·광학 공급망, 네트워크 장비와 PQC 전환까지 쉽게 연결하고 실제 거래 단계를 판정한다."
category: tech-story
series: tech-story
seriesOrder: 17
topicSlug: "quantum-computing-evidence-ladder"
tags:
  - 양자컴퓨터
  - 큐비트
  - 양자오류정정
  - 논리큐비트
  - 이온트랩
  - 초전도
  - 양자어닐링
  - 양자내성암호
  - PQC
  - QKD
  - IONQ
  - QBTS
  - RGTI
  - QNT
  - DART
  - EDGAR
  - 기술이야기
ogImage: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/49/499fc0d56f3c4c6b8ef190ab5c36130ce61ef338a8cfa500314ee0dbe87b43de.webp
cardPreview: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/bc/bcc7d3c3450ccdd9a1770bc494da0c0f73a68a5a275b72a275f854c149beccd4.webp
thumbnailBg: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/7b/7b2e56bc68d2cb9e3cfdc5358fd7bbba90ffd409bd4b0ba97357336c91c13dd9.png
ai:
  verdict: "양자 산업은 큐비트 수 한 줄로 순위를 매길 수 없다. 물리 큐비트의 방식과 오류율, 논리 큐비트, 유용한 작업, 고객 주문, 매출과 현금이 서로 다른 증거 단계다. 지금 가장 분명한 변화는 정부가 연구비를 넘어 제조 병목에 자금을 대기 시작했고, 일부 장비 주문과 PQC 전환이 실제 계약 단계로 내려왔다는 점이다."
  direction: 관망
  confidence: 높음
  archetype: 산업네트워크
  dataAsOf: "2026-07-22"
---

![초전도 냉동기, 이온트랩 광학계, 고성능컴퓨팅 센터가 서로 다른 구역에서 연결된 양자컴퓨팅 산업 장면](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/7b/7b2e56bc68d2cb9e3cfdc5358fd7bbba90ffd409bd4b0ba97357336c91c13dd9.png)

2026년 7월, 양자컴퓨팅 관련주는 같은 날 함께 오르기도 한다. IonQ, D-Wave, Rigetti, Quantum Computing Inc., 새로 상장한 Quantinuum을 한 바구니로 보는 시장의 습관 때문이다. 미국 정부의 대규모 지원 의향서, 실제 장비 주문, Quantinuum의 기업공개, 양자내성암호 전환까지 호재도 많다.

그런데 이 회사들은 같은 경주를 하지 않는다. D-Wave의 수천 큐비트 어닐러와 Rigetti의 108큐비트 게이트형 시스템을 숫자만 놓고 비교하면 자동차 엔진의 실린더 수와 화물선의 컨테이너 수를 비교하는 꼴이다. IonQ와 Quantinuum은 원자를 이온으로 가둔다. Rigetti, IBM, Google은 초전도 회로를 극저온에 둔다. QUBT는 광자와 박막 리튬나이오베이트 파운드리에 무게를 둔다. 국내 관련주는 대부분 양자컴퓨터를 만들지 않고 기존 통신망의 암호를 바꾸거나 양자키를 전달한다.

이 글의 질문은 “어느 종목이 대장인가”가 아니다. **한 회사의 발표가 멋진 실험인지, 쓸 수 있는 기계인지, 반복 매출로 내려온 사업인지 어떻게 구분할까?** 답은 `물리 큐비트 → 오류 억제 → 논리 큐비트 → 유용한 작업 → 주문 → 설치 → 매출 → 현금`이라는 증거 사다리에 있다.

## 1. 양자컴퓨터는 모든 답을 한꺼번에 계산하는 기계가 아니다

먼저 가장 유명한 오해부터 걷어내자. 일반 비트는 0 또는 1이다. 큐비트는 측정하기 전까지 0과 1의 **중첩**으로 표현할 수 있다. 그렇다고 가능한 답을 모두 계산한 뒤 정답만 꺼내 주는 것은 아니다. 측정하면 한 결과만 나온다.

양자 알고리즘의 핵심은 중첩보다 **간섭**이다. 물결 두 개가 만나면 봉우리가 더 커지거나 서로 지워진다. 양자 회로는 원하는 답으로 이어지는 확률 진폭은 보강하고, 틀린 답으로 이어지는 진폭은 상쇄하도록 연산 순서를 설계한다. 마지막 측정을 여러 번 반복하면 보강된 결과가 통계적으로 더 자주 나타난다.

중첩, 얽힘, 간섭은 각각 다른 역할을 한다. 중첩은 계산 상태를 넓힌다. 얽힘은 큐비트들을 고전적으로 흉내 내기 어려운 상관관계로 묶는다. 간섭은 그 넓은 상태 공간에서 쓸모 있는 패턴을 남긴다. 그래서 큐비트가 많다는 사실만으로는 부족하다. 큐비트를 원하는 대로 연결하고, 충분히 정확한 게이트를 여러 번 실행하며, 끝까지 상태를 보존해야 한다.

![중첩을 만들고 얽힘으로 상태를 연결한 뒤 간섭과 측정으로 답의 분포를 얻는 양자회로 흐름](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/81/81b5031f5f810f3dcfb58c8289c2c62c75aefb6b7efd1b99410ea66e6ecfc2b9.svg)

여기서 고전컴퓨터가 사라지는 것도 아니다. 문제를 준비하고, 양자 회로를 편성하고, 오류 신호를 해독하고, 수천 번 측정한 결과를 모으는 일은 CPU와 GPU가 맡는다. 양자처리장치인 QPU는 범용 노트북의 대체재보다 특정 계산을 맡는 가속기에 가깝다. [GPU 전력이 칩 안으로 들어가는 과정](/blog/backside-power-delivery-network)처럼, 양자컴퓨터도 물리 장치 하나보다 주변 제어와 데이터 이동까지 보아야 시스템이 보인다.

## 2. 큐비트는 늘릴수록 왜 더 쓸모없어질 수 있나

큐비트는 환경과 상호작용하면 양자 상태를 잃는다. 이를 결맞음이 깨진다는 뜻의 **디코히런스**라고 한다. 제어 펄스가 조금 틀리거나, 이웃 큐비트가 간섭하거나, 측정이 잘못돼도 오류가 난다. 일반 컴퓨터는 비트를 복사해 다수결을 하면 되지만 미지의 양자 상태는 마음대로 복제할 수 없다.

양자오류정정은 상태 자체를 복사하지 않는다. 여러 물리 큐비트에 하나의 정보가 퍼지도록 부호화하고, 정보값을 직접 읽지 않은 채 오류의 흔적인 **신드롬**만 반복 측정한다. 고전 디코더가 어느 위치에서 어떤 오류가 났는지 추정한 뒤 다음 연산을 보정한다. 이렇게 보호된 계산 단위가 논리 큐비트다.

![수많은 물리 제어 노드가 오류를 감지하며 하나의 안정된 논리 영역을 보호하는 개념 장면](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/8e/8eae4bbf6fa21113c4fb67838c720b6ac95714018ab289c1f4d12a07cc22a392.png)

중요한 것은 물리 큐비트를 더 붙였을 때 논리 오류율이 실제로 내려가느냐다. 물리 오류율이 임계값보다 높으면 보호용 큐비트를 추가할수록 오류 지점도 늘어난다. 임계값 아래로 내려가면 코드의 거리를 키울수록 논리 오류가 줄어드는 방향으로 바뀐다. Google은 Willow에서 표면부호의 크기를 키울수록 오류가 억제되는 이른바 below-threshold 결과를 발표했다. 하지만 이것도 실용 알고리즘을 장시간 실행하는 완성 기계와 같지는 않다.

![물리 오류율이 임계값 위일 때와 아래일 때 코드 거리에 따라 논리 오류가 달라지는 구조](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/6d/6dc7c73679ade134d02e95890c097bcfd43a5eebc6532c4f98013e1ba23c326c.svg)

그래서 앞으로는 물리 큐비트 수보다 다음 질문이 중요해진다.

1. 동시에 동작할 때의 1큐비트와 2큐비트 게이트 오류율은 얼마인가?
2. 회로가 깊어져도 성능이 유지되는가?
3. 논리 큐비트를 만들었을 때 물리 큐비트보다 실제로 더 정확한가?
4. 오류 신드롬을 실시간으로 읽고 보정할 수 있는가?
5. 논리 게이트를 몇 번 연속 실행할 수 있는가?

IBM도 2026년 성능 지표를 설명하면서 장기적으로 프로그래머블 큐비트와 논리 큐비트, 그리고 오류정정에서 비용이 큰 T 게이트 수가 더 중요해질 것이라고 적었다. 단순 큐비트 수 경쟁이 회로의 깊이와 유효 연산 경쟁으로 이동하는 이유다.

## 3. 초전도, 이온트랩, 광자, 어닐링은 같은 경주가 아니다

양자 상태를 무엇으로 만들 것인지에 따라 기계 전체가 달라진다. 어느 방식도 모든 항목에서 우월하지 않다.

| 방식 | 큐비트의 실체 | 강점 | 핵심 병목 | 대표 회사 |
|---|---|---|---|---|
| 초전도 게이트 | 칩 위의 인공 원자 회로 | 게이트가 빠르고 반도체 공정 경험을 활용하기 좋음 | 극저온 배선, 칩 균일도, 누설과 교차간섭 | IBM, Google, Rigetti |
| 이온트랩 | 전자기장에 가둔 원자 이온 | 높은 정확도와 좋은 연결성 | 레이저와 광학계 복잡도, 게이트 속도, 모듈 연결 | IonQ, Quantinuum |
| 중성원자 | 레이저로 배열한 원자 | 많은 원자를 재배열하기 좋음 | 정밀 광학, 원자 손실, 오류정정 통합 | Atom Computing, Infleqtion, QuEra |
| 광자 | 광원과 도파로 속의 빛 입자 | 실온 부품과 통신 파장, 네트워크에 유리 | 광자 손실, 단일광자원과 검출기, 패키징 | PsiQuantum, Xanadu, QUBT 인접 영역 |
| 양자 어닐링 | 초전도 플럭스 큐비트의 에너지 지형 | 최적화 문제를 직접 표현하고 현재 대형 시스템 제공 | 문제 임베딩, 고전 알고리즘 대비 우위의 범위 | D-Wave |

초전도 방식은 전자레인지 펄스로 빠르게 게이트를 실행하지만 10밀리켈빈 안팎의 냉동기와 수많은 동축선이 필요하다. 이온트랩은 같은 종류의 원자를 쓰므로 큐비트 편차가 작고 이온을 이동시켜 연결할 수 있지만, 레이저 빔과 광학 부품이 늘어나면 정렬과 제어가 복잡해진다. 광자는 멀리 보내기 좋지만 손실된 광자를 되돌릴 수 없다.

D-Wave의 어닐링은 문제를 에너지가 낮아지는 지형으로 바꿔 최저점을 찾는다. 게이트형 컴퓨터처럼 임의의 양자 회로를 차례로 실행하는 방식과 목적이 다르다. 따라서 Advantage2의 큐비트 수를 Rigetti Cepheus의 108큐비트와 나란히 놓고 “누가 더 크다”고 말하면 안 된다. D-Wave는 2026년 Quantum Circuits 인수 뒤 게이트형 시스템도 병행하고 있지만, 현재 매출과 고객 기반의 중심은 여전히 어닐링과 하이브리드 최적화다.

![초전도, 이온트랩, 중성원자, 광자, 양자 어닐링의 강점과 병목 비교](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/df/df87f893e8fe2f819bf1a938d6ea3a14428684c140cbc0dbb6c51422b571c15e.svg)

이 차이는 회사의 공급망도 바꾼다. 초전도에는 양자급 웨이퍼, 극저온 냉동기, 저잡음 증폭기, 고밀도 배선과 패키징이 필요하다. 이온트랩에는 진공 챔버, 레이저, 광학 변조기와 집적광학이 필요하다. 광자에는 단일광자원, 검출기, 초저손실 도파로와 패키징이 필요하다. [모래에서 반도체까지 이어지는 제조 사슬](/blog/sand-to-semiconductor)과 [실리콘 포토닉스와 광패키징의 병목](/blog/co-packaged-optics-silicon-photonics)이 양자 분야에도 다시 등장하는 이유다.

## 4. 정부의 20억 달러는 무엇을 사려는 돈인가

2026년 5월 미국 상무부는 CHIPS법 연구개발 재원으로 9개 회사에 총 20억1,300만 달러의 지원 의향서를 체결했다고 발표했다. 중요한 단어는 **의향서**와 **계획 자금**이다. 이미 모두 지급된 확정 지분투자라고 쓰면 한 단계 과장이다. 다만 연구 논문이 아니라 제조 병목과 국내 공급망을 직접 겨냥했고, 정부가 조건으로 소수 비지배 지분을 받는다는 점은 분명한 변화다.

가장 큰 10억 달러는 IBM의 양자급 초전도 웨이퍼 파운드리 자회사 계획에 배정됐다. GlobalFoundries에는 여러 방식의 양자칩을 지원하는 국내 파운드리 구축 명목으로 3억7,500만 달러가 계획됐다. D-Wave, Quantinuum, Atom Computing, Infleqtion, PsiQuantum에는 각각 1억 달러, Rigetti에는 최대 1억 달러, Diraq에는 최대 3,800만 달러가 제시됐다.

지원 사유를 읽으면 산업의 진짜 병목이 보인다. NIST 원문은 소자 재현성, 광학계 복잡도, 오류율, 극저온 시스템 통합, 제어 하드웨어, 초고속 판독 전자장치, 광자 손실, 인터커넥트와 패키징을 적었다. 정부는 “큐비트 숫자를 늘려라”보다 **같은 성능의 소자를 반복 생산하고, 읽고, 연결하고, 냉각하라**에 돈을 대고 있다.

![양자칩에서 냉각과 광학, 제어, 오류정정, HPC, 응용으로 이어지는 산업 스택](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/3a/3ac0d8591a8b540fa6113a741312f57e1e609ca350bf9029f3264093a95c0ffd.svg)

2026년 6월 미국 행정명령은 과학적 응용과 발견을 위한 QC-ADDS 국가 노력을 만들고 에너지부 시설에 과학용 양자컴퓨터를 배치하는 방향을 제시했다. DARPA의 Quantum Benchmarking Initiative는 한술 더 떠서 2033년까지 계산 가치가 비용을 넘는 utility-scale 시스템이 가능한지 독립 검증하려 한다. 정부 지원은 호재지만 동시에 회사 로드맵을 외부 검증대에 올리는 장치다.

프랑스의 10억 유로도 날짜를 바로 읽어야 한다. 이는 2026년 하루에 새로 생긴 단일 예산이 아니라 2021년부터 2025년까지 총 18억 유로 양자전략 가운데 국가가 부담한 몫이다. 미국의 2026년 의향서와 프랑스의 기존 전략을 같은 날의 신규 자금처럼 합치면 정책 모멘텀은 부풀려진다.

## 5. 발표에서 현금까지, 증거는 여덟 칸을 내려온다

양자 산업은 기술 로드맵이 길어서 서로 다른 단계의 뉴스가 같은 “상용화”라는 말로 섞인다. 이를 막으려면 증거 사다리를 사용해야 한다.

![연구 발표에서 벤치마크, 고객 접근, 주문, 설치, 매출, 반복 주문, 현금으로 내려오는 증거 사다리](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/52/522a02ba6678202fbd86f2af37debb597c7bf97757bf015f2980bcbc227786b9.svg)

첫 칸은 원리 시연이다. 오류정정, 얽힘, 새 칩처럼 기술적 가능성을 보인다. 둘째는 비교 가능한 벤치마크다. 큐비트 수뿐 아니라 정확도, 회로 깊이, 실행시간과 전체 시스템 성능을 함께 공개해야 한다. 셋째는 클라우드나 현장 접근이다. 외부 사용자가 같은 결과를 재현할 수 있어야 한다.

넷째는 유상 주문이다. Rigetti가 인도 C-DAC에서 받은 840만 달러 108큐비트 시스템 주문, D-Wave가 Florida Atlantic University와 맺은 2,000만 달러 Advantage2 설치 계약이 여기에 해당한다. 주문은 고객이 돈을 지불할 의사를 보였다는 강한 증거지만 아직 설치와 매출이 아니다.

다섯째는 납품과 시운전이다. 고객 시설의 냉각, 전력, 네트워크, 안전 조건에 맞춰 기계가 실제로 돌아가야 한다. 여섯째는 회계상 매출이다. 마일스톤과 장비 인도 조건에 따라 분기 매출이 크게 흔들릴 수 있다. 일곱째는 같은 고객이나 다른 고객의 반복 주문이다. 마지막은 영업현금이다. 계약 자산과 미수금이 아니라 현금이 들어와야 사업이 자립하는 방향인지 볼 수 있다.

이 기준으로 보면 2026년 1분기 숫자가 전혀 다르게 읽힌다.

| 회사 | 기술과 2026년 1분기 증거 | 매출 | 영업손실 | 영업현금흐름 | 해석 주의 |
|---|---|---:|---:|---:|---|
| IonQ | 이온트랩, 특수 양자 하드웨어 진행과 인수 사업 확대 | 6,467만달러 | 2억7,151만달러 적자 | 1억5,102만달러 유출 | 755% 성장 전부를 기존 QCaaS의 유기적 성장으로 읽지 않음 |
| D-Wave | 어닐링, 3,340만달러 bookings와 2,000만달러 시스템 계약 | 286만달러 | 5,473만달러 적자 | 4,496만달러 유출 | bookings는 매출이 아니며 장비 인도 시점에 출렁임 |
| Rigetti | 초전도, 108큐비트 일반 제공과 840만달러 C-DAC 주문 | 440만달러 | 2,595만달러 적자 | 1,622만달러 유출 | 주문은 2026년 하반기 예정 납품 전까지 실행 위험이 남음 |
| QUBT | 광자와 파운드리, LSI와 NuCrypt 인수 | 369만달러 | 2,055만달러 적자 | 942만달러 유출 | 매출 증가의 대부분이 인수 효과이고 매출총손실 상태 |

수치는 2026년 7월 22일 DartLab의 EDGAR 분기 패널로 다시 읽었다. 영업손실은 투자와 기술개발을 무조건 나쁘다고 판정하려는 숫자가 아니다. **뉴스의 증거 단계와 회사가 소비하는 현금의 속도를 같은 화면에 놓기 위한 경계선**이다. 순이익은 워런트와 파생상품의 공정가치 변동으로 크게 왜곡될 수 있어 비교에서 뺐다.

```python
import dartlab

for ticker in ["IONQ", "QBTS", "RGTI", "QUBT"]:
    company = dartlab.Company(ticker)
    income = company.panel("IS", freq="Q")
    cashflow = company.panel("CF", freq="Q")
    print(ticker)
    print(income.filter(income["snakeId"].is_in([
        "sales", "operating_income"
    ])).select(["snakeId", "2026Q1"]))
    print(cashflow.filter(cashflow["snakeId"] == "operating_cashflow")
          .select(["snakeId", "2026Q1"]))
```

IonQ의 6,470만 달러 매출과 4억7,000만 달러 잔여 수행의무는 순수 상장사 가운데 상업화 규모가 커졌다는 증거다. 다만 10-Q는 증가분이 특수 양자 하드웨어 구축 진행과 인수 효과에서 주로 왔다고 설명한다. 매출 성장률 하나만 보고 기존 클라우드 사용량이 8배가 됐다고 해석하면 틀린다.

D-Wave의 1분기 매출은 290만 달러로 전년보다 줄었지만 bookings는 3,340만 달러였다. 이는 나쁜 매출과 좋은 주문이 동시에 존재할 수 있다는 사례다. 시스템이 설치되고 고객 검수를 거쳐 매출과 현금으로 내려오는지 다음 칸을 봐야 한다.

Rigetti의 Cepheus-1-108Q는 클라우드에서 제공되고 2큐비트 게이트 중간 정확도 99.1%를 회사가 공개했다. 108이라는 숫자보다 이 정확도가 개선되는지, C-DAC 시스템이 예정대로 배치되는지가 더 중요하다. QUBT의 1분기 매출 369만 달러는 전년 3만9,000달러보다 크게 늘었지만 회사 스스로 LSI와 NuCrypt 인수가 주된 원인이라고 밝혔다.

## 6. Quantinuum 상장은 기술과 가격표를 동시에 공개했다

Quantinuum은 2026년 6월 나스닥에 QNT로 상장해 주당 60달러에 2,800만 주를 팔았고 총 16억8,000만 달러를 조달했다. 전통적 기업공개를 거친 이온트랩 회사가 생겼다는 점에서 IonQ뿐 아니라 전체 양자 순수주의 새로운 비교 기준이 생겼다.

그러나 기업가치가 기술 성숙도를 자동 인증하지 않는다. SEC 투자설명서를 보면 Quantinuum의 2025년 매출은 3,093만 달러, 영업손실은 1억9,930만 달러였다. 2026년 1분기 매출은 520만 달러로 전년 동기 1,910만 달러보다 줄었고 순손실은 1억3,660만 달러였다. 큰 하드웨어 계약의 인식 시점 때문에 매출이 흔들리는 사업 구조가 그대로 드러난다.

Quantinuum의 강점은 QCCD 방식의 이온트랩 하드웨어, 오류정정 연구, TKET 소프트웨어와 응용을 한 회사 안에 묶은 수직 통합이다. 동시에 높은 연구개발비와 고객 집중, 시스템 판매 시점 변동도 함께 공개됐다. IPO가 만든 진짜 가격표는 “가장 좋은 기술” 한 줄이 아니라 **정확도, 논리 연산, 고객 다변화, 매출 인식, 현금 소모를 공개시장 안에서 계속 비교할 수 있게 된 것**이다.

### 양자 계산 한 번이 여섯 회사군을 지난다

회사 지도를 가장 쉽게 이해하는 방법은 QPU를 식당의 화구라고 생각하는 것이다. 화구만 있다고 주문이 음식이 되지는 않는다. 클라우드는 주문을 받는 창구, 컴파일러는 조리법을 주방 언어로 바꾸는 역할, CPU와 GPU는 주문 순서와 오류 처리를 맡는 주방장, 제어장비는 실제 불 세기를 조절하는 손, 냉동기와 레이저는 주방 설비에 해당한다.

1. 제약사, 연구소, 대학, 정부기관이 풀 문제를 정한다.
2. Amazon Braket, Azure Quantum, IBM Quantum 같은 플랫폼에서 QPU와 실행 방식을 고른다.
3. 컴파일러가 회로를 해당 장비가 이해하는 게이트와 펄스로 바꾼다.
4. CPU와 GPU가 회로 최적화, 작업 편성, 측정 반복, 오류 신호 해독을 맡는다.
5. Keysight 같은 제어장비, Oxford Instruments와 FormFactor 같은 극저온·검사장비, Coherent 같은 레이저·광학 부품이 물리 동작을 만든다.
6. IonQ, Quantinuum, Rigetti, D-Wave 같은 QPU가 측정값을 내고 결과가 다시 고객에게 돌아간다.

이 순서를 보면 누가 먼저 돈을 받을지도 보인다. 고객은 플랫폼 사용료나 프로젝트 비용을 낸다. 플랫폼은 QPU 접근권을 공급한다. QPU 회사는 장비를 만들기 위해 제어기, 냉각기, 계측기, 레이저와 웨이퍼를 산다. 완전한 범용 양자컴퓨터가 나오기 전에도 **연구장비와 클라우드 접근, 제어와 시험 층에는 현재형 거래가 생길 수 있다.**

![양자 계산과 양자안전 네트워크에서 고객의 예산이 플랫폼, 장비, 부품과 통신 인프라로 이동하는 지도](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/22/221512f318454d94723473a65e7476e1cc2f893e450a3eb3f019d2e55a5a3412.svg)

| 공정/층위 | 실제로 파는 것 | 대표 회사 | 돈을 내는 고객 | 공시 근거 | 읽을 때 주의 |
|---|---|---|---|---|---|
| 접근 플랫폼 | QPU 작업, 예약, 시뮬레이터, 개발환경 | Amazon, Microsoft, IBM | 기업, 대학, 연구소 | Braket과 Azure에서 여러 회사 QPU를 유료 사용 가능 | 양자 매출은 클라우드 전체에서 따로 공개되지 않음 |
| 게이트형 QPU | 이온트랩·초전도 회로 실행과 시스템 | IONQ, QNT, RGTI, IBM, Alphabet | 클라우드, 국가연구소, 대학, 기업 | 외부 접근, 장비 주문, 일부 현장 설치 | 큐비트 수만으로 방식 간 순위를 매길 수 없음 |
| 어닐링 | 최적화용 QPU와 하이브리드 솔버 | D-Wave | 기업, 대학, 공공기관 | QCaaS와 시스템 구매 계약 | 범용 게이트형과 다른 계산 모델 |
| 고전 가속과 연결 | 회로 시뮬레이션, 오류 해독, GPU와 QPU의 저지연 연결 | NVIDIA, IBM | QPU 개발사, 슈퍼컴퓨팅 센터 | CUDA-Q와 NVQLink 채택·통합 발표 | NVIDIA 전체 매출을 양자 매출로 부를 수 없음 |
| 제어와 판독 | 펄스 생성, 신호 읽기, 교정 시스템 | Keysight | QPU 개발사, 연구소 | Keysight 제어시스템이 Fujitsu·RIKEN 256큐비트 장비에 탑재 | 전사 매출에서 양자 비중은 비공개 |
| 극저온과 웨이퍼 검사 | 밀리켈빈 냉각, 4K 웨이퍼 프로빙, 소자 특성 측정 | Oxford Instruments, FormFactor | 양자 연구소, 파운드리, QPU 개발사 | 양자 전용 냉각·검사 제품군을 판매 | 제품 연결과 큰 양자 매출은 다른 주장 |
| 레이저와 광학 | 이온 포획, 원자 냉각, 광자 생성과 측정용 광원 | Coherent | 이온·중성원자·광자 회사와 연구소 | 양자광학용 레이저 제품군을 판매 | 범용 광학 매출과 양자 수요가 섞임 |
| 웨이퍼와 패키징 | 양자급 웨이퍼, 도파로, 배선과 패키징 | GlobalFoundries, IBM 계획 자회사 | QPU 회사와 정부 프로그램 | 미국의 파운드리 지원 의향서 | 계획 자금과 실제 고객 매출을 구분해야 함 |

Keysight 사례는 이 연결망이 단순 테마표가 아니라는 점을 보여 준다. 회사는 2025년 자사 Quantum Control System이 Fujitsu와 RIKEN의 256큐비트 초전도 컴퓨터에 들어갔다고 밝혔다. 반면 FormFactor의 4K 웨이퍼 검사장비, Oxford Instruments의 희석냉동기, Coherent의 냉각 원자·양자광학 레이저는 양자 전용 제품 페이지가 있어도 양자 매출이 별도 공시되지는 않는다. **제품이 존재한다는 증거, 고객 장비에 들어갔다는 증거, 반복 매출이 커졌다는 증거를 세 칸으로 나눠야 한다.**

대형주 간접 연결도 같은 원칙을 따른다. Amazon과 Microsoft는 여러 QPU의 유통 창구이고 NVIDIA는 고전 계산과 QPU를 잇는 제어면이다. 그러나 이 연결만으로 각 회사의 실적이 양자 수요에 민감하다고 단정할 수 없다. Honeywell도 Quantinuum의 출발과 지분 관계로 연결되지만 QNT 상장 뒤에는 두 회사의 가치와 공시 범위를 따로 읽어야 한다.

## 7. 한국은 양자컴퓨터보다 암호 교체 시계가 먼저 간다

국내 양자 관련주를 미국 순수 하드웨어 회사와 같은 표에 놓으면 가장 큰 오해가 생긴다. 국내 상장사의 실제 제품은 대부분 QKD, PQC, QRNG, VPN, 키관리, 광전송 장비와 보안칩이다.

여기서 **양자 네트워크라는 말도 세 가지로 나눠야 한다.** 첫째는 사용자가 인터넷으로 QPU에 접속하는 클라우드망이다. 둘째는 기존 기업망을 PQC와 QKD로 보호하는 양자안전망이다. 셋째는 멀리 떨어진 양자 노드 사이에 얽힘을 전달하려는 양자인터넷 연구다. 지금 Cisco, Cloudflare, Nokia, KT와 국내 보안장비 회사에서 제품과 매출 경로가 보이는 곳은 주로 둘째다.

**PQC, 즉 양자내성암호는 양자컴퓨터를 쓰는 암호가 아니다.** 일반 CPU와 통신장비에서 돌아가는 새로운 수학 알고리즘이다. 충분히 큰 양자컴퓨터가 RSA와 타원곡선암호를 깨는 미래에 대비해, 양자 공격에도 버티도록 키 교환과 전자서명을 바꾼다. NIST는 2024년 ML-KEM, ML-DSA, SLH-DSA 표준을 확정했고 즉시 전환을 시작하라고 권고했다.

QKD, 즉 양자키분배는 다르다. 광자 같은 양자 상태를 전송해 도청 시 흔적이 생기도록 하고 양쪽이 대칭키 재료를 나눈다. 전용 광링크와 장비가 필요하고 거리, 운용, 인증 비용이 따른다. PQC는 기존 네트워크 전체에 소프트웨어와 펌웨어로 넓게 배포하기 좋고, QKD는 특정 고가치 회선에 물리 계층을 더한다. 둘은 경쟁자이면서 일부 구간에서는 하이브리드로 함께 쓸 수 있다.

![기존 네트워크에서 PQC 소프트웨어 경로와 선택된 광링크의 QKD 경로가 분리된 보안 전환 장면](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/ca/cac62a283d8c9915d2d77245b3b9a7df01a28fb97fd6bb70af344e0b72733487.png)

![PQC, QKD, QRNG가 사용하는 물리 자산과 적용 범위를 비교한 지도](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/84/848d2c89d72d0ba2e27cfdbb0fafd1a27a5dcc916bb4802507bfd6a0bfdebae2.svg)

### 기업의 한 통신이 바뀌는 순서

PQC 전환은 암호 알고리즘 하나를 내려받는 일로 끝나지 않는다. 한 직원이 지사에서 본사 서버에 접속하는 장면만 따라가도 돈이 쓰이는 층이 보인다.

1. 회사는 서버, 인증서, VPN, 라우터에 어떤 암호가 숨어 있는지 목록부터 만든다.
2. 웹과 애플리케이션의 TLS, 인증서, 서명 라이브러리를 PQC 또는 기존 방식과 섞은 하이브리드 방식으로 바꾼다.
3. 지사와 데이터센터 사이의 라우터, 스위치, 방화벽, VPN 터널을 교체하거나 펌웨어를 올린다.
4. 보안칩, HSM, 키관리시스템이 새 키를 만들고 보관하며 수명주기를 관리한다.
5. 국가기간망처럼 특히 중요한 일부 광회선에는 QKD 장비와 키관리 계층을 추가할 수 있다.

| 네트워크 층 | 실제 제품과 역할 | 글로벌 상장사 | 국내 상장사 | 공개된 현재 단계 | 가장 큰 함정 |
|---|---|---|---|---|---|
| 웹·제로트러스트·SASE | TLS, 사내 접속, 사이트 간 IPsec에 PQC 적용 | Cloudflare | 통신사와 보안 서비스사 | Cloudflare One 주요 연결 방식에 하이브리드 ML-KEM 적용 | 무료·번들 기능은 PQC 독립 매출이 아닐 수 있음 |
| 라우터·스위치·방화벽 | 장비 부팅, 관리, MACsec, IPsec, VPN을 양자안전 방식으로 전환 | Cisco, Nokia | 엑스게이트, 케이씨에스 | Cisco 제품 로드맵, Nokia의 이동통신·데이터센터 실증, 국내 Quantum VPN 제품 | 로드맵과 전체 설치 기반 전환을 혼동하면 안 됨 |
| 인증서·키관리·HSM | 키 생성·보관·교체, 전자서명과 인증서 수명주기 관리 | Thales | 아이씨티케이, 케이씨에스 | PQC KMS·CA·라이브러리, Q-HSM과 보안칩 제품 공개 | 제품 출시와 고객 반복 매출은 다른 단계 |
| 통신 회선 | 기업 전용회선에 PQC를 적용하고 선택 구간에 QKD 추가 | Nokia | KT, SK텔레콤, 우리넷 | KT 약관의 QKD·PQC 회선, SKT 하이브리드 제품, 광전송 장비 연결 | 통신사 전체 매출에서 양자 몫은 분리되지 않음 |
| 단말과 보안칩 | 기기 고유키, QRNG, PUF, PQC 연산을 칩에 묶음 | Thales 등 | 아이씨티케이, 케이씨에스 | ICTK의 PQC·PUF 칩과 KMS, KCS의 QKEV7·QC-VPN | 납품처, 물량, 단가가 없으면 실적 민감도를 모름 |

글로벌 연결망도 이미 제품 단계로 내려오고 있다. Cisco는 2026년 12월까지 핵심 포트폴리오 대부분에 양자안전 통신 기능을 제공하겠다는 제품별 로드맵을 냈다. Cloudflare는 TLS뿐 아니라 Zero Trust와 사이트 간 IPsec까지 하이브리드 ML-KEM 경로를 공개했다. Nokia는 라우터와 광전송 장비에서 양자안전 IPsec·MACsec·광전송을 실증했고, Thales는 PKI, HSM, 키관리와 네트워크 암호 전환을 한 묶음으로 제시한다. 이 회사들은 양자컴퓨터 제조사가 아니라 **기존 네트워크 예산이 PQC 전환으로 이동할 때 만나는 회사**다.

한국인터넷진흥원은 2026년 통신, 금융, 교통, 국방, 우주 다섯 분야의 양자내성암호 시범전환을 추진했고, 3월 통신 분야 재공모에는 9억 원 예산을 명시했다. 이 숫자는 국내 양자보안 전체 시장 규모가 아니다. 실제 인프라에서 암호 목록을 찾고, 교체 절차와 성능, 호환성, 제약조건을 뽑는 시범사업 규모다.

KT 이용약관에는 QKD 방식과 PQC 방식의 양자암호 전용회선이 들어가 있다. SK텔레콤은 ID Quantique의 QKD와 자체 PQC를 결합한 제품을 공개했다. 케이씨에스는 QKEV7 기반 QC-VPN, 아이씨티케이는 PQC KMS·CA·라이브러리와 PQC·PUF 보안칩, 엑스게이트는 QRNG가 들어간 Quantum VPN과 PQC 확장 경로를 제품으로 설명한다. 우리넷은 광전송과 양자암호 장비 쪽에 연결된다. 제품 연결은 존재하지만 곧바로 회사 전체의 양자 매출을 뜻하지 않는다.

DART에서 확인해야 할 것은 제품 설명 다음 칸이다. 고객명, 수주금액, 납품 완료, 매출 인식, 같은 고객의 추가 발주가 따로 나오는지 보아야 한다. “양자”라는 단어가 사업보고서에 한 번 등장하는 것보다 **어느 네트워크 층에서 누가 비용을 지불했고 그 거래가 반복됐는지**가 훨씬 강한 증거다.

이 전환은 대형 양자컴퓨터가 완성되기 전에 돈이 쓰인다는 점이 중요하다. 오늘 훔친 암호문을 저장해 두었다가 미래 양자컴퓨터로 푸는 `harvest now, decrypt later` 위험 때문에 수명이 긴 기밀 데이터는 먼저 움직여야 한다. [백신형 보안에서 EDR 운영으로 바뀐 과정](/blog/antivirus-to-edr-who-profits)처럼, 암호 전환도 알고리즘 구매 한 번보다 자산 발견, 키와 인증서 교체, 하이브리드 운영, 검증과 반복 갱신이 긴 사업이 된다.

## 8. 양자 호재를 읽을 때 가장 자주 생기는 오해

첫째, **큐비트가 많으면 가장 좋은 컴퓨터라는 오해**다. 방식, 연결성, 동시에 실행할 때의 정확도, 회로 깊이와 논리 오류율이 다르면 숫자는 직접 비교할 수 없다.

둘째, **양자 우위가 곧 산업 매출이라는 오해**다. 고전컴퓨터가 따라 하기 어려운 벤치마크를 수행하는 것과 고객의 화학, 물류, 금융 문제를 비용보다 싸게 푸는 것은 다른 단계다. DARPA가 utility-scale의 계산 가치와 비용을 함께 보는 이유다.

셋째, **bookings와 매출, 현금을 같은 것으로 보는 오해**다. 주문은 강한 신호지만 고객 시설 준비, 납품, 검수, 마일스톤과 수금이 남는다. D-Wave의 1분기처럼 bookings가 늘고 매출이 줄 수 있다.

넷째, **정부 의향서를 현금 입금으로 쓰는 오해**다. 2026년 미국 20억1,300만 달러는 중요한 산업정책이지만 회사별 조건, 실사, 최종 계약과 집행이 남는 계획 자금이다.

다섯째, **PQC 회사가 양자컴퓨터 회사라는 오해**다. PQC는 기존 컴퓨터에서 실행되는 암호 전환이며 오히려 양자컴퓨터의 위협에 대비하는 시장이다. 국내 관련주의 대부분은 이쪽이다.

여섯째, **순이익이 흑자면 상용화가 끝났다는 오해**다. 워런트 공정가치 변화로 순이익이 커질 수 있다. 매출총이익, 영업손익, 연구개발비, 영업현금흐름과 주식보상을 함께 봐야 한다.

일곱째, **모든 양자 회사가 서로 대체된다는 오해**다. 어닐링은 최적화, 게이트형은 범용 회로, QKD는 키 전달, PQC는 암호 교체다. 예산 경쟁은 할 수 있지만 기술 역할은 서로 다르다.

이 기준은 다른 인프라 기술에도 같다. [800V 직류 데이터센터](/blog/800vdc-ai-data-center-power)에서 제품 발표와 현장 설치를 나눴듯, 양자도 `제안 → 시연 → 외부 접근 → 유상 주문 → 설치 → 반복 매출`의 순서를 건너뛰면 안 된다.

## 9. 관전 포인트는 어느 증거 칸이 실제로 움직이느냐다

미래를 “양자 시대가 온다” 한 줄로 쓰면 검증할 방법이 없다. 앞으로는 다음 네 시나리오를 조건, 변화 경로, 결과, 확인 지표와 반증 조건으로 나눠 보는 편이 낫다.

![정부 제조지원, 장비 반복주문, 논리연산 진전, PQC 전환의 조건과 반증 지표](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/b5/b50f838e7e2c920deaacaa6506f5f1290dbb884653bbd56887d8bc5df85fa371.svg)

### 시나리오 1. 미국의 계획 자금이 실제 제조능력으로 바뀐다면

만약 NIST의 9건 의향서가 최종 계약과 단계별 집행으로 이어지고 IBM과 GlobalFoundries의 파운드리, Rigetti의 판독 전자장치와 냉동기, Quantinuum의 집적광학이 실제 생산설비로 내려간다면 양자 산업의 병목은 연구실 수작업에서 반복 제조로 이동한다.

이 경우 직접 하드웨어 회사뿐 아니라 웨이퍼, 광학, 검사, 극저온, 패키징과 제어장비 층이 강해진다. 관전 지표는 최종 지원계약, 회사별 매칭 투자, 공장 착공과 장비 반입, 수율, 동일 성능 소자의 반복 생산, 고객 인도 일정이다. 의향서가 장기간 최종 계약으로 가지 못하거나, 설비가 생겨도 오류율과 수율이 개선되지 않으면 정책 호재는 연구비 연장에 머문다.

### 시나리오 2. 첫 장비 주문이 반복 주문으로 이어진다면

만약 Rigetti의 C-DAC 시스템과 D-Wave의 FAU 시스템이 예정대로 설치되고, 같은 고객의 확장 주문이나 다른 국가와 기업의 두 번째 주문이 이어진다면 양자컴퓨터는 클라우드 실험도구에서 현장 장비 시장으로 한 칸 내려온다.

이 경우 시스템 통합, 현장 서비스, 냉각과 제어, 소프트웨어 유지보수 매출이 함께 생길 수 있다. 확인할 것은 보도자료 수가 아니라 설치 완료, 검수, 매출 인식, 매출총이익, 유지보수 계약, 반복 고객과 영업현금이다. 납품이 밀리고 계약 자산만 늘거나, 일회성 국가 연구장비 주문 뒤 후속 고객이 없으면 시장은 얕다.

### 시나리오 3. 물리 큐비트보다 논리 연산이 빨라진다면

만약 Google, IBM, Quantinuum, IonQ 같은 회사가 더 큰 코드에서 논리 오류율을 계속 낮추고 실시간 디코딩과 논리 게이트를 외부가 재현한다면 경쟁의 기준은 물리 큐비트 수에서 오류정정된 연산 수로 이동한다.

이때 유리한 회사는 특정 방식 하나로 미리 정할 수 없다. 높은 정확도의 이온트랩, 빠른 초전도 게이트, 모듈 연결, 디코더와 HPC 통합이 서로 다른 경로를 만들기 때문이다. 관전 지표는 물리 대비 논리 오류율, 코드 거리 증가 효과, 논리 2큐비트 게이트, T 게이트와 회로 깊이, 실시간 신드롬 처리, 독립 벤치마크다. 더 많은 물리 큐비트를 투입해도 논리 오류가 줄지 않거나 선택된 벤치마크 밖에서 성능이 무너지면 로드맵은 다시 늦춰진다.

### 시나리오 4. 양자컴퓨터보다 PQC 전환이 먼저 큰 시장이 된다면

만약 미국의 2030년과 2031년 고가치 자산 전환 일정, NIST의 2035년 취약 알고리즘 제거 방향, 한국의 다섯 산업 시범전환이 조달과 인증 기준으로 내려간다면 양자 분야에서 먼저 반복 매출이 커지는 곳은 계산기가 아니라 보안 운영일 수 있다.

이 경우 암호 자산 탐색, PQC 라이브러리, 보안칩, VPN과 전용회선, 인증서와 키관리, 호환성 시험이 연결된다. Cloudflare 같은 엣지망, Cisco와 Nokia 같은 네트워크 장비, Thales 같은 키관리, KT와 SK텔레콤 같은 회선, 아이씨티케이·케이씨에스·엑스게이트 같은 칩과 VPN 회사가 서로 다른 예산에서 만난다. 확인 지표는 시범사업 선정이 아니라 본사업 예산, 표준 적합성, 기존 장비의 펌웨어 교체율, 고객 반복 계약, 독립 제품 매출이다. 성능 저하와 호환성 문제가 해결되지 않거나 조달 일정이 계속 미뤄지면 전환은 긴 하이브리드 단계에 머문다.

양자 분야의 호재는 분명하다. 정부는 제조 병목에 자금을 대기 시작했고, 일부 고객은 실제 장비를 주문했으며, 공개시장은 Quantinuum이라는 새 비교 대상을 얻었다. 그러나 오늘의 반등을 내일의 범용 양자컴퓨터 완성으로 읽을 필요는 없다. **가장 좋은 관전법은 회사 이름을 외우는 것이 아니라, 그 회사의 증거가 사다리의 어느 칸에 있고 다음 칸으로 실제 내려오는지 확인하는 것이다.**

### 원문 근거

- [NIST, 9개 회사 20억1,300만 달러 지원 의향서](https://www.nist.gov/news-events/news/2026/05/department-commerce-announces-letters-intent-9-companies-2-billion)
- [백악관, 양자 혁신 행정명령 팩트시트](https://www.whitehouse.gov/fact-sheets/2026/06/fact-sheet-president-donald-j-trump-ushers-in-the-next-frontier-of-quantum-innovation/)
- [DARPA Quantum Benchmarking Initiative Stage B](https://www.darpa.mil/research/programs/quantum-benchmarking-initiative/stage-b-selection)
- [Google Research, Willow 양자오류정정](https://research.google/blog/making-quantum-error-correction-work/)
- [IBM, 2026 양자 로드맵](https://www.ibm.com/roadmaps/quantum/2026/)
- [IonQ 2026년 1분기 실적](https://investors.ionq.com/news/news-details/2026/IonQ-Announces-First-Quarter-2026-Financial-Results/default.aspx)
- [D-Wave 2026년 1분기 실적](https://www.dwavequantum.com/company/newsroom/press-release/d-wave-reports-first-quarter-2026-results/)
- [Rigetti 2026년 1분기 실적](https://investors.rigetti.com/news-releases/news-release-details/rigetti-computing-reports-first-quarter-2026-financial-results)
- [Quantinuum IPO 투자설명서](https://www.sec.gov/Archives/edgar/data/2110105/000162828026041003/quantinuum-424b4.htm)
- [QUBT 2026년 1분기 10-Q](https://www.sec.gov/Archives/edgar/data/1758009/000121390026054473/ea0289133-10q_quantum.htm)
- [AWS, Amazon Braket 지원 QPU와 실행 방식](https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html)
- [Microsoft, Azure Quantum 개요와 하드웨어 공급자](https://learn.microsoft.com/en-us/azure/quantum/overview-azure-quantum)
- [NVIDIA, QPU와 GPU를 연결하는 NVQLink](https://www.nvidia.com/en-us/solutions/quantum-computing/nvqlink/)
- [Keysight, Fujitsu·RIKEN 256큐비트 장비 제어시스템](https://www.keysight.com/be/en/about/newsroom/news-releases/2025/0515-pr25-073-keysight-quantum-control-system-embedded-within-fujitsu-and-rikens-world-leading-256-qubit-quantum-computer.html)
- [FormFactor, 양자용 극저온 웨이퍼 검사장비](https://www.formfactor.com/products/quantum-cryo/)
- [Oxford Instruments, 양자용 극저온·제조·측정 장비](https://www.oxinst.com/applications/quantum-technology)
- [Coherent, 냉각 원자와 양자광학용 레이저](https://www.coherent.com/industrial-solutions/instrumentation/scientific/cold-atoms-quantum-optics)
- [NIST 양자내성암호 표준](https://csrc.nist.gov/Projects/Post-Quantum-Cryptography)
- [KISA 2026년 양자내성암호 시범전환](https://www.kisa.or.kr/402/form?lang_type=KO&page=2&postSeq=2569)
- [Cisco, 양자안전 통신 제품 로드맵](https://www.cisco.com/site/us/en/about/trust-center/post-quantum-cryptography.html)
- [Cloudflare, TLS·Zero Trust·IPsec의 PQC 적용](https://developers.cloudflare.com/ssl/post-quantum-cryptography/)
- [Nokia, KDDI 데이터센터 양자안전 광전송 실증](https://www.nokia.com/newsroom/nokia-and-kddi-demonstrate-quantum-safe-optical-transport-for-secure-ai-and-data-center-infrastructure/)
- [Thales, PKI·키관리·네트워크 양자안전 전환](https://cpl.thalesgroup.com/sites/default/files/content/solution_briefs/quantum-safe-security-data-identities-networks-sb.pdf)
- [케이씨에스, QKEV7 기반 QC-VPN](https://www.kcins.co.kr/)
- [아이씨티케이, PQC KMS·CA·라이브러리](https://ictk.com/pressRelease/?bmode=view&idx=161872957)
- [엑스게이트, Quantum VPN](https://www.axgate.com/main/about/product/quantum.php)

> 이 글은 기술과 산업 구조를 이해하기 위한 자료다. 특정 종목의 매수나 매도를 권하지 않는다. 수치 기준일은 2026년 7월 22일이며, 의향서와 로드맵은 이후 최종 계약과 실행 과정에서 달라질 수 있다.
