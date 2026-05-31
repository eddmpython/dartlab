"""Horizon Meaning Learner V76 - bounded coordinate relay rows.

V76 실제 기록
--------------
아이디어:
    V33 은 same-suffix 오염을 막아 `손실충당금 -> 대손충당금` 을 살리고 bad accepted 를 0/7 로 낮췄다.
    남은 실패는 `외상매출금 -> 매출채권` 이다. 이 둘은 suffix family 가 아니라 compound 내부 substring
    (`매출`) 을 공유하고, 의미상 같은 장면에서 함께 쓰이는 표면이다. 반면 `매출액` 도 `매출` 을 공유하므로
    단순 substring overlap 만 쓰면 revenue 쪽으로 빨려간다.

    V34 는 tokenized surface pair 로 compound co-view 를 세었다. 그러나 DART 표/문장 안에서는
    `외상매출채권` 처럼 붙은 복합어가 raw 본문에는 있어도 surface pair 로 분리되지 않는다. 그 결과
    `외상매출금 -> 매출채권` 은 route top1 까지는 올라왔지만 compound path 가 0 으로 남아 accepted=False 였다.

    V35 는 긴 raw token 안의 의미 후보 substring 을 pseudo-occurrence 로 추가했다. pseudo surface 는 같은 위치의
    앞뒤 stem 경험을 물려받고, substring 포함 관계가 pair index 에 들어가므로 `외상매출채권` 안의
    `매출채권` 같은 bridge 가 tokenized pair 없이도 학습된다. 특정 alias map 이 아니라 현재 query/target
    후보군의 coordinate compound gram 과 겹치는 raw substring 만 올리는 방식이다.

    남은 문제는 accepted 가 후보별 독립 판정이라 top1 은 맞아도 2순위 `매출액` 같은 약한 compound 후보가
    accepted=True 로 열리는 점이다. V36 은 route 를 후보 간 경쟁 문제로 보고, top1 대비 점수 margin 이
    약한 non-top 후보의 accepted 를 닫는다. alias map, target 예외, 수동 family lock 없이 query 내부의
    상대적 확신만 사용한다.

    V36 의 남은 문제는 route 는 맞아도 search hit snippet 이 차입금 표 조각처럼 보이는 것이다. candidate unit 은
    target surface posting 으로 잡혔을 수 있지만, chunk 앞 110 자를 그대로 잘라 보여주면 실제 evidence 위치가
    뒤에 있어도 앞쪽 표 조각이 대표 근거가 된다. V37 은 unit rerank 에 route target/query surface/relation
    evidence 를 넣고, 반환 snippet 도 evidence term 주변으로 자른다. alias map 없이 현재 route target 과
    query stem, raw bridge proxy 만 사용한다.

    V37 의 한계는 relation proximity 를 검색 시점에 chunk 전체에서 다시 계산한다는 점이다. `매출채권` 과
    `증가` 가 같은 chunk 안에 있어도 실제 가까운 span 인지 후보 생성 단계에서 모른다. V38 은 build 단계에서
    모든 surface 와 relation term 의 거리 기반 span posting 을 만든다. search 는 `(routeTarget, polarity)`
    posting 을 후보 생성에 직접 넣고, unit score/snippet 도 span strength 를 우선한다.

    V38 의 한계는 거리 기반 span 이라 `대손충당금 설정금액 증가 ... 매출채권` 처럼 relation 이 다른 명사를
    수식하고 target 은 표 항목으로 근처에만 있어도 강한 evidence 로 본다는 점이다. V39 는 surface, value,
    relation 의 순서를 frame 으로 만든다. `surface -> 숫자/금액 -> 증가/감소` 는 강하게, `relation -> ... -> surface`
    는 표 항목 후행 가능성이 커서 약하게 준다. target 예외나 alias map 이 아니라 순서와 값 slot 만 사용한다.

    V39 의 남은 문제는 표 narrative 와 table row 가 같은 chunk 안에 붙을 때다. 예를 들어 `대손충당금 설정금액 증가`
    뒤에 `구분 계정과목 ... 매출채권 ...` row 가 오면, 단순 span/order frame 은 아직 `매출채권 증가` evidence 로
    오인할 수 있다. V40 은 relation 과 target 사이의 table fence (`구분`, `계정과목`, `채권금액`, `설정률`, `단위`)
    를 build-time leak 신호로 별도 인덱싱하고, leak 이 강한 후보는 search score 에서 강하게 낮춘다.

    V40 의 남은 문제는 같은 문장 안에 여러 대상과 여러 변화가 섞일 때 relation 이 어느 surface 에 귀속되는지
    충분히 분리하지 못한다는 점이다. `당기순이익은 감소하여 영업이익에 비해 감소폭...` 같은 문장은
    `감소`가 실제로는 당기순이익에 붙고, `감소폭`은 명사형 비교 표현인데도 `영업이익 감소` evidence 로 잡힐 수 있다.
    V41 은 relation occurrence 를 surface 에 귀속시키는 role-bound frame 을 추가한다. 같은 절 안에서 relation 과
    직접 결속된 surface 를 owner 로 보고, `감소폭/증가율/감소액` 같은 bound noun relation 은 약하게 만든다.

    V41 의 남은 문제는 작은 표본에서 직접 polarity-bound 근거가 없을 때도 약한 span 후보를 답처럼 반환한다는 점이다.
    V42 는 검색 결과를 단일 점수로만 내지 않고 `reliable/weak/abstain` 상태로 분리한다. bound evidence 가 강하면
    reliable, span/frame 은 있으나 bound 가 약하면 weak, polarity-bound 근거가 없으면 abstain 으로 기록한다.
    이는 정답을 더 맞히는 튜닝이 아니라 의미 검색기가 근거 없는 의미 연결을 말하지 않게 하는 신뢰도 게이트다.

    V42 의 남은 문제는 abstain 을 내린 뒤 보강 경로가 없다는 점이다. V43 은 main 학습셋은 그대로 두고,
    더 넓은 row/file 범위에서 relation-bound 후보만 별도 side unit 으로 수집한다. 이 side unit 은 route/signature
    학습에는 넣지 않고 search fallback posting 에만 쓴다. 따라서 경험 그래프의 주 학습 분포를 흔들지 않으면서,
    abstain 이 나왔을 때 CPU 친화적으로 이미 만들어 둔 side posting 만 조회한다.

    V43 의 남은 문제는 side fallback 이 효과는 있지만 side unit 을 full Unit/Cache/signature 흐름에 붙여
    build/메모리 비용이 커진다는 점이다. V44 는 side 를 모델의 정규 unit 으로 보관하지 않고, `sidePayload(ref,text)` 와
    `(surface, relation) -> sideId` bound posting 및 score 만 남긴다. fallback scoring 도 이 compact payload 만 사용한다.

    V44 의 남은 문제는 side payload 는 compact 하지만 side bound index 생성을 위해 여전히 side unit 을 tokenize 해서
    Cache 를 만든다는 점이다. V45 는 side chunk 에서 TOKEN_RE 와 rawBridgeSubsurfaces 로 surface position 을 바로
    뽑고, relation position 과 즉시 bound posting 을 만든다. 즉 side 는 Cache/Occ/stem list 를 만들지 않고
    `SidePayload + direct bound posting` 만 생성한다.

    V45 의 진단은 side cache 제거가 1,200 표본에서는 도움이 됐지만 4,000 표본에서는 main relation
    frame/bound build 비용에 묻힌다는 것이다. 기존 main frame 은 unit 마다 모든 surface 와 모든 relation
    occurrence 를 곱으로 비교한 뒤 거리 함수 안에서 다시 버렸다. V46 은 relation occurrence 를 중심으로
    `FRAME_MAX_DISTANCE * 2` 안의 surface position 만 bisect window 로 꺼내 평가한다. 이는 정답어 예외나
    family lock 이 아니라, 기존 frame/leak/bound 함수가 실제로 의미 있다고 인정하는 거리 영역만 build 단계에서
    먼저 자르는 구조적 pruning 이다.

    V46 의 남은 중복은 span index 가 아직 별도 builder 에서 surface 별 `allPositions` 와 relation positions 를
    다시 만든다는 점이다. V47 은 한 번 만든 relation-local surface position map 으로 span/frame/leak/bound 를
    동시에 산출한다. 즉 relation occurrence 주변의 경험 그래프를 한 번 순회하면서 거리 span, 순서 frame, table leak,
    owner-bound 를 모두 얻는 구조다. scoring/acceptance/search gate 는 유지해 변화 원인을 build 통합으로 분리한다.

    V47 의 남은 병목 후보는 `surfacePairDf` 다. 기존 builder 는 각 unit 안의 모든 surface 조합을 세어
    4,000 표본에서 120만 개 이상의 pair 를 만든다. 그러나 실제 `directPairAssociation()` 호출은 route/search 의
    target 후보와 query/proxy 사이에서만 일어난다. V48 은 `surfaceDf` 는 전체 surface 에 대해 유지하되,
    `surfacePairDf` 는 한쪽이 `TARGETS` 인 pair 만 저장한다. 이는 target 예외처리가 아니라 현재 scorer 가
    실제 조회하는 역인덱스 표면만 물리화하는 sparse posting pruning 이다.

    V48 결과 pair footprint 는 크게 줄었지만 wall-clock 병목은 그대로였다. 다음 후보는 suffix cohort contrast 다.
    기존 contrast index 는 cohort 별 모든 meaning atom count 를 보관해 4,000 표본에서 약 480만 cohort atom entry 를
    만든다. 그러나 contrast 의 핵심 기능은 같은 suffix cohort 에서 너무 흔한 경험을 감쇠하는 것이다. V49 는 각
    surface signature 의 상위 meaning atom 만 cohort DF 에 투입하고, cohort 안에서 `CONTRAST_COMMON_RATIO` 이상인
    common atom 만 저장한다. rare atom 의 정확한 ratio 는 버리고 rare 는 기본적으로 distinctive 로 취급한다.

    V49 이후 남은 비용 후보는 sketch/signature 쪽이다. `horizonAtoms(unit, position)` 는 surface 자체가 아니라
    같은 위치의 marker 와 주변 stem 좌표 경험으로 결정되는데, 기존 코드는 buildSketches 와 buildSignatures 에서
    같은 unit/position 을 반복 계산했다. rawBridge pseudo surface 도 같은 position 을 공유하므로 중복이 더 커진다.
    V50 은 unitId+position 별 horizon atom cache 를 공유해 sketch 와 signature 가 같은 경험 atom 을 재사용한다.
    scorer 는 그대로 두고, 경험 수평선 atom 생성 비용만 줄인다. 동시에 stage timing 을 찍어 다음 병목을 분리한다.

    V51 은 line atom cache 를 시도했지만 cache hit 가 낮아 4,000 표본에서 오히려 느려졌다. V52 는
    `relayExperience` fanout 을 top6 이웃 × top16 atom 으로 줄여 품질을 유지하면서 4,000 totalSeconds 를
    165.6 으로 낮췄다. V53 은 raw signature counter 를 lane 별로 pruning 하고 relay source 의 common suffix
    atom 을 quarantine 했다. footprint 와 relay update 는 줄었지만 buildSignatures 는 74.5s 로 그대로였고,
    내부 timing 에서 raw atom 생성이 57.8s 로 대부분이었다.

    V54 는 after-prune 이 아니라 raw atom 생성 호출 자체를 줄인다. surface 별 occurrence 를 모두 쓰지 않고,
    rawBridge pseudo occurrence, relation 주변 occurrence, 숫자/값 주변 occurrence, 조사 marker 가 있는
    occurrence 를 우선한다. 여기에 unit/position bucket 다양성을 넣어 같은 표 row 반복이 signature 를
    지배하지 않게 한다. 이는 target 예외가 아니라 문서 안에서 의미 근거가 생길 가능성이 높은 경험 위치를
    먼저 선택하는 focused occurrence sampling 이다.

    V54 이후 남은 병목은 buildSketches 22.7s 와 focusedRelation 27.4s 다. V55 는 같은 occurrence sampling 을
    buildSketches 로 옮기되, sketch 는 lineAtoms 의 기반이므로 signature 보다 넓은 budget 을 둔다.
    1-pass 로 희소 surface 는 전량 유지하고, 2-pass 로 빈번한 surface 에서 relation/value/bridge/marker 근거와
    unit-position 다양성을 우선한다. 단순 sampling 은 `현금및현금성자산` 같은 self-echo compound 의 suffix alias
    경로를 깨므로, 반복 gram 이 있거나 `및` 으로 연결된 compound surface 는 sketch 단계에서 전량 보존한다.
    즉 sketch recall 을 보존하면서 반복 표 row 경험만 줄이는 구조다.

    V56 은 sketch/signature sampler 를 공유했지만 4,000 표본에서 V55 보다 느려져 본진 투입 가치가 낮았다.
    따라서 V57 은 V55 로 돌아와 focusedRelation 병목을 직접 겨냥한다. 현재 relation-local loop 는 같은
    relation occurrence 안에서 surface pair 마다 owner 후보 목록을 다시 훑어 best owner 를 계산한다.
    V57 은 relation occurrence 별로 owner frame 을 한 번 만들고, 각 pair 에서는 그 owner frame 을 재사용한다.
    bound 의미는 유지하면서 반복 owner scan 을 제거하는 구조다.

    V57 이후 병목은 buildSignatures 44.4s 와 buildSketches 18.3s 로 이동했다. 특히 signature raw 단계는
    선택된 occurrence 마다 `lineAtoms()` 안에서 stem 의 top sketch atom, sketch cell, stable hash 를 다시
    계산한다. V58 은 sketch 결과를 stem -> self atom, neighbor atom hash, sketch cell 로 한 번 물리화한
    `SketchAtomView` 로 만들고, `lineAtoms()` 는 이 view 를 조립만 하게 한다. 의미 atom 정의, sampling,
    scoring 은 유지하고 반복 hash/most_common 계산만 제거하는 CPU 구조 개선이다.

    V58 이후 남은 병목 중 하나는 buildUnitIndex 11.1s 다. 기존 unit index 는 unit 안의 occurrence 를
    그대로 순회하며 같은 surface 가 반복될 때마다 `model.signatures[surface].most_common(12)` 를 다시
    훑고 같은 atom 을 더했다. V59 는 surface 별 unit atom view 를 한 번 만들고, unit 내부에서는
    `Counter(surface)` 로 반복 surface 를 묶어 atom weight 를 occurrence count 만큼 더한다. unit signature 의
    의미와 posting 후보는 보존하되 반복 표 row 조립 비용을 줄이는 구조다.

    V60 은 relay 자체는 줄였지만 전체 시간은 악화되어 본진 후보로 약했다. V61 은 V59 기준으로 돌아와
    side fallback 의 buildSideBoundPayloadIndex 병목을 줄인다. 기존 side bound 는 payload 안의 모든
    surface 와 모든 relation occurrence 를 곱으로 비교하고, 각 pair 마다 owner 후보 목록을 다시 스캔했다.
    V61 은 main focusedRelation 처럼 relation occurrence 주변 FRAME_MAX_DISTANCE 안의 surface 만 평가하고,
    relation occurrence 별 owner frame 을 한 번 계산해 pair 들이 공유한다. side fallback 의 의미는 유지하면서
    compact side posting build 비용을 줄이는 구조다.

    V62 는 focusedRelation 의 intervening 미세 최적화였지만 개선폭이 없어 본진 가치가 낮았다. V63 은 V61
    기준으로 돌아와 buildSketches/buildSignatures 가 공유하는 horizon atom raw 경로를 겨냥한다. 기존
    `horizonAtoms()` 는 position 마다 주변 stem 의 `isContentStem`, `coordCells`, marker 정규화, 좌/우 nearest
    cell 계산을 반복했다. V63 은 cache 단위로 token content flag, marker cell, coordinate cells 를 미리 만든
    `HorizonTokenView` 를 공유하고, horizon atom 생성은 view 조립만 하게 한다. 의미 atom 정의와 sampling 은
    유지하고 반복 좌표 lookup 비용만 줄이는 구조다.

    V64 는 V61 의 성공한 sideBound 구조 위에 V63 horizon token view 와 V60 relay atom view 를 합성해
    품질을 유지하면서 4,000 totalSeconds 를 80.1 까지 줄였다. 그러나 rawBridge seed 는 아직
    `TARGETS`/probe surface 에서 만든 `BRIDGE_SEED_SURFACES` 에 직접 기대고 있다. 이 구조는 성능은 좋지만
    사용자가 우려한 "정답어를 보고 graph 를 그리는" 방향으로 해석될 여지가 있다.

    V65 는 bridge 없는 base tokenize 를 먼저 수행하고, base cache 의 실제 corpus surface DF/TF 에서
    rawBridge seed 를 뽑는 2-pass 구조를 검증했다. target/probe seed 없이도 품질은 유지됐지만, corpus seed 가
    너무 넓어 rawBridge hits 가 4,000 표본에서 229,485 까지 늘고 totalSeconds 가 115.0 으로 후퇴했다.

    V66 은 같은 2-pass corpus seed 방향을 유지하되 seed 를 단순 DF/TF top-k 가 아니라 relation/value 근처에서
    실제로 관측된 경험 surface 로 점수화한다. 또한 corpus 에 독립 surface 로 관측된 substring 은 self seed
    anchor 로 허용하되, token 하나에서 그래프에 얹는 bridge pseudo surface 는 상위 4개로 제한한다. 목적은
    target/probe seed 없이 품질을 유지하면서 V65 의 과도한 pseudo occurrence footprint 를 줄이는 것이다.

    V67 은 unit-local relation/value gate 로 bridge 적용 위치를 줄였지만, range 계산과 relation index 비용이
    커져 4,000 표본 totalSeconds 가 108.2 로 악화됐다. V68 은 corpus seed score floor 로 약한 bridge 를
    제거했지만 `영업손익 -> 영업이익` recall 이 끊겼다. 진단 결과 이 route 는 `매출액또는손익구`,
    `기손익인식금융자`, `감소하였습` 같은 공시 제목/표 boilerplate bridge 조각의 경험도 일부 사용했다.

    V70 은 lane 을 route penalty 로 분리해 오염 점수를 낮췄지만 buildSignatures relay 가 4,000 표본에서 13.3s 로
    남았다. V75 는 line atom cache 로 raw 중복을 줄였지만 후반 relay/메모리 비용을 이기지 못했다. V76 은 relay 를
    직접 겨냥한다. 기존 relay 는 surface 마다 `coordAtoms(surface)` 의 모든 postings row 를 훑는데, `cx:g1`,
    `cx:p1`, `cx:s1` 같은 1글자 좌표 atom 은 수평선의 아주 넓은 주변부라 후보 fanout 을 키운다. V76 은 2글자
    이상 좌표 atom 만 relay 후보 row 로 쓰고, row 가 넓으면 surface 의 experience mass 로 bounded top row 만
    유지한다. 또한 buildSignatures 에서 만든 bounded coord postings 를 Model 에 재사용해 같은 row 를 다시 만들지
    않는다. target alias, target/probe seed, 수동 family lock 은 추가하지 않는다.

시도 방법:
    1. V33 의 coordinate experience line, suffix cohort contrast, nonSuffix resonance gate 를 유지한다.
    2. 긴 token 에서 length 4~8 substring 을 뽑되, query/target 후보군의 coordinate compound gram 과 충분히
       겹치는 substring 만 pseudo-occurrence 로 추가한다.
    3. pseudo surface 는 원 token 과 같은 position 에 놓고 horizon/experience-line sketch 를 학습시킨다.
    4. pseudo surface 까지 포함한 pair index 로 compound association 을 다시 계산한다.
    5. route score 에 compound association 을 보조 신호로 더하고, accepted 조건에도 compound path 를 추가한다.
    6. route 정렬 후 top1 대비 score ratio/gap 을 계산해 non-top accepted 오염을 닫는다.
    7. search rerank 에 target/query/bridge evidence coverage 를 추가하고 evidence 위치 중심 snippet 을 반환한다.
    8. surface-relation span posting 을 build-time 인덱스로 만들어 relation query 의 후보 생성/점수에 사용한다.
    9. surface-value-relation order frame 을 추가해 실제 target 값 변화처럼 보이는 span 을 우선한다.
    10. relation-target 사이에 table fence 가 있는 row-leak 후보를 별도 점수로 만들고 rerank 에서 낮춘다.
    11. relation occurrence 의 owner surface 를 같은 절/거리/명사형 여부로 추정해 role-bound score 를 만든다.
    12. search hit 에 reliable/weak/abstain 상태를 붙여 직접 polarity-bound 근거가 약하면 답으로 확정하지 않는다.
    13. main search 가 reliable 을 못 찾으면 side-bound posting 을 조회해 route target/relation 직접 근거만 보강한다.
    14. side unit 을 full signature/unit 으로 저장하지 않고 compact payload + bound score 만 유지한다.
    15. side index 생성도 tokenize/cache 없이 chunk 에서 surface/relation 위치를 직접 추출한다.
    16. main relation frame/bound 는 relation occurrence 주변 window 에 들어온 surface position 만 평가한다.
    17. owner surface 도 relation 주변 bound window 로 제한해 role-bound owner 탐색 비용을 줄인다.
    18. 기존 scoring 함수와 acceptance/search gate 는 유지해 품질 변화가 pruning 때문인지 분리해 본다.
    19. span/frame/leak/bound posting 을 하나의 relation-local pass 에서 동시에 만든다.
    20. span 은 기존처럼 surface/relation start distance 로 strength 를 계산해 search 후보 recall 을 유지한다.
    21. surface pair 는 전체 pair 대신 target-linked pair 만 세어 compound association 조회 표면과 build 표면을 맞춘다.
    22. suffix cohort contrast 는 모든 atom ratio 대신 bounded top atom + common atom set 만 저장한다.
    23. unit/position 단위 horizon atom cache 를 buildSketches/buildSignatures 가 공유한다.
    24. buildModel stage timing 을 남겨 다음 최적화 대상을 증거 기반으로 고른다.
    25. coordinate relay fanout 을 top6 이웃 × top16 atom 으로 제한하고 relay update 수를 계측한다.
    26. raw signature counter 를 xp/hx/el/other lane 별 상한으로 먼저 prune 한 뒤 DF weighting 한다.
    27. relay source 에서는 suffix cohort common meaning atom 을 제거해 같은 suffix 경험 오염 전파를 줄인다.
    28. buildSignatures 는 surface 별 occurrence budget 을 두고 relation/value/bridge/marker 근거와
        unit-position 다양성 기준으로 occurrence 를 먼저 sampling 한다.
    29. buildSketches 에도 2-pass occurrence sampling 을 적용하되, 희소 surface 와 self-echo compound
        surface 는 전량 유지하고 frequent surface 만 signature 보다 넓은 sketch budget 으로 줄인다.
    30. relation occurrence 별 owner frame 을 미리 계산하고 relationBoundStrength 의 owner scan 을 재사용한다.
    31. sketch 결과를 `SketchAtomView` 로 precompute 해 signature raw 단계의 반복 `most_common/stableHash`
        호출을 줄인다.
    32. unit index 에서 surface별 top atom view 를 precompute 하고 unit 내부 반복 surface 는 count 로 묶어
        같은 의미 atom 누적을 한 번에 처리한다.
    33. side-bound payload index 도 relation-local window 와 ownerFrame 캐시를 사용해 전체 surface×relation
        곱과 pair별 owner scan 을 제거한다.
    34. cache 단위 `HorizonTokenView` 로 content flag, marker, coord cells 를 미리 계산해 buildSketches 와
        buildSignatures 의 horizon atom 생성이 같은 token view 를 공유하게 한다.
    35. relay source surface 별 top relay atom view 도 precompute 해 relayExperience 의 반복 `most_common`
        호출을 줄인다.
    36. rawBridge 를 target/probe seed 에서 떼어내기 위해 bridge 없는 `tokenizeBase` 를 먼저 만든다.
    37. base cache 에서 relation token 과 value token 위치를 잡고, 그 근처에서 관측된 surface 에 evidence score 를
        부여한다.
    38. corpus seed 후보는 한글 surface, 길이, content stem, 문장 종결/HTML 잡음 필터와 relation/value evidence 만
        사용한다. target/probe alias, 수작업 family lock, 정답별 예외는 넣지 않는다.
    39. substring 자체가 corpus seed 로 독립 관측됐다면 self seed anchor 로 허용한다. 이것은 정답어 예외가 아니라
        "부분 stem 이 이미 corpus 에서 경험을 가진 surface 인가" 를 보는 일반 규칙이다.
    40. base cache 를 다시 tokenize 하지 않고 같은 stem position 위에 corpus-derived bridge pseudo occurrence 를
        얹어 cache 를 증강한다.
    41. main focused relation 과 side bound position extraction 도 같은 `BridgeSeedIndex` 를 사용해 evidence
        위치 추적과 학습 cache 의 bridge 기준을 맞춘다.
    42. token 하나에서 추가하는 bridge pseudo surface 는 seed anchor/길이 기준 상위 4개로 제한해 V65 의 과도한
        bridge fanout 을 줄인다.
    43. token lane 을 relation/value 위치, 숫자, 공시 artifact 힌트, 긴 non-relation 표면, owner 후보성으로
        `sentence`, `artifact`, `owner` 로 분류한다.
    44. rawBridge pseudo occurrence 는 원 token 의 position 뿐 아니라 lane 도 함께 상속한다.
    45. `lineAtoms()` 에서는 lane atom 을 추가하지 않고 기존 coordinate/experience atom 만 만든다.
    46. cache occurrence 전체에서 surface 별 `sentence/artifact/owner` lane profile 을 별도 집계한다.
    47. route 단계에서 artifact mismatch 와 resonance 가 낮은 owner-lane 전이를 penalty 로 넣어, 경험 atom fanout 없이
        title/table/owner 오염을 낮출 수 있는지 확인한다.
    48. lane profile probe 를 출력해 positive/negative 표면의 lane 분포 차이가 실제로 penalty 근거가 되는지 확인한다.
    49. relay 후보 postings 에서는 `cx:g1`, `cx:p1`, `cx:s1`, `cx:full` 을 제외하고 2글자 이상 좌표 atom 만 사용한다.
    50. relay row 가 넓으면 surface signature 의 xp/el/hx experience mass + coordinate mass 로 정렬해 bounded row 로
        줄인다. 기본 row limit 은 2글자 atom 160, 3글자 이상 atom 320 이다.
    51. `relayPostings` 에 rawLinks/keptLinks/skippedBroad/prunedRows/maxRow 를 출력해 후보 fanout 절감량을 기록한다.
    52. buildSignatures 가 만든 bounded coord postings 를 Model 생성에도 재사용해 같은 sparse row materialization 을
        반복하지 않는다.

실행:
    uv run python -X utf8 -m py_compile tests/_attempts/horizonMeaning/horizonMeaningLearnerV76Test.py

    $env:DARTLAB_HORIZON_V76_MAX_FILES_PER_SOURCE='8'
    $env:DARTLAB_HORIZON_V76_MAX_RECORDS_PER_SOURCE='180'
    $env:DARTLAB_HORIZON_V76_MAX_UNITS='1200'
    $env:DARTLAB_HORIZON_V76_MAX_WINDOWS_PER_RECORD='2'
    uv run python -X utf8 tests/_attempts/horizonMeaning/horizonMeaningLearnerV76Test.py

    $env:DARTLAB_HORIZON_V76_MAX_FILES_PER_SOURCE='20'
    $env:DARTLAB_HORIZON_V76_MAX_RECORDS_PER_SOURCE='600'
    $env:DARTLAB_HORIZON_V76_MAX_UNITS='4000'
    $env:DARTLAB_HORIZON_V76_MAX_WINDOWS_PER_RECORD='3'
    uv run python -X utf8 tests/_attempts/horizonMeaning/horizonMeaningLearnerV76Test.py

판정 기준:
    V70 과 같은 품질 기준을 유지해야 한다. 즉 `외상매출금 -> 매출채권`, `영업손익 -> 영업이익`,
    `현금성자산 -> 현금및현금성자산`, `손실충당금 -> 대손충당금` positiveHits=4/4 와 badAccepted=0/7,
    searchTop1=5/5, reliableSearch=5/5 를 유지해야 한다. 동시에 4,000 표본에서 V70 의 buildSignatures 41.2s,
    relay 13.3s, totalSeconds 104.1s 를 줄이고, 가능하면 V66 의 totalSeconds 100.4s 도 넘겨야 본진 후보로 본다.

결과:
    1,200 units + direct side payload 600개:
        tokenizeBase=1.6s, buildCorpusBridgeSeedIndex=1.3s, augmentBridgeSurfaces=0.8s.
        bridgeSeeds corpusSeeds=2,400, candidates=3,618, evidenceSurfaces=6,526,
        rawBridge surfaces=4,328, hits=40,345, cache=7,044.
        horizonView caches=1,200, tokens=175,983,
        lanes={'sentence': 150325, 'artifact': 16571, 'owner': 9087}.
        sketchSample=150,989 -> 116,480, lanes={'sentence': 79177, 'artifact': 24316, 'owner': 12987},
        buildSketches=7.9s.
        signature occSample=150,989 -> 96,259,
        lanes={'sentence': 65341, 'artifact': 18653, 'owner': 12265}, buildSignatures=17.4s.
        rawPrune atoms=2,933,152 -> 1,812,361, el=58,222.
        relayPostings keys=54,339, rawLinks=220,061, keptLinks=139,623,
        skippedBroad=80,277, prunedRows=7, maxRow=160.
        signatureStage view=0.2s, sample=2.5s, raw=5.8s, prune=2.7s, weight=2.7s,
        relaySource=2.1s, relay=1.4s.
        relay views=9,967, updates=716,800, view=0.3s, build=1.1s.
        laneProfile surfaces=10,902, artifactHeavy=2,294, ownerHeavy=1,522.
        focusedRelation relationOcc=1,312, spanPairs=81,891, localPairs=150,820,
        ownerFrames=1,312, buildFocusedRelationIndexes=4.0s.
        sideFocusedBound payloads=600, relationOcc=1,575, localPairs=102,451,
        ownerFrames=1,575, buildSideBoundPayloadIndex=1.9s.
        buildUnitIndex=1.1s, modelSeconds=41.9, totalSeconds=44.4.
        laneProbe: 외상매출금 S1.00/A0.00/O0.00, 매출채권 S0.48/A0.49/O0.02,
        대손충당금 S0.71/A0.00/O0.29, 복구충당금 S1.00/A0.00/O0.00.
        `외상매출금 -> 매출채권` accepted=True(score 0.080, cp 0.055), `매출액` 2순위는
        accepted=False. `현금성자산 -> 현금및현금성자산` accepted=True(score 1.561).
        `영업손익 -> 영업이익` accepted=True(score 0.182).
        `손실충당금 -> 대손충당금` accepted=True(score 0.113).
        `복구충당금 -> 대손충당금` 은 score 1.040 으로 accepted=False.
        `대출채권 -> 대손충당금` 은 score 0.037 로 accepted=False.
        positiveHits=4/4, badAccepted=0/7, searchTop1=5/5, reliableSearch=5/5.

    4,000 units + direct side payload 600개:
        tokenizeBase=5.5s, buildCorpusBridgeSeedIndex=4.1s, augmentBridgeSurfaces=1.9s.
        bridgeSeeds corpusSeeds=2,400, candidates=6,041, evidenceSurfaces=10,548,
        rawBridge surfaces=5,725, hits=137,244, cache=11,447.
        horizonView caches=4,000, tokens=607,533,
        lanes={'sentence': 520182, 'artifact': 53620, 'owner': 33731}.
        sketchSample=505,826 -> 275,808, lanes={'sentence': 182038, 'artifact': 51914, 'owner': 41856},
        buildSketches=19.3s.
        signature occSample=505,826 -> 208,173,
        lanes={'sentence': 136450, 'artifact': 36514, 'owner': 35209}, buildSignatures=33.8s.
        rawPrune atoms=4,607,269 -> 2,757,382, el=94,220.
        relayPostings keys=81,530, rawLinks=334,322, keptLinks=211,662,
        skippedBroad=121,533, prunedRows=17, maxRow=219.
        signatureStage view=0.3s, sample=7.6s, raw=12.5s, prune=4.0s, weight=4.4s,
        relaySource=2.6s, relay=2.4s.
        relay views=15,233, updates=1,112,394, view=0.4s, build=2.0s.
        laneProfile surfaces=16,386, artifactHeavy=3,559, ownerHeavy=2,253.
        focusedRelation relationOcc=4,825, spanPairs=290,683, localPairs=539,818,
        ownerFrames=4,825, buildFocusedRelationIndexes=12.7s.
        sideFocusedBound payloads=600, relationOcc=1,870, localPairs=123,609,
        ownerFrames=1,870, buildSideBoundPayloadIndex=1.9s.
        buildUnitIndex=3.4s, modelSeconds=91.6, totalSeconds=98.8.
        laneProbe: 외상매출금 S1.00/A0.00/O0.00, 매출채권 S0.63/A0.35/O0.01,
        대손충당금 S0.71/A0.00/O0.29, 복구충당금 S1.00/A0.00/O0.00.
        `외상매출금 -> 매출채권` accepted=True(score 1.119, cp 0.624), `매출액` 2순위는
        accepted=False. `현금성자산 -> 현금및현금성자산` accepted=True(score 2.308).
        `영업손익 -> 영업이익` accepted=True(score 0.198).
        `손실충당금 -> 대손충당금` accepted=True(score 0.115).
        `복구충당금 -> 대손충당금` 은 score 0.226 으로 accepted=False.
        `대출채권 -> 대손충당금` 은 score -0.134 로 accepted=False.
        `대출채권 -> 매출채권` 은 forbidden=-0.124 로 accepted=False.
        positiveHits=4/4, badAccepted=0/7, searchTop1=5/5, reliableSearch=5/5.

판정:
    성공/구조 개선. 1글자 좌표 atom 을 relay 후보에서 제외하고 bounded coordinate row 를 쓰자 4,000 기준
    relay build 는 V70 12.9s -> V76 2.0s, signatureStage relay 는 13.3s -> 2.4s 로 줄었다. buildSignatures 는
    41.2s -> 33.8s, totalSeconds 는 104.1s -> 98.8s 로 내려갔다. V66 의 100.4s 도 근소하게 넘었고,
    target/probe seed 없이 corpus-derived bridge 구조를 유지했다.

    품질은 positiveHits=4/4, badAccepted=0/7, searchTop1=5/5, reliableSearch=5/5 를 유지했다. 오염 점수도
    `복구충당금 -> 대손충당금` 은 V66 0.442/V70 0.285 -> V76 0.226 으로 더 낮아졌고,
    `대출채권 -> 대손충당금` 은 -0.134 를 유지했다. 결론적으로 1글자 좌표는 stem 수평선의 원자료로는
    남기되 relay 후보 생성에서는 너무 넓은 경험 fanout 이므로 2글자 이상 sparse row 가 맞다. 다음은 이 V76
    relay 구조를 유지한 채 focusedRelation 12.7s 와 raw 12.5s 중 하나를 줄이는 방향이 본진 투입에 가장 가깝다.
"""

from __future__ import annotations

import hashlib
import html
import math
import os
import re
import time
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
ALL_FILINGS_DIR = ROOT / "data" / "dart" / "allFilings"
DOCS_DIR = ROOT / "data" / "dart" / "docs"

MAX_FILES_PER_SOURCE = int(os.environ.get("DARTLAB_HORIZON_V76_MAX_FILES_PER_SOURCE", "30"))
MAX_RECORDS_PER_SOURCE = int(os.environ.get("DARTLAB_HORIZON_V76_MAX_RECORDS_PER_SOURCE", "700"))
MAX_UNITS = int(os.environ.get("DARTLAB_HORIZON_V76_MAX_UNITS", "8000"))
MAX_WINDOWS_PER_RECORD = int(os.environ.get("DARTLAB_HORIZON_V76_MAX_WINDOWS_PER_RECORD", "3"))
SIDE_MAX_FILES_PER_SOURCE = int(
    os.environ.get("DARTLAB_HORIZON_V76_SIDE_MAX_FILES_PER_SOURCE", str(max(20, MAX_FILES_PER_SOURCE)))
)
SIDE_MAX_RECORDS_PER_SOURCE = int(
    os.environ.get("DARTLAB_HORIZON_V76_SIDE_MAX_RECORDS_PER_SOURCE", str(max(600, MAX_RECORDS_PER_SOURCE)))
)
SIDE_MAX_UNITS = int(os.environ.get("DARTLAB_HORIZON_V76_SIDE_MAX_UNITS", "600"))
WINDOW_CHARS = int(os.environ.get("DARTLAB_HORIZON_V76_WINDOW_CHARS", "720"))
RADIUS = int(os.environ.get("DARTLAB_HORIZON_V76_RADIUS", "6"))
SKETCH_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_SKETCH_LIMIT", "32"))
SIGNATURE_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_SIGNATURE_LIMIT", "96"))
POSTING_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_POSTING_LIMIT", "1200"))
SEARCH_RELATION_POSTING_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_SEARCH_RELATION_POSTING_LIMIT", "2400"))
SEARCH_CANDIDATE_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_SEARCH_CANDIDATE_LIMIT", "420"))
ROUTE_MIN_SCORE = float(os.environ.get("DARTLAB_HORIZON_V76_ROUTE_MIN_SCORE", "0.075"))
ROUTE_MIN_EXPERIENCE = float(os.environ.get("DARTLAB_HORIZON_V76_ROUTE_MIN_EXPERIENCE", "0.018"))
COHORT_SUFFIX_MIN = int(os.environ.get("DARTLAB_HORIZON_V76_COHORT_SUFFIX_MIN", "2"))
COHORT_SUFFIX_MAX = int(os.environ.get("DARTLAB_HORIZON_V76_COHORT_SUFFIX_MAX", "4"))
CONTRAST_COMMON_RATIO = float(os.environ.get("DARTLAB_HORIZON_V76_CONTRAST_COMMON_RATIO", "0.34"))
CONTRAST_ACCEPT_MIN = float(os.environ.get("DARTLAB_HORIZON_V76_CONTRAST_ACCEPT_MIN", "0.010"))
RESONANCE_ACCEPT_MIN = float(os.environ.get("DARTLAB_HORIZON_V76_RESONANCE_ACCEPT_MIN", "0.030"))
COMPOUND_ASSOC_ACCEPT_MIN = float(os.environ.get("DARTLAB_HORIZON_V76_COMPOUND_ASSOC_ACCEPT_MIN", "0.045"))
LANE_MISMATCH_PENALTY = float(os.environ.get("DARTLAB_HORIZON_V76_LANE_MISMATCH_PENALTY", "0.18"))
LANE_ARTIFACT_PENALTY = float(os.environ.get("DARTLAB_HORIZON_V76_LANE_ARTIFACT_PENALTY", "0.10"))
ROUTE_ACCEPT_MARGIN_RATIO = float(os.environ.get("DARTLAB_HORIZON_V76_ROUTE_ACCEPT_MARGIN_RATIO", "0.42"))
ROUTE_ACCEPT_MARGIN_GAP = float(os.environ.get("DARTLAB_HORIZON_V76_ROUTE_ACCEPT_MARGIN_GAP", "0.060"))
SEARCH_EVIDENCE_MIN = float(os.environ.get("DARTLAB_HORIZON_V76_SEARCH_EVIDENCE_MIN", "0.34"))
SPAN_MAX_DISTANCE = int(os.environ.get("DARTLAB_HORIZON_V76_SPAN_MAX_DISTANCE", "160"))
FRAME_MAX_DISTANCE = int(os.environ.get("DARTLAB_HORIZON_V76_FRAME_MAX_DISTANCE", "180"))
FOCUSED_FRAME_DISTANCE = int(os.environ.get("DARTLAB_HORIZON_V76_FOCUSED_FRAME_DISTANCE", str(FRAME_MAX_DISTANCE * 2)))
TABLE_ROW_LEAK_EVIDENCE_CAP = float(os.environ.get("DARTLAB_HORIZON_V76_TABLE_ROW_LEAK_EVIDENCE_CAP", "0.18"))
TABLE_ROW_LEAK_SEARCH_PENALTY = float(os.environ.get("DARTLAB_HORIZON_V76_TABLE_ROW_LEAK_SEARCH_PENALTY", "8.0"))
ROLE_BOUND_EVIDENCE_CAP = float(os.environ.get("DARTLAB_HORIZON_V76_ROLE_BOUND_EVIDENCE_CAP", "0.48"))
ROLE_BOUND_SEARCH_PENALTY = float(os.environ.get("DARTLAB_HORIZON_V76_ROLE_BOUND_SEARCH_PENALTY", "5.0"))
RELIABLE_BOUND_MIN = float(os.environ.get("DARTLAB_HORIZON_V76_RELIABLE_BOUND_MIN", "0.55"))
WEAK_BOUND_MIN = float(os.environ.get("DARTLAB_HORIZON_V76_WEAK_BOUND_MIN", "0.34"))
RELIABLE_EVIDENCE_MIN = float(os.environ.get("DARTLAB_HORIZON_V76_RELIABLE_EVIDENCE_MIN", "0.70"))
SIDE_FALLBACK_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_SIDE_FALLBACK_LIMIT", "220"))
RAW_BRIDGE_MIN_SIM = float(os.environ.get("DARTLAB_HORIZON_V76_RAW_BRIDGE_MIN_SIM", "0.24"))
RAW_BRIDGE_MIN_SIZE = int(os.environ.get("DARTLAB_HORIZON_V76_RAW_BRIDGE_MIN_SIZE", "4"))
RAW_BRIDGE_MAX_SIZE = int(os.environ.get("DARTLAB_HORIZON_V76_RAW_BRIDGE_MAX_SIZE", "8"))
RAW_BRIDGE_MAX_TOKEN = int(os.environ.get("DARTLAB_HORIZON_V76_RAW_BRIDGE_MAX_TOKEN", "18"))
CORPUS_BRIDGE_SEED_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_SEED_LIMIT", "2400"))
CORPUS_BRIDGE_SEED_MIN_DF = int(os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_SEED_MIN_DF", "1"))
CORPUS_BRIDGE_GRAM_POSTING_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_GRAM_POSTING_LIMIT", "360"))
CORPUS_BRIDGE_NON_CONTAINMENT_MIN_SIM = float(
    os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_NON_CONTAINMENT_MIN_SIM", "0.46")
)
CORPUS_BRIDGE_RELATION_RADIUS = int(os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_RELATION_RADIUS", "9"))
CORPUS_BRIDGE_VALUE_RADIUS = int(os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_VALUE_RADIUS", "7"))
CORPUS_BRIDGE_MIN_EVIDENCE = float(os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_MIN_EVIDENCE", "0.55"))
CORPUS_BRIDGE_SUBSURFACE_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_CORPUS_BRIDGE_SUBSURFACE_LIMIT", "4"))
COHORT_CONTRAST_ATOM_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_COHORT_CONTRAST_ATOM_LIMIT", "48"))
RELAY_NEIGHBOR_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RELAY_NEIGHBOR_LIMIT", "6"))
RELAY_ATOM_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RELAY_ATOM_LIMIT", "16"))
RAW_PRUNE_XP_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RAW_PRUNE_XP_LIMIT", "96"))
RAW_PRUNE_HX_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RAW_PRUNE_HX_LIMIT", "96"))
RAW_PRUNE_EL_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RAW_PRUNE_EL_LIMIT", "48"))
RAW_PRUNE_OTHER_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RAW_PRUNE_OTHER_LIMIT", "32"))
RELAY_COMMON_ATOM_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RELAY_COMMON_ATOM_LIMIT", "40"))
RELAY_COMMON_RATIO = float(os.environ.get("DARTLAB_HORIZON_V76_RELAY_COMMON_RATIO", str(CONTRAST_COMMON_RATIO)))
RELAY_ROW_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RELAY_ROW_LIMIT", "160"))
RELAY_SPECIFIC_ROW_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_RELAY_SPECIFIC_ROW_LIMIT", "320"))
SIGNATURE_OCC_FULL_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_SIGNATURE_OCC_FULL_LIMIT", "8"))
SIGNATURE_OCC_BUDGET = int(os.environ.get("DARTLAB_HORIZON_V76_SIGNATURE_OCC_BUDGET", "48"))
SIGNATURE_OCC_BUCKETS = int(os.environ.get("DARTLAB_HORIZON_V76_SIGNATURE_OCC_BUCKETS", "12"))
SIGNATURE_OCC_RELATION_RADIUS = int(os.environ.get("DARTLAB_HORIZON_V76_SIGNATURE_OCC_RELATION_RADIUS", "8"))
SIGNATURE_OCC_VALUE_RADIUS = int(os.environ.get("DARTLAB_HORIZON_V76_SIGNATURE_OCC_VALUE_RADIUS", "6"))
SKETCH_OCC_FULL_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V76_SKETCH_OCC_FULL_LIMIT", "12"))
SKETCH_OCC_BUDGET = int(os.environ.get("DARTLAB_HORIZON_V76_SKETCH_OCC_BUDGET", "96"))
SKETCH_OCC_BUCKETS = int(os.environ.get("DARTLAB_HORIZON_V76_SKETCH_OCC_BUCKETS", "16"))

TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
VALUE_RE = re.compile(r"(?:\(?-?\d[\d,]*(?:\.\d+)?\)?\s*(?:백만원|억원|원|천원|%|배|주)?)")
FRAME_FENCE_RE = re.compile(r"(구\s*분|계정과목|설정률|단위\s*:|채권금액|합\s*계)")
CLAUSE_BOUNDARY_RE = re.compile(r"([.;。!?！？]|(?:습니다|였다|했다|하였다|됩니다|합니다)\s*)")
BOUND_RELATION_NOUN_RE = re.compile(r"(폭|률|율|액|분|요인|효과|추세|규모)")
ARTIFACT_HINT_RE = re.compile(
    r"(보고서|사업연|대규모법인|전화번호|팩스번호|공시|주식수|액면가|소유|증권|사채권|예탁증권|"
    r"결산기간|투자판단|흑자적자전환|손익구조|재무제표|기초자산|특정증권|파생결합)"
)
SENTENCE_VERB_RE = re.compile(r"(증가|감소|하였|되었|됩니다|합니다|영향|기인|따른|인한|개선|저하)")
OWNER_STOP_SUFFIXES = ("대비", "기준", "분기", "반기", "백만원", "억원", "천원", "비율", "금액")

MARKER_SUFFIXES = tuple(
    sorted(
        {
            "으로부터",
            "로부터",
            "에서는",
            "에게서",
            "까지",
            "부터",
            "으로",
            "에서",
            "에게",
            "보다",
            "처럼",
            "하고",
            "이며",
            "이고",
            "이다",
            "했다",
            "하였다",
            "하는",
            "하여",
            "해서",
            "한다",
            "된다",
            "됐다",
            "되며",
            "되는",
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "의",
            "에",
            "로",
            "과",
            "와",
            "도",
            "만",
        },
        key=len,
        reverse=True,
    )
)

TARGETS = ("매출채권", "재고자산", "차입금", "영업이익", "매출액", "현금및현금성자산", "대손충당금")
POSITIVE_PROBES = (
    ("외상매출금", "매출채권"),
    ("영업손익", "영업이익"),
    ("현금성자산", "현금및현금성자산"),
    ("손실충당금", "대손충당금"),
)
NEGATIVE_PROBES = (
    ("대출채권", "매출채권"),
    ("현금배당금", "현금및현금성자산"),
    ("당기순이익", "영업이익"),
    ("복구충당금", "대손충당금"),
    ("대출채권", "대손충당금"),
    ("현금성자산", "대손충당금"),
    ("당기순이익", "대손충당금"),
)
SEARCH_PROBES = (
    ("매출채권 증가", "매출채권", "increase"),
    ("외상매출금 감소", "매출채권", "decrease"),
    ("영업손익 감소", "영업이익", "decrease"),
    ("현금성자산 증가", "현금및현금성자산", "increase"),
    ("손실충당금 증가", "대손충당금", "increase"),
)
RELATIONS = (
    ("increase", ("증가", "상승", "확대", "성장", "늘", "증대", "개선")),
    ("decrease", ("감소", "하락", "축소", "줄", "저하")),
    ("delay", ("지연", "회수지연", "연체", "부실", "위험")),
)


def focusSurfaceFragments(values: set[str]) -> set[str]:
    fragments: set[str] = set()
    for raw in values:
        value = re.sub(r"[^가-힣A-Za-z0-9]", "", raw)
        if len(value) < 4:
            continue
        for size in range(4, min(7, len(value)) + 1):
            for index in range(0, len(value) - size + 1):
                fragments.add(value[index : index + size])
    return fragments


BASE_FOCUS_SURFACES = (
    set(TARGETS) | {surface for surface, _ in POSITIVE_PROBES} | {surface for surface, _ in NEGATIVE_PROBES}
)
FOCUS_TERMS = tuple(
    sorted(
        BASE_FOCUS_SURFACES
        | focusSurfaceFragments(BASE_FOCUS_SURFACES)
        | {term for _, terms in RELATIONS for term in terms}
        | {"기대신용손실", "손상", "채권", "손실", "대손"},
        key=lambda item: (-len(item), item),
    )
)
FOCUS_REGEX = "|".join(re.escape(term) for term in FOCUS_TERMS)
RELATION_REGEX = "|".join(re.escape(term) for _, terms in RELATIONS for term in terms)
RELATION_TERMS = tuple(sorted({term for _, terms in RELATIONS for term in terms}, key=lambda item: (-len(item), item)))
VALUE_MARKERS = {"원", "천원", "백만원", "억원", "%", "배", "주"}
STOP_STEMS = {
    "그리고",
    "또한",
    "또는",
    "대한",
    "관련",
    "해당",
    "경우",
    "보고서",
    "사업",
    "회사",
    "연결",
    "당사",
    "현재",
    "전기",
    "당기",
    "기말",
    "기초",
    "천원",
    "백만원",
}
BRIDGE_SEED_STOP_STEMS = STOP_STEMS | {
    "padding",
    "decoration",
    "있습니다",
    "있으며",
    "있고",
    "있다",
    "합니다",
    "됩니다",
    "입니다",
    "하였습니다",
    "되었습니다",
}
BRIDGE_SEED_STOP_SUFFIXES = ("습니다", "합니다", "됩니다", "입니다", "있으며", "있고", "있다", "하였다", "되었다")


@dataclass(frozen=True)
class Unit:
    unitId: int
    source: str
    ref: str
    text: str


@dataclass(frozen=True)
class SidePayload:
    sideId: int
    ref: str
    text: str


@dataclass(frozen=True)
class Occ:
    surface: str
    marker: str
    position: int
    lane: str = "sentence"


@dataclass
class Cache:
    unit: Unit
    stems: list[str]
    markers: list[str]
    occs: list[Occ]
    bridgeSurfaces: set[str]
    terms: set[str]
    lanes: list[str] | None = None


@dataclass
class HorizonTokenView:
    content: list[bool]
    markers: list[str]
    cells: list[tuple[str, ...]]
    lanes: list[str]


@dataclass
class SketchAtomView:
    cells: dict[str, str]
    selfAtoms: dict[str, tuple[str, ...]]
    neighborAtomHashes: dict[str, tuple[str, ...]]


@dataclass
class BridgeSeedIndex:
    seeds: tuple[str, ...]
    seedValues: frozenset[str]
    gramPostings: dict[str, tuple[str, ...]]
    seedGrams: dict[str, frozenset[str]]
    cache: dict[str, tuple[str, ...]]


@dataclass
class Model:
    units: list[Unit]
    caches: list[Cache]
    sidePayloads: list[SidePayload]
    sketches: dict[str, Counter[str]]
    signatures: dict[str, Counter[str]]
    coordPostings: dict[str, list[str]]
    unitSignatures: dict[int, Counter[str]]
    unitPostings: dict[str, list[int]]
    cohortAtomDf: dict[str, Counter[str]]
    cohortSurfaceCounts: Counter[str]
    coordGramDf: Counter[str]
    surfaceDf: Counter[str]
    surfacePairDf: Counter[tuple[str, str]]
    surfaceLaneProfiles: dict[str, tuple[float, float, float]]
    compoundGramPostings: dict[str, list[str]]
    relationSpanPostings: dict[tuple[str, str], list[int]]
    relationSpanScores: dict[tuple[int, str, str], float]
    relationFramePostings: dict[tuple[str, str], list[int]]
    relationFrameScores: dict[tuple[int, str, str], float]
    relationFrameLeaks: dict[tuple[int, str, str], float]
    relationBoundPostings: dict[tuple[str, str], list[int]]
    relationBoundScores: dict[tuple[int, str, str], float]
    sideRelationBoundPostings: dict[tuple[str, str], list[int]]
    sideRelationBoundScores: dict[tuple[int, str, str], float]


@lru_cache(maxsize=500_000)
def stableHash(value: str, size: int = 12) -> str:
    return hashlib.blake2b(value.encode("utf-8"), digest_size=8).hexdigest()[:size]


def cleanText(raw: object) -> str:
    return SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", "" if raw is None else str(raw)))).strip()


def splitStemMarker(token: str) -> tuple[str, str]:
    for suffix in MARKER_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            return token[: -len(suffix)], suffix
    return token, ""


@lru_cache(maxsize=200_000)
def normStem(value: str) -> str:
    stem, _ = splitStemMarker(value)
    return re.sub(r"[^가-힣A-Za-z0-9]", "", stem)


def isContentStem(stem: str) -> bool:
    return len(stem) >= 2 and stem not in STOP_STEMS and not stem.isdigit() and bool(re.search(r"[가-힣A-Za-z]", stem))


def isCorpusBridgeSeedCandidate(stem: str) -> bool:
    value = normStem(stem)
    if not isContentStem(value):
        return False
    if value in BRIDGE_SEED_STOP_STEMS:
        return False
    if not re.search(r"[가-힣]", value):
        return False
    if any(value.endswith(suffix) for suffix in BRIDGE_SEED_STOP_SUFFIXES):
        return False
    return True


def relationTokenLike(stem: str) -> bool:
    return any(term in stem for term in RELATION_TERMS)


def valueTokenLike(stem: str, marker: str) -> bool:
    return marker in VALUE_MARKERS or bool(re.search(r"\d", stem))


def unitLaneAt(text: str, start: int, size: int, stem: str, marker: str) -> str:
    left = max(0, start - 90)
    right = min(len(text), start + size + 90)
    window = text[left:right]
    relationLike = any(term in window for term in RELATION_TERMS)
    sentenceLike = bool(CLAUSE_BOUNDARY_RE.search(window) or SENTENCE_VERB_RE.search(window))
    if relationLike and sentenceLike and relationOwnerCandidate(stem):
        return "owner"

    artifactScore = 0
    if any(ch.isdigit() for ch in stem):
        artifactScore += 2
    if FRAME_FENCE_RE.search(window):
        artifactScore += 2
    if len(VALUE_RE.findall(window)) >= 2:
        artifactScore += 2
    if ARTIFACT_HINT_RE.search(window):
        artifactScore += 1
    if len(stem) >= 9 and not sentenceLike:
        artifactScore += 1
    if marker == "" and any(hint in stem for hint in ("또는", "여부", "보고서", "사업연", "법인", "주식", "증권")):
        artifactScore += 1

    if artifactScore >= 2 and not (relationLike and sentenceLike and artifactScore <= 2):
        return "artifact"
    if relationLike and relationOwnerCandidate(stem):
        return "owner"
    return "sentence"


def tokenLaneAt(
    stem: str,
    marker: str,
    position: int,
    relationPositions: list[int],
    valuePositions: list[int],
) -> str:
    relationDistance = nearestTokenDistance(position, relationPositions)
    valueDistance = nearestTokenDistance(position, valuePositions)
    relationNear = relationDistance is not None and relationDistance <= SIGNATURE_OCC_RELATION_RADIUS
    valueNear = valueDistance is not None and valueDistance <= SIGNATURE_OCC_VALUE_RADIUS

    if relationNear and relationOwnerCandidate(stem):
        return "owner"

    artifactScore = 0
    if any(ch.isdigit() for ch in stem):
        artifactScore += 2
    if valueNear:
        artifactScore += 1
    if ARTIFACT_HINT_RE.search(stem):
        artifactScore += 1
    if len(stem) >= 9 and not relationNear:
        artifactScore += 1
    if marker == "" and any(hint in stem for hint in ("또는", "여부", "보고서", "사업연", "법인", "주식", "증권")):
        artifactScore += 1

    if artifactScore >= 2:
        return "artifact"
    if relationNear and relationOwnerCandidate(stem):
        return "owner"
    return "sentence"


def nearestTokenDistance(position: int, positions: list[int]) -> int | None:
    if not positions:
        return None
    index = bisect_left(positions, position)
    best: int | None = None
    if index < len(positions):
        best = abs(positions[index] - position)
    if index:
        left = abs(position - positions[index - 1])
        best = left if best is None else min(best, left)
    return best


@lru_cache(maxsize=200_000)
def codePath(stem: str) -> str:
    return ".".join(f"{ord(ch):05d}" for ch in stem) + ".$"


def coordDecimal(stem: str, size: int = 24) -> str:
    return "0." + "".join(f"{ord(ch):05d}" for ch in normStem(stem))[:size]


@lru_cache(maxsize=200_000)
def coordAtoms(stem: str) -> frozenset[str]:
    value = normStem(stem)
    if not value:
        return frozenset()
    points = [f"{ord(ch):05d}" for ch in value]
    atoms = {f"cx:full:{stableHash(codePath(value))}"}
    for size in range(1, min(4, len(points)) + 1):
        atoms.add(f"cx:p{size}:{stableHash('.'.join(points[:size]))}")
        atoms.add(f"cx:s{size}:{stableHash('.'.join(points[-size:]))}")
    for size in range(1, min(4, len(value)) + 1):
        for index in range(0, len(value) - size + 1):
            atoms.add(f"cx:g{size}:{stableHash(codePath(value[index : index + size]))}")
    return frozenset(atoms)


@lru_cache(maxsize=200_000)
def coordCells(stem: str) -> tuple[str, ...]:
    cells = [atom.replace("cx:", "cc:", 1) for atom in sorted(coordAtoms(stem))]
    return tuple(cells[:12])


def meaningAtom(atom: str) -> bool:
    return atom.startswith(
        (
            "xp:",
            "el:",
            "hx:",
            "relay:xp",
            "relay:el",
            "relay:hx",
            "compoundProxy:xp",
            "compoundProxy:el",
            "compoundProxy:hx",
        )
    )


@lru_cache(maxsize=200_000)
def suffixCohortKeys(stem: str) -> tuple[str, ...]:
    value = normStem(stem)
    if len(value) <= COHORT_SUFFIX_MIN:
        return tuple()
    keys: list[str] = []
    for size in range(COHORT_SUFFIX_MIN, min(COHORT_SUFFIX_MAX, len(value) - 1) + 1):
        keys.append(f"sf:{size}:{stableHash(codePath(value[-size:]))}")
    return tuple(keys)


@lru_cache(maxsize=200_000)
def coordResonanceGrams(stem: str) -> frozenset[str]:
    value = normStem(stem)
    grams: set[str] = set()
    for size in range(1, min(4, len(value)) + 1):
        for index in range(0, len(value) - size + 1):
            grams.add(f"rg:{size}:{stableHash(codePath(value[index : index + size]))}")
    return frozenset(grams)


def longestCommonSuffixSize(left: str, right: str) -> int:
    leftValue = normStem(left)
    rightValue = normStem(right)
    size = 0
    for lch, rch in zip(reversed(leftValue), reversed(rightValue)):
        if lch != rch:
            break
        size += 1
    return size


def nonSuffixResonanceGrams(surface: str, target: str) -> tuple[set[str], set[str]]:
    suffixSize = longestCommonSuffixSize(surface, target)
    left = normStem(surface)
    right = normStem(target)
    if suffixSize >= COHORT_SUFFIX_MIN:
        left = left[:-suffixSize] or left
        right = right[:-suffixSize] or right
    return set(coordResonanceGrams(left)), set(coordResonanceGrams(right))


@lru_cache(maxsize=200_000)
def compoundGrams(stem: str) -> frozenset[str]:
    value = normStem(stem)
    grams: set[str] = set()
    for size in range(2, min(5, len(value)) + 1):
        for index in range(0, len(value) - size + 1):
            grams.add(f"cg:{size}:{stableHash(codePath(value[index : index + size]))}")
    return frozenset(grams)


def nonSuffixCompoundOverlap(surface: str, target: str) -> float:
    if longestCommonSuffixSize(surface, target) >= COHORT_SUFFIX_MIN:
        return 0.0
    left = compoundGrams(surface)
    right = compoundGrams(target)
    if not left or not right:
        return 0.0
    overlap = left & right
    if not overlap:
        return 0.0
    return len(overlap) / math.sqrt(len(left) * len(right))


def compoundSimilarity(surface: str, proxy: str) -> float:
    left = compoundGrams(surface)
    right = compoundGrams(proxy)
    if not left or not right:
        return 0.0
    overlap = left & right
    if len(overlap) < 2:
        return 0.0
    return len(overlap) / math.sqrt(len(left) * len(right))


def rawBridgeSeedMatch(surface: str, bridgeSeedIndex: BridgeSeedIndex) -> bool:
    value = normStem(surface)
    if len(value) < RAW_BRIDGE_MIN_SIZE or not isContentStem(value):
        return False
    grams = compoundGrams(value)
    if not grams:
        return False

    if value in bridgeSeedIndex.seedValues:
        return True

    candidateSeeds: set[str] = set()
    for gram in grams:
        candidateSeeds.update(bridgeSeedIndex.gramPostings.get(gram, ()))

    for seedValue in candidateSeeds:
        if seedValue == value:
            continue
        if value in seedValue or seedValue in value:
            return True
        seedGrams = bridgeSeedIndex.seedGrams.get(seedValue, frozenset())
        overlap = grams & seedGrams
        if len(overlap) >= 3:
            score = len(overlap) / math.sqrt(len(grams) * len(seedGrams))
            if score >= max(RAW_BRIDGE_MIN_SIM, CORPUS_BRIDGE_NON_CONTAINMENT_MIN_SIM):
                return True
    return False


def rawBridgeSubsurfaces(stem: str, bridgeSeedIndex: BridgeSeedIndex | None) -> tuple[str, ...]:
    value = normStem(stem)
    if bridgeSeedIndex is None:
        return tuple()
    cached = bridgeSeedIndex.cache.get(value)
    if cached is not None:
        return cached
    if len(value) < RAW_BRIDGE_MIN_SIZE + 1 or len(value) > RAW_BRIDGE_MAX_TOKEN:
        bridgeSeedIndex.cache[value] = tuple()
        return tuple()
    out: dict[str, tuple[int, int, str]] = {}
    maxSize = min(RAW_BRIDGE_MAX_SIZE, len(value))
    for size in range(RAW_BRIDGE_MIN_SIZE, maxSize + 1):
        for index in range(0, len(value) - size + 1):
            part = value[index : index + size]
            if part == value:
                continue
            if rawBridgeSeedMatch(part, bridgeSeedIndex):
                seedAnchor = 0 if part in bridgeSeedIndex.seedValues else 1
                out[part] = min(out.get(part, (9, 0, part)), (seedAnchor, -len(part), part))
    surfaces = tuple(part for _, _, part in sorted(out.values())[:CORPUS_BRIDGE_SUBSURFACE_LIMIT])
    bridgeSeedIndex.cache[value] = surfaces
    return surfaces


def buildCorpusBridgeSeedIndex(caches: list[Cache]) -> BridgeSeedIndex:
    surfaceDf: Counter[str] = Counter()
    surfaceTf: Counter[str] = Counter()
    evidenceDf: Counter[str] = Counter()
    evidenceTf: Counter[str] = Counter()
    relationEvidenceDf: Counter[str] = Counter()
    valueEvidenceDf: Counter[str] = Counter()
    for cache in caches:
        unitSurfaces = {occ.surface for occ in cache.occs if isContentStem(occ.surface)}
        surfaceDf.update(unitSurfaces)
        surfaceTf.update(occ.surface for occ in cache.occs if isContentStem(occ.surface))
        relationPositions = sorted(
            {index for index, stem in enumerate(cache.stems) if isContentStem(stem) and relationTokenLike(stem)}
        )
        valuePositions = sorted(
            {
                index
                for index, (stem, marker) in enumerate(zip(cache.stems, cache.markers))
                if valueTokenLike(stem, marker)
            }
        )
        evidenceSurfaces: set[str] = set()
        relationSurfaces: set[str] = set()
        valueSurfaces: set[str] = set()
        for occ in cache.occs:
            surface = occ.surface
            if not isCorpusBridgeSeedCandidate(surface):
                continue
            evidence = 0.0
            relationDistance = nearestTokenDistance(occ.position, relationPositions)
            if relationDistance is not None and relationDistance <= CORPUS_BRIDGE_RELATION_RADIUS:
                evidence += 2.6 * (1.0 - relationDistance / (CORPUS_BRIDGE_RELATION_RADIUS + 1.0))
                relationSurfaces.add(surface)
            valueDistance = nearestTokenDistance(occ.position, valuePositions)
            if valueDistance is not None and valueDistance <= CORPUS_BRIDGE_VALUE_RADIUS:
                evidence += 1.7 * (1.0 - valueDistance / (CORPUS_BRIDGE_VALUE_RADIUS + 1.0))
                valueSurfaces.add(surface)
            if occ.marker:
                evidence += 0.25
            if relationOwnerCandidate(surface):
                evidence += 0.45
            if evidence <= 0.0:
                continue
            evidenceTf[surface] += evidence
            evidenceSurfaces.add(surface)
        evidenceDf.update(evidenceSurfaces)
        relationEvidenceDf.update(relationSurfaces)
        valueEvidenceDf.update(valueSurfaces)

    candidates: list[tuple[float, int, int, str]] = []
    for surface, df in surfaceDf.items():
        value = normStem(surface)
        if value != surface:
            continue
        if df < CORPUS_BRIDGE_SEED_MIN_DF:
            continue
        if len(value) < RAW_BRIDGE_MIN_SIZE or len(value) > RAW_BRIDGE_MAX_TOKEN:
            continue
        if not isCorpusBridgeSeedCandidate(value):
            continue
        evidence = evidenceTf.get(value, 0.0)
        if evidence < CORPUS_BRIDGE_MIN_EVIDENCE:
            continue
        grams = compoundGrams(value)
        if not grams:
            continue
        tf = surfaceTf[value]
        score = (
            math.log1p(evidenceDf[value]) * 2.80
            + math.log1p(evidence) * 1.15
            + math.log1p(relationEvidenceDf[value]) * 0.75
            + math.log1p(valueEvidenceDf[value]) * 0.55
            + math.log1p(df) * 0.55
            + math.log1p(tf) * 0.10
            + min(len(value), 14) * 0.08
            + min(len(grams), 16) * 0.02
        )
        candidates.append((score, df, tf, value))

    selected = sorted(candidates, reverse=True)[:CORPUS_BRIDGE_SEED_LIMIT]
    seeds = tuple(value for _, _, _, value in selected)
    seedGrams = {seed: compoundGrams(seed) for seed in seeds}
    postings: dict[str, list[str]] = defaultdict(list)
    for seed in seeds:
        for gram in seedGrams[seed]:
            if len(postings[gram]) < CORPUS_BRIDGE_GRAM_POSTING_LIMIT:
                postings[gram].append(seed)
    topSample = ", ".join(seeds[:8])
    print(
        f"[bridgeSeeds] corpusSeeds={len(seeds)} candidates={len(candidates)} "
        f"evidenceSurfaces={len(evidenceDf)} minEvidence={CORPUS_BRIDGE_MIN_EVIDENCE} top={topSample}"
    )
    return BridgeSeedIndex(
        seeds,
        frozenset(seeds),
        {gram: tuple(values) for gram, values in postings.items()},
        seedGrams,
        {},
    )


def augmentCacheWithBridgeSurfaces(cache: Cache, bridgeSeedIndex: BridgeSeedIndex) -> Cache:
    occs = list(cache.occs)
    bridgeSurfaces: set[str] = set()
    for pos, stem in enumerate(cache.stems):
        if not isContentStem(stem):
            continue
        lane = cache.lanes[pos] if cache.lanes and pos < len(cache.lanes) else "sentence"
        for bridgeSurface in rawBridgeSubsurfaces(stem, bridgeSeedIndex):
            bridgeSurfaces.add(bridgeSurface)
            occs.append(Occ(bridgeSurface, "~", pos, lane))
    terms = set(cache.terms)
    terms.update(bridgeSurfaces)
    return Cache(cache.unit, cache.stems, cache.markers, occs, bridgeSurfaces, terms, cache.lanes)


def compoundProxySurfaces(surface: str, model: Model) -> list[tuple[float, str]]:
    scores: Counter[str] = Counter()
    for gram in compoundGrams(surface):
        for proxy in model.compoundGramPostings.get(gram, ())[:260]:
            if proxy == normStem(surface):
                continue
            score = compoundSimilarity(surface, proxy)
            if score >= 0.24:
                scores[proxy] = max(scores[proxy], score)
    return sorted(((score, proxy) for proxy, score in scores.items()), reverse=True)[:8]


def pairKey(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def buildSurfacePairIndex(caches: list[Cache]) -> tuple[Counter[str], Counter[tuple[str, str]]]:
    surfaceDf: Counter[str] = Counter()
    surfacePairDf: Counter[tuple[str, str]] = Counter()
    targetSet = {normStem(target) for target in TARGETS}
    focusedPairChecks = 0
    for cache in caches:
        surfaces = sorted({occ.surface for occ in cache.occs})
        surfaceDf.update(surfaces)
        targetSurfaces = [surface for surface in surfaces if surface in targetSet]
        if not targetSurfaces or len(surfaces) < 2:
            continue
        seenPairs: set[tuple[str, str]] = set()
        for target in targetSurfaces:
            for surface in surfaces:
                if surface == target:
                    continue
                key = pairKey(surface, target)
                if key in seenPairs:
                    continue
                seenPairs.add(key)
                surfacePairDf[key] += 1
                focusedPairChecks += 1
    print(f"[surfacePair] focusedTargets={len(targetSet)} targetPairChecks={focusedPairChecks}")
    return surfaceDf, surfacePairDf


def buildSurfaceLaneProfiles(caches: list[Cache]) -> dict[str, tuple[float, float, float]]:
    laneCounts: dict[str, Counter[str]] = defaultdict(Counter)
    for cache in caches:
        for occ in cache.occs:
            laneCounts[occ.surface][occ.lane] += 1

    profiles: dict[str, tuple[float, float, float]] = {}
    for surface, counts in laneCounts.items():
        total = sum(counts.values())
        if total <= 0:
            continue
        profiles[surface] = (
            counts["sentence"] / total,
            counts["artifact"] / total,
            counts["owner"] / total,
        )

    artifactHeavy = sum(1 for profile in profiles.values() if profile[1] >= 0.35)
    ownerHeavy = sum(1 for profile in profiles.values() if profile[2] >= 0.35)
    print(f"[laneProfile] surfaces={len(profiles)} artifactHeavy={artifactHeavy} ownerHeavy={ownerHeavy}")
    return profiles


def buildCompoundGramPostings(surfaces: list[str]) -> dict[str, list[str]]:
    postings: dict[str, list[str]] = defaultdict(list)
    for surface in sorted(surfaces):
        for gram in compoundGrams(surface):
            postings[gram].append(surface)
    return dict(postings)


def directPairAssociation(surface: str, target: str, model: Model) -> float:
    pairCount = model.surfacePairDf.get(pairKey(normStem(surface), normStem(target)), 0)
    if pairCount <= 0:
        return 0.0
    leftDf = max(1, model.surfaceDf.get(normStem(surface), 0))
    rightDf = max(1, model.surfaceDf.get(normStem(target), 0))
    total = max(1, len(model.caches))
    pmi = math.log(1.0 + (pairCount * total) / math.sqrt(leftDf * rightDf))
    support = math.log1p(pairCount)
    return pmi * support / 8.0


def compoundAssociation(surface: str, target: str, model: Model) -> float:
    overlap = nonSuffixCompoundOverlap(surface, target)
    if overlap <= 0:
        return 0.0
    surfaceGrams = compoundGrams(surface)
    targetGrams = compoundGrams(target)
    shared = surfaceGrams & targetGrams
    querySpecific = surfaceGrams - shared
    targetSpecific = targetGrams - shared
    proxyScores: list[float] = []
    for gram in sorted(shared):
        for proxy in model.compoundGramPostings.get(gram, ())[:260]:
            if proxy in {normStem(surface), normStem(target)}:
                continue
            proxyGrams = compoundGrams(proxy)
            if not (querySpecific & proxyGrams):
                continue
            if targetSpecific and not (targetSpecific & proxyGrams):
                continue
            proxyOverlap = nonSuffixCompoundOverlap(surface, proxy)
            if proxyOverlap < 0.18:
                continue
            association = directPairAssociation(proxy, target, model)
            if association <= 0:
                continue
            proxyScores.append(overlap * proxyOverlap * association * 0.62)
    for proxySimilarity, proxy in compoundProxySurfaces(surface, model):
        proxyGrams = compoundGrams(proxy)
        if not (querySpecific & proxyGrams):
            continue
        proxyTargetOverlap = nonSuffixCompoundOverlap(proxy, target)
        if proxyTargetOverlap <= 0:
            continue
        association = directPairAssociation(proxy, target, model)
        if association <= 0:
            continue
        proxyScores.append(overlap * proxySimilarity * proxyTargetOverlap * association * 2.10)
    proxy = sum(sorted(proxyScores, reverse=True)[:4])
    return proxy


def hasRawCompoundBridge(surface: str, model: Model) -> bool:
    return any(compoundAssociation(surface, target, model) >= COMPOUND_ASSOC_ACCEPT_MIN * 0.35 for target in TARGETS)


def buildContrastIndexes(
    signatures: dict[str, Counter[str]],
) -> tuple[dict[str, Counter[str]], Counter[str], Counter[str]]:
    cohortAtomDf: dict[str, Counter[str]] = defaultdict(Counter)
    cohortSurfaceCounts: Counter[str] = Counter()
    coordGramDf: Counter[str] = Counter()
    rawAtomUpdates = 0
    for surface, signature in signatures.items():
        for gram in coordResonanceGrams(surface):
            coordGramDf[gram] += 1
        keys = suffixCohortKeys(surface)
        if not keys:
            continue
        atoms = {atom for atom, _ in signature.most_common(COHORT_CONTRAST_ATOM_LIMIT) if meaningAtom(atom)}
        rawAtomUpdates += len(atoms) * len(keys)
        for key in keys:
            cohortSurfaceCounts[key] += 1
            cohortAtomDf[key].update(atoms)
    commonAtomDf: dict[str, Counter[str]] = {}
    commonAtoms = 0
    for key, counter in cohortAtomDf.items():
        surfaceCount = cohortSurfaceCounts.get(key, 0)
        if surfaceCount <= 1:
            continue
        common = Counter(
            {atom: count for atom, count in counter.items() if count / surfaceCount >= CONTRAST_COMMON_RATIO}
        )
        if common:
            commonAtomDf[key] = common
            commonAtoms += len(common)
    print(
        f"[contrastPrune] atomLimit={COHORT_CONTRAST_ATOM_LIMIT} rawUpdates={rawAtomUpdates} commonAtoms={commonAtoms}"
    )
    return commonAtomDf, cohortSurfaceCounts, coordGramDf


def cohortCommonRatio(surface: str, atom: str, model: Model) -> float:
    ratios: list[float] = []
    for key in suffixCohortKeys(surface):
        surfaceCount = model.cohortSurfaceCounts.get(key, 0)
        if surfaceCount <= 1:
            continue
        ratios.append(model.cohortAtomDf.get(key, Counter()).get(atom, 0) / surfaceCount)
    return max(ratios) if ratios else 0.0


def contrastSignature(surface: str, signature: Counter[str], model: Model) -> Counter[str]:
    out: Counter[str] = Counter()
    for atom, weight in signature.items():
        if not meaningAtom(atom):
            continue
        ratio = cohortCommonRatio(surface, atom, model)
        if ratio >= CONTRAST_COMMON_RATIO:
            out[atom] += weight * 0.10
        else:
            out[atom] += weight * (1.15 - ratio)
    return out


def coordResonance(surface: str, target: str, model: Model) -> float:
    left, right = nonSuffixResonanceGrams(surface, target)
    if not left or not right:
        return 0.0
    universe = max(1, len(model.signatures))
    overlap = left & right
    if not overlap:
        return 0.0

    def gramWeight(gram: str) -> float:
        return math.log(1.0 + universe / (1.0 + model.coordGramDf.get(gram, 0)))

    numerator = sum(gramWeight(gram) for gram in overlap)
    leftNorm = math.sqrt(sum(gramWeight(gram) ** 2 for gram in left))
    rightNorm = math.sqrt(sum(gramWeight(gram) ** 2 for gram in right))
    if leftNorm <= 0 or rightNorm <= 0:
        return 0.0
    return numerator / (leftNorm * rightNorm)


def relKeys(text: str) -> set[str]:
    return {f"rel:{name}" for name, terms in RELATIONS if any(term in text for term in terms)}


def tokenize(unit: Unit) -> Cache:
    stems: list[str] = []
    markers: list[str] = []
    lanes: list[str] = []
    occs: list[Occ] = []
    contentFlags: list[bool] = []
    for match in TOKEN_RE.finditer(unit.text):
        raw = match.group(0)
        stem, marker = splitStemMarker(raw)
        stem = normStem(stem)
        isContent = isContentStem(stem)
        stems.append(stem)
        markers.append(marker)
        contentFlags.append(isContent)
    relationPositions = sorted(
        index for index, stem in enumerate(stems) if contentFlags[index] and relationTokenLike(stem)
    )
    valuePositions = sorted(
        index for index, (stem, marker) in enumerate(zip(stems, markers)) if valueTokenLike(stem, marker)
    )
    for pos, (stem, marker, isContent) in enumerate(zip(stems, markers, contentFlags)):
        lane = tokenLaneAt(stem, marker, pos, relationPositions, valuePositions) if isContent else "sentence"
        lanes.append(lane)
        if isContent:
            occs.append(Occ(stem, marker, pos, lane))
    terms = set(TOKEN_RE.findall(unit.text)) | relKeys(unit.text)
    return Cache(unit, stems, markers, occs, set(), terms, lanes)


def windows(raw: object) -> list[str]:
    text = cleanText(raw)
    if not text:
        return []
    hits: list[int] = []
    for term in FOCUS_TERMS:
        start = 0
        while len(hits) < MAX_WINDOWS_PER_RECORD * 10:
            index = text.find(term, start)
            if index < 0:
                break
            hits.append(index)
            start = index + max(1, len(term))
    out: list[str] = []
    seen: set[tuple[int, int]] = set()
    half = WINDOW_CHARS // 2
    for index in sorted(set(hits)):
        left = max(0, index - half)
        right = min(len(text), index + half)
        key = (left // 80, right // 80)
        if key in seen:
            continue
        seen.add(key)
        chunk = text[left:right].strip()
        if len(chunk) >= 24:
            out.append(chunk)
        if len(out) >= MAX_WINDOWS_PER_RECORD:
            break
    return out


def parquetRows(source: str, folder: Path):
    files = sorted(folder.glob("*.parquet")) if source == "allFilings" else sorted(folder.rglob("*.parquet"))
    for path in files[:MAX_FILES_PER_SOURCE]:
        schema = set(pl.scan_parquet(str(path)).collect_schema().names())
        if source == "allFilings":
            cols = [col for col in ("stock_code", "rcept_no", "report_nm", "content_raw") if col in schema]
            textCol = "content_raw"
        else:
            cols = [
                col
                for col in (
                    "stock_code",
                    "rcept_no",
                    "report_type",
                    "section_title",
                    "section_content_mixed",
                    "section_content",
                )
                if col in schema
            ]
            textCol = "section_content_mixed" if "section_content_mixed" in cols else "section_content"
        if textCol not in cols:
            continue
        frame = (
            pl.scan_parquet(str(path))
            .select(cols)
            .filter(pl.col(textCol).fill_null("").str.contains(FOCUS_REGEX))
            .limit(MAX_RECORDS_PER_SOURCE)
            .collect()
        )
        for row in frame.iter_rows(named=True):
            yield row, textCol


def sideParquetRows(source: str, folder: Path):
    files = sorted(folder.glob("*.parquet")) if source == "allFilings" else sorted(folder.rglob("*.parquet"))
    for path in files[:SIDE_MAX_FILES_PER_SOURCE]:
        schema = set(pl.scan_parquet(str(path)).collect_schema().names())
        if source == "allFilings":
            cols = [col for col in ("stock_code", "rcept_no", "report_nm", "content_raw") if col in schema]
            textCol = "content_raw"
        else:
            cols = [
                col
                for col in (
                    "stock_code",
                    "rcept_no",
                    "report_type",
                    "section_title",
                    "section_content_mixed",
                    "section_content",
                )
                if col in schema
            ]
            textCol = "section_content_mixed" if "section_content_mixed" in cols else "section_content"
        if textCol not in cols:
            continue
        frame = (
            pl.scan_parquet(str(path))
            .select(cols)
            .filter(pl.col(textCol).fill_null("").str.contains(FOCUS_REGEX))
            .filter(pl.col(textCol).fill_null("").str.contains(RELATION_REGEX))
            .limit(SIDE_MAX_RECORDS_PER_SOURCE)
            .collect()
        )
        for row in frame.iter_rows(named=True):
            yield row, textCol


def collectUnits() -> list[Unit]:
    units: list[Unit] = []
    counts: Counter[str] = Counter()
    perSource = max(1, math.ceil(MAX_UNITS / 2))
    started = time.perf_counter()
    for source, folder in (("allFilings", ALL_FILINGS_DIR), ("docs", DOCS_DIR)):
        for row, textCol in parquetRows(source, folder):
            title = row.get("report_nm") or row.get("section_title") or row.get("report_type") or ""
            ref = f"{source}:{row.get('stock_code') or ''}:{row.get('rcept_no') or ''}:{title}"
            for chunk in windows(row.get(textCol)):
                units.append(Unit(len(units), source, ref, chunk))
                counts[source] += 1
                if len(units) >= MAX_UNITS or counts[source] >= perSource:
                    break
            if len(units) >= MAX_UNITS or counts[source] >= perSource:
                break
    print(f"[collect] units={len(units)} sourceCounts={dict(counts)} seconds={time.perf_counter() - started:.1f}")
    return units


def collectSidePayloads(seenTexts: set[str]) -> list[SidePayload]:
    payloads: list[SidePayload] = []
    counts: Counter[str] = Counter()
    perSource = max(1, math.ceil(SIDE_MAX_UNITS / 2))
    started = time.perf_counter()
    for source, folder in (("allFilings", ALL_FILINGS_DIR), ("docs", DOCS_DIR)):
        for row, textCol in sideParquetRows(source, folder):
            title = row.get("report_nm") or row.get("section_title") or row.get("report_type") or ""
            ref = f"side:{source}:{row.get('stock_code') or ''}:{row.get('rcept_no') or ''}:{title}"
            for chunk in windows(row.get(textCol)):
                if not relKeys(chunk):
                    continue
                key = stableHash(chunk, 16)
                if key in seenTexts:
                    continue
                seenTexts.add(key)
                payloads.append(SidePayload(len(payloads), ref, chunk))
                counts[source] += 1
                if len(payloads) >= SIDE_MAX_UNITS or counts[source] >= perSource:
                    break
            if len(payloads) >= SIDE_MAX_UNITS or counts[source] >= perSource:
                break
    print(
        f"[sideCollect] payloads={len(payloads)} sourceCounts={dict(counts)} seconds={time.perf_counter() - started:.1f}"
    )
    return payloads


def horizonAtoms(pos: int, stems: list[str], markers: list[str]) -> set[str]:
    atoms = {f"hx:selfMarker:{markers[pos] if pos < len(markers) and markers[pos] else '_'}"}
    ordered: list[tuple[int, str]] = []
    for index in range(max(0, pos - RADIUS), min(len(stems), pos + RADIUS + 1)):
        if index == pos or not isContentStem(stems[index]):
            continue
        dist = index - pos
        side = "L" if dist < 0 else "R"
        bucket = min(abs(dist), 4)
        cells = coordCells(stems[index])
        for cell in cells[:8]:
            atoms.add(f"hx:n:{side}:{bucket}:{cell}")
        atoms.add(f"hx:m:{side}:{bucket}:{markers[index] if index < len(markers) and markers[index] else '_'}")
        ordered.append((dist, cells[0] if cells else "_"))
    left = [cell for dist, cell in sorted(ordered) if dist < 0]
    right = [cell for dist, cell in sorted(ordered) if dist > 0]
    if left and right:
        atoms.add(f"hx:lr:{left[-1]}>{right[0]}")
    return atoms


def buildHorizonTokenViews(caches: list[Cache]) -> dict[int, HorizonTokenView]:
    views: dict[int, HorizonTokenView] = {}
    laneCounts: Counter[str] = Counter()
    for cache in caches:
        content = [isContentStem(stem) for stem in cache.stems]
        markerCells = [marker if marker else "_" for marker in cache.markers]
        cells = [tuple(coordCells(stem)) if isContent else tuple() for stem, isContent in zip(cache.stems, content)]
        lanes = cache.lanes if cache.lanes is not None else ["sentence"] * len(cache.stems)
        laneCounts.update(lanes)
        views[cache.unit.unitId] = HorizonTokenView(content, markerCells, cells, lanes)
    print(
        f"[horizonView] caches={len(views)} tokens={sum(len(view.content) for view in views.values())} "
        f"lanes={dict(laneCounts)}"
    )
    return views


def horizonAtomsFromView(pos: int, view: HorizonTokenView) -> set[str]:
    lane = view.lanes[pos] if pos < len(view.lanes) else "sentence"
    atoms = {
        f"hx:selfMarker:{view.markers[pos] if pos < len(view.markers) else '_'}",
    }
    leftNearest = ""
    rightNearest = ""
    for index in range(max(0, pos - RADIUS), min(len(view.content), pos + RADIUS + 1)):
        if index == pos or not view.content[index]:
            continue
        dist = index - pos
        side = "L" if dist < 0 else "R"
        bucket = min(abs(dist), 4)
        cells = view.cells[index]
        for cell in cells[:8]:
            atoms.add(f"hx:n:{side}:{bucket}:{cell}")
        atoms.add(f"hx:m:{side}:{bucket}:{view.markers[index] if index < len(view.markers) else '_'}")
        firstCell = cells[0] if cells else "_"
        if dist < 0:
            leftNearest = firstCell
        elif not rightNearest:
            rightNearest = firstCell
    if leftNearest and rightNearest:
        atoms.add(f"hx:lr:{leftNearest}>{rightNearest}")
    return atoms


def cachedHorizonAtoms(
    cache: Cache,
    pos: int,
    horizonAtomCache: dict[tuple[int, int], set[str]],
    horizonTokenViews: dict[int, HorizonTokenView],
    stats: Counter[str] | None = None,
) -> set[str]:
    key = (cache.unit.unitId, pos)
    cached = horizonAtomCache.get(key)
    if cached is not None:
        if stats is not None:
            stats["hit"] += 1
        return cached
    atoms = horizonAtomsFromView(pos, horizonTokenViews[cache.unit.unitId])
    horizonAtomCache[key] = atoms
    if stats is not None:
        stats["miss"] += 1
    return atoms


def buildSketches(
    caches: list[Cache],
    horizonAtomCache: dict[tuple[int, int], set[str]],
    horizonTokenViews: dict[int, HorizonTokenView],
) -> dict[str, Counter[str]]:
    started = time.perf_counter()
    raw: dict[str, Counter[str]] = defaultdict(Counter)
    stats: Counter[str] = Counter()
    sampledOccs = selectSketchOccurrences(caches)
    sampled = time.perf_counter()
    for cache, occ in sampledOccs:
        raw[occ.surface].update(cachedHorizonAtoms(cache, occ.position, horizonAtomCache, horizonTokenViews, stats))
    rawBuilt = time.perf_counter()
    df: Counter[str] = Counter()
    for counter in raw.values():
        df.update(counter.keys())
    total = max(1, len(raw))
    sketches: dict[str, Counter[str]] = {}
    for stem, counter in raw.items():
        rows = []
        for atom, count in counter.items():
            rows.append((math.sqrt(count) * math.log(1.0 + total / (1.0 + df[atom])), atom))
        selected = Counter({atom: score for score, atom in sorted(rows, reverse=True)[:SKETCH_LIMIT]})
        if selected:
            sketches[stem] = selected
    print(
        f"[sketch] stems={len(sketches)} raw={len(raw)} "
        f"horizonMiss={stats['miss']} horizonHit={stats['hit']} "
        f"sample={sampled - started:.1f}s raw={rawBuilt - sampled:.1f}s"
    )
    return sketches


def sketchCell(stem: str, sketches: dict[str, Counter[str]]) -> str:
    if stem in sketches:
        atom, _ = sketches[stem].most_common(1)[0]
        return f"sk:{stableHash(atom)}"
    return coldSketchCell(stem)


@lru_cache(maxsize=200_000)
def coldSketchCell(stem: str) -> str:
    return f"sk:cold:{stableHash(codePath(stem))}"


def buildSketchAtomView(sketches: dict[str, Counter[str]]) -> SketchAtomView:
    cells: dict[str, str] = {}
    selfAtoms: dict[str, tuple[str, ...]] = {}
    neighborAtomHashes: dict[str, tuple[str, ...]] = {}
    for stem, sketch in sketches.items():
        common = sketch.most_common(6)
        if not common:
            continue
        cells[stem] = f"sk:{stableHash(common[0][0])}"
        selfAtoms[stem] = tuple(f"xp:self:{stableHash(atom)}" for atom, _ in common)
        neighborAtomHashes[stem] = tuple(stableHash(atom) for atom, _ in common[:4])
    return SketchAtomView(cells, selfAtoms, neighborAtomHashes)


def lineAtoms(
    pos: int, stems: list[str], markers: list[str], lanes: list[str] | None, sketchView: SketchAtomView
) -> set[str]:
    atoms: set[str] = set()
    stem = stems[pos]
    atoms.update(sketchView.selfAtoms.get(stem, ()))
    cells: dict[int, str] = {}
    for index in range(max(0, pos - RADIUS), min(len(stems), pos + RADIUS + 1)):
        neighborStem = stems[index]
        if not isContentStem(neighborStem):
            continue
        cells[index] = sketchView.cells.get(neighborStem, coldSketchCell(neighborStem))
        if index == pos:
            continue
        dist = index - pos
        side = "L" if dist < 0 else "R"
        bucket = min(abs(dist), 4)
        for atomHash in sketchView.neighborAtomHashes.get(neighborStem, ()):
            atoms.add(f"xp:n:{side}:{bucket}:{atomHash}")
    for start in range(pos - 2, pos + 1):
        idxs = [start, start + 1, start + 2]
        if all(index in cells for index in idxs):
            atoms.add(
                f"el:tri:{'.'.join(str(index - pos) for index in idxs)}:{'>'.join(cells[index] for index in idxs)}"
            )
    if pos - 1 in cells and pos in cells and pos + 1 in cells:
        atoms.add(f"el:lr:{cells[pos - 1]}>{cells[pos]}>{cells[pos + 1]}")
    return atoms


def relationTokenPositions(cache: Cache) -> list[int]:
    relTerms = tuple(term for _, terms in RELATIONS for term in terms)
    return [index for index, stem in enumerate(cache.stems) if any(term in stem for term in relTerms)]


def valueTokenPositions(cache: Cache) -> list[int]:
    return [index for index, stem in enumerate(cache.stems) if any(ch.isdigit() for ch in stem)]


def nearDistance(position: int, positions: list[int], radius: int) -> int | None:
    best: int | None = None
    for other in positions:
        distance = abs(other - position)
        if distance > radius:
            continue
        if best is None or distance < best:
            best = distance
    return best


def signatureOccurrenceScore(
    cache: Cache,
    occ: Occ,
    relationPositions: list[int],
    valuePositions: list[int],
) -> tuple[float, bool, bool, bool]:
    relationDistance = nearDistance(occ.position, relationPositions, SIGNATURE_OCC_RELATION_RADIUS)
    valueDistance = nearDistance(occ.position, valuePositions, SIGNATURE_OCC_VALUE_RADIUS)
    isBridge = occ.marker == "~"
    score = min(len(normStem(occ.surface)), 16) * 0.03
    if isBridge:
        score += 12.0
    if relationDistance is not None:
        score += 9.0 - relationDistance * 0.55
    if valueDistance is not None:
        score += 5.0 - valueDistance * 0.45
    if occ.marker and occ.marker != "~":
        score += 1.4
    if cache.terms & {f"rel:{name}" for name, _ in RELATIONS}:
        score += 0.4
    return score, isBridge, relationDistance is not None, valueDistance is not None


def occurrenceBucket(cache: Cache, occ: Occ, bucketCount: int = SIGNATURE_OCC_BUCKETS) -> tuple[int, int]:
    buckets = max(1, bucketCount)
    tokenBucket = min(buckets - 1, int(occ.position * buckets / max(1, len(cache.stems))))
    return cache.unit.unitId % buckets, tokenBucket


@lru_cache(maxsize=200_000)
def selfEchoCompoundSurface(surface: str) -> bool:
    value = normStem(surface)
    if len(value) < 6:
        return False
    if "및" in value:
        return True
    for size in (2, 3):
        grams = [value[index : index + size] for index in range(0, len(value) - size + 1)]
        if len(grams) != len(set(grams)):
            return True
    return False


def selectSketchOccurrences(caches: list[Cache]) -> list[tuple[Cache, Occ]]:
    grouped: dict[str, list[tuple[float, int, int, tuple[int, int], Cache, Occ, bool, bool, bool]]] = defaultdict(list)
    for cache in caches:
        relationPositions = relationTokenPositions(cache)
        valuePositions = valueTokenPositions(cache)
        for occ in cache.occs:
            score, isBridge, nearRelation, nearValue = signatureOccurrenceScore(
                cache, occ, relationPositions, valuePositions
            )
            grouped[occ.surface].append(
                (
                    score,
                    cache.unit.unitId,
                    occ.position,
                    occurrenceBucket(cache, occ, SKETCH_OCC_BUCKETS),
                    cache,
                    occ,
                    isBridge,
                    nearRelation,
                    nearValue,
                )
            )

    selectedRows: list[tuple[float, int, int, tuple[int, int], Cache, Occ, bool, bool, bool]] = []
    totalOccs = 0
    limitedSurfaces = 0
    for rows in grouped.values():
        totalOccs += len(rows)
        if len(rows) <= SKETCH_OCC_FULL_LIMIT or selfEchoCompoundSurface(rows[0][5].surface):
            selectedRows.extend(rows)
            continue
        limitedSurfaces += 1
        ordered = sorted(rows, key=lambda row: (-row[0], row[1], row[2]))
        chosen: list[tuple[float, int, int, tuple[int, int], Cache, Occ, bool, bool, bool]] = []
        chosenKeys: set[tuple[int, int, str]] = set()
        usedBuckets: set[tuple[int, int]] = set()
        for row in ordered:
            key = (row[1], row[2], row[5].marker)
            if row[3] in usedBuckets or key in chosenKeys:
                continue
            chosen.append(row)
            chosenKeys.add(key)
            usedBuckets.add(row[3])
            if len(chosen) >= SKETCH_OCC_BUDGET:
                break
        if len(chosen) < SKETCH_OCC_BUDGET:
            for row in ordered:
                key = (row[1], row[2], row[5].marker)
                if key in chosenKeys:
                    continue
                chosen.append(row)
                chosenKeys.add(key)
                if len(chosen) >= SKETCH_OCC_BUDGET:
                    break
        selectedRows.extend(chosen)

    selectedRows.sort(key=lambda row: (row[1], row[2], row[5].surface, row[5].marker))
    bridgeKept = sum(1 for row in selectedRows if row[6])
    relationKept = sum(1 for row in selectedRows if row[7])
    valueKept = sum(1 for row in selectedRows if row[8])
    laneKept = Counter(row[5].lane for row in selectedRows)
    print(
        f"[sketchSample] surfaces={len(grouped)} occs={totalOccs}->{len(selectedRows)} "
        f"limited={limitedSurfaces} budget={SKETCH_OCC_BUDGET} fullLimit={SKETCH_OCC_FULL_LIMIT} "
        f"bridge={bridgeKept} relation={relationKept} value={valueKept} "
        f"lanes={dict(laneKept)}"
    )
    return [(row[4], row[5]) for row in selectedRows]


def selectSignatureOccurrences(caches: list[Cache]) -> list[tuple[Cache, Occ]]:
    grouped: dict[str, list[tuple[float, int, int, tuple[int, int], Cache, Occ, bool, bool, bool]]] = defaultdict(list)
    for cache in caches:
        relationPositions = relationTokenPositions(cache)
        valuePositions = valueTokenPositions(cache)
        for occ in cache.occs:
            score, isBridge, nearRelation, nearValue = signatureOccurrenceScore(
                cache, occ, relationPositions, valuePositions
            )
            grouped[occ.surface].append(
                (
                    score,
                    cache.unit.unitId,
                    occ.position,
                    occurrenceBucket(cache, occ),
                    cache,
                    occ,
                    isBridge,
                    nearRelation,
                    nearValue,
                )
            )

    selectedRows: list[tuple[float, int, int, tuple[int, int], Cache, Occ, bool, bool, bool]] = []
    totalOccs = 0
    limitedSurfaces = 0
    for rows in grouped.values():
        totalOccs += len(rows)
        if len(rows) <= SIGNATURE_OCC_FULL_LIMIT:
            selectedRows.extend(rows)
            continue
        limitedSurfaces += 1
        ordered = sorted(rows, key=lambda row: (-row[0], row[1], row[2]))
        chosen: list[tuple[float, int, int, tuple[int, int], Cache, Occ, bool, bool, bool]] = []
        chosenKeys: set[tuple[int, int, str]] = set()
        usedBuckets: set[tuple[int, int]] = set()
        for row in ordered:
            key = (row[1], row[2], row[5].marker)
            if row[3] in usedBuckets or key in chosenKeys:
                continue
            chosen.append(row)
            chosenKeys.add(key)
            usedBuckets.add(row[3])
            if len(chosen) >= SIGNATURE_OCC_BUDGET:
                break
        if len(chosen) < SIGNATURE_OCC_BUDGET:
            for row in ordered:
                key = (row[1], row[2], row[5].marker)
                if key in chosenKeys:
                    continue
                chosen.append(row)
                chosenKeys.add(key)
                if len(chosen) >= SIGNATURE_OCC_BUDGET:
                    break
        selectedRows.extend(chosen)

    selectedRows.sort(key=lambda row: (row[1], row[2], row[5].surface, row[5].marker))
    bridgeKept = sum(1 for row in selectedRows if row[6])
    relationKept = sum(1 for row in selectedRows if row[7])
    valueKept = sum(1 for row in selectedRows if row[8])
    laneKept = Counter(row[5].lane for row in selectedRows)
    print(
        f"[occSample] surfaces={len(grouped)} occs={totalOccs}->{len(selectedRows)} "
        f"limited={limitedSurfaces} budget={SIGNATURE_OCC_BUDGET} fullLimit={SIGNATURE_OCC_FULL_LIMIT} "
        f"bridge={bridgeKept} relation={relationKept} value={valueKept} "
        f"lanes={dict(laneKept)}"
    )
    return [(row[4], row[5]) for row in selectedRows]


def signatureRawLane(atom: str) -> str:
    if atom.startswith("xp:"):
        return "xp"
    if atom.startswith("hx:"):
        return "hx"
    if atom.startswith("el:"):
        return "el"
    if atom.startswith("cx:"):
        return "cx"
    return "other"


def pruneRawSignatureCounters(raw: dict[str, Counter[str]]) -> dict[str, Counter[str]]:
    limits = {
        "xp": RAW_PRUNE_XP_LIMIT,
        "hx": RAW_PRUNE_HX_LIMIT,
        "el": RAW_PRUNE_EL_LIMIT,
        "other": RAW_PRUNE_OTHER_LIMIT,
    }
    beforeAtoms = 0
    afterAtoms = 0
    laneKept: Counter[str] = Counter()
    pruned: dict[str, Counter[str]] = {}
    for surface, counter in raw.items():
        beforeAtoms += len(counter)
        selected: Counter[str] = Counter()
        lanes: dict[str, list[tuple[float, str]]] = defaultdict(list)
        for atom, count in counter.items():
            lane = signatureRawLane(atom)
            if lane == "cx":
                selected[atom] = count
                laneKept[lane] += 1
            else:
                lanes[lane].append((float(count), atom))
        for lane, rows in lanes.items():
            limit = limits.get(lane, RAW_PRUNE_OTHER_LIMIT)
            if limit <= 0:
                continue
            for _, atom in sorted(rows, reverse=True)[:limit]:
                selected[atom] = counter[atom]
                laneKept[lane] += 1
        afterAtoms += len(selected)
        pruned[surface] = selected
    print(
        f"[rawPrune] surfaces={len(raw)} atoms={beforeAtoms}->{afterAtoms} "
        f"xp={laneKept['xp']} hx={laneKept['hx']} el={laneKept['el']} "
        f"cx={laneKept['cx']} other={laneKept['other']}"
    )
    return pruned


def weightCounters(raw: dict[str, Counter[str]]) -> dict[str, Counter[str]]:
    df: Counter[str] = Counter()
    for counter in raw.values():
        df.update(counter.keys())
    total = max(1, len(raw))
    weighted: dict[str, Counter[str]] = {}
    for surface, counter in raw.items():
        rows = []
        for atom, count in counter.items():
            lane = (
                1.7
                if atom.startswith("xp:")
                else 1.5
                if atom.startswith("el:")
                else 1.0
                if atom.startswith("hx:")
                else 0.35
            )
            rows.append((math.sqrt(float(count)) * math.log(1.0 + total / (1.0 + df[atom])) * lane, atom))
        selected = Counter({atom: score for score, atom in sorted(rows, reverse=True)[:SIGNATURE_LIMIT]})
        for atom, count in counter.items():
            if atom.startswith("cx:"):
                selected[atom] = max(float(selected.get(atom, 0.0)), float(count) * 0.35)
        weighted[surface] = selected
    return weighted


def coordAtomSpecificity(atom: str) -> int:
    if atom.startswith("cx:full:"):
        return 8
    parts = atom.split(":", 2)
    if len(parts) < 2:
        return 0
    key = parts[1]
    if len(key) < 2 or key[0] not in {"p", "s", "g"}:
        return 0
    return int(key[1:]) if key[1:].isdigit() else 0


def relayCoordAtom(atom: str) -> bool:
    if not atom.startswith("cx:") or atom.startswith("cx:full:"):
        return False
    return coordAtomSpecificity(atom) >= 2


def relaySurfacePriority(surface: str, signature: Counter[str]) -> float:
    meaningMass = sum(float(weight) for atom, weight in signature.items() if atom.startswith(("xp:", "el:", "hx:")))
    coordMass = sum(float(weight) for atom, weight in signature.items() if atom.startswith("cx:"))
    return meaningMass + coordMass * 0.15 + min(len(normStem(surface)), 20) * 0.02


def coordPostings(signatures: dict[str, Counter[str]], *, log: bool = True) -> dict[str, list[str]]:
    rows: dict[str, list[tuple[float, int, str]]] = defaultdict(list)
    rawLinks = 0
    skippedBroad = 0
    for surface, signature in signatures.items():
        priority = relaySurfacePriority(surface, signature)
        length = len(normStem(surface))
        for atom in signature:
            if not atom.startswith("cx:"):
                continue
            rawLinks += 1
            if not relayCoordAtom(atom):
                skippedBroad += 1
                continue
            rows[atom].append((priority, length, surface))

    postings: dict[str, list[str]] = {}
    keptLinks = 0
    prunedRows = 0
    maxRow = 0
    for atom, row in rows.items():
        specificity = coordAtomSpecificity(atom)
        limit = RELAY_SPECIFIC_ROW_LIMIT if specificity >= 3 else RELAY_ROW_LIMIT
        if len(row) > limit:
            prunedRows += 1
            row = sorted(row, reverse=True)[:limit]
        else:
            row = sorted(row, reverse=True)
        surfaces = [surface for _, _, surface in row]
        postings[atom] = surfaces
        keptLinks += len(surfaces)
        maxRow = max(maxRow, len(surfaces))
    if log:
        print(
            f"[relayPostings] keys={len(postings)} rawLinks={rawLinks} keptLinks={keptLinks} "
            f"skippedBroad={skippedBroad} prunedRows={prunedRows} maxRow={maxRow} "
            f"rowLimit={RELAY_ROW_LIMIT}/{RELAY_SPECIFIC_ROW_LIMIT}"
        )
    return postings


def relaySourceSignatures(signatures: dict[str, Counter[str]]) -> dict[str, Counter[str]]:
    cohortCounts: Counter[str] = Counter()
    cohortAtoms: dict[str, Counter[str]] = defaultdict(Counter)
    rawUpdates = 0
    for surface, signature in signatures.items():
        keys = suffixCohortKeys(surface)
        if not keys:
            continue
        atoms = {atom for atom, _ in signature.most_common(RELAY_COMMON_ATOM_LIMIT) if meaningAtom(atom)}
        rawUpdates += len(atoms) * len(keys)
        for key in keys:
            cohortCounts[key] += 1
            cohortAtoms[key].update(atoms)
    commonByKey: dict[str, set[str]] = {}
    commonAtoms = 0
    for key, counter in cohortAtoms.items():
        surfaceCount = cohortCounts.get(key, 0)
        if surfaceCount <= 1:
            continue
        atoms = {atom for atom, count in counter.items() if count / surfaceCount >= RELAY_COMMON_RATIO}
        if atoms:
            commonByKey[key] = atoms
            commonAtoms += len(atoms)
    sources: dict[str, Counter[str]] = {}
    removed = 0
    for surface, signature in signatures.items():
        blocked: set[str] = set()
        for key in suffixCohortKeys(surface):
            blocked.update(commonByKey.get(key, ()))
        if not blocked:
            sources[surface] = signature
            continue
        source = Counter()
        for atom, weight in signature.items():
            if atom in blocked and meaningAtom(atom):
                removed += 1
                continue
            source[atom] = weight
        sources[surface] = source
    print(
        f"[relaySource] atomLimit={RELAY_COMMON_ATOM_LIMIT} rawUpdates={rawUpdates} "
        f"commonAtoms={commonAtoms} removed={removed}"
    )
    return sources


def relayAtomView(relaySources: dict[str, Counter[str]]) -> dict[str, tuple[tuple[str, float], ...]]:
    views: dict[str, tuple[tuple[str, float], ...]] = {}
    for surface, source in relaySources.items():
        atoms = tuple(
            (f"relay:{atom}", float(weight))
            for atom, weight in source.most_common(RELAY_ATOM_LIMIT)
            if atom.startswith(("xp:", "el:"))
        )
        if atoms:
            views[surface] = atoms
    return views


def relayExperience(
    signatures: dict[str, Counter[str]],
    postings: dict[str, list[str]],
    relaySources: dict[str, Counter[str]],
) -> None:
    started = time.perf_counter()
    relayViews = relayAtomView(relaySources)
    viewBuilt = time.perf_counter()
    candidateSurfaces = 0
    relayUpdates = 0
    for surface, signature in list(signatures.items()):
        candidates: Counter[str] = Counter()
        for atom in coordAtoms(surface):
            for other in postings.get(atom, ()):
                if other != surface:
                    candidates[other] += 1
        if candidates:
            candidateSurfaces += 1
        for other, overlap in candidates.most_common(RELAY_NEIGHBOR_LIMIT):
            scale = min(0.11, 0.012 * overlap)
            for atom, weight in relayViews.get(other, ()):
                signature[atom] += weight * scale
                relayUpdates += 1
    finished = time.perf_counter()
    print(
        f"[relay] surfaces={candidateSurfaces} neighbors={RELAY_NEIGHBOR_LIMIT} "
        f"atoms={RELAY_ATOM_LIMIT} views={len(relayViews)} updates={relayUpdates} "
        f"view={viewBuilt - started:.1f}s build={finished - viewBuilt:.1f}s"
    )


def buildSignatures(
    caches: list[Cache],
    sketches: dict[str, Counter[str]],
    horizonAtomCache: dict[tuple[int, int], set[str]],
    horizonTokenViews: dict[int, HorizonTokenView],
) -> tuple[dict[str, Counter[str]], dict[str, list[str]]]:
    started = time.perf_counter()
    raw: dict[str, Counter[str]] = defaultdict(Counter)
    stats: Counter[str] = Counter()
    sketchView = buildSketchAtomView(sketches)
    viewBuilt = time.perf_counter()
    sampledOccs = selectSignatureOccurrences(caches)
    sampled = time.perf_counter()
    for cache, occ in sampledOccs:
        raw[occ.surface].update(cachedHorizonAtoms(cache, occ.position, horizonAtomCache, horizonTokenViews, stats))
        raw[occ.surface].update(lineAtoms(occ.position, cache.stems, cache.markers, cache.lanes, sketchView))
    for surface, counter in raw.items():
        for atom in coordAtoms(surface):
            counter[atom] += 1
    rawBuilt = time.perf_counter()
    raw = pruneRawSignatureCounters(raw)
    pruned = time.perf_counter()
    signatures = weightCounters(raw)
    weighted = time.perf_counter()
    postings = coordPostings(signatures)
    relaySources = relaySourceSignatures(signatures)
    sourceBuilt = time.perf_counter()
    relayExperience(signatures, postings, relaySources)
    relayed = time.perf_counter()
    print(
        f"[signature] surfaces={len(signatures)} coordKeys={len(postings)} "
        f"horizonMiss={stats['miss']} horizonHit={stats['hit']}"
    )
    print(
        f"[signatureStage] view={viewBuilt - started:.1f}s sample={sampled - viewBuilt:.1f}s "
        f"raw={rawBuilt - sampled:.1f}s "
        f"prune={pruned - rawBuilt:.1f}s "
        f"weight={weighted - pruned:.1f}s relaySource={sourceBuilt - weighted:.1f}s "
        f"relay={relayed - sourceBuilt:.1f}s"
    )
    return signatures, postings


def pref(counter: Counter[str], prefixes: tuple[str, ...]) -> Counter[str]:
    return Counter({key: value for key, value in counter.items() if key.startswith(prefixes)})


def cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = sum(value * right.get(key, 0.0) for key, value in left.items())
    if overlap <= 0:
        return 0.0
    return overlap / math.sqrt(
        sum(value * value for value in left.values()) * sum(value * value for value in right.values())
    )


def inferSignature(surface: str, model: Model) -> Counter[str]:
    stem = normStem(surface)
    if stem in model.signatures:
        return Counter(model.signatures[stem])
    out = Counter({atom: 0.25 for atom in coordAtoms(stem)})
    if not hasRawCompoundBridge(stem, model):
        candidates: Counter[str] = Counter()
        for atom in coordAtoms(stem):
            for other in model.coordPostings.get(atom, ()):
                candidates[other] += 1
        for other, overlap in candidates.most_common(10):
            scale = min(0.16, 0.02 * overlap)
            for atom, weight in model.signatures.get(other, Counter()).most_common(36):
                if atom.startswith(("xp:", "el:", "hx:", "relay:")):
                    out[atom] += weight * scale
    return out


def surfaceLaneProfile(surface: str, model: Model) -> tuple[float, float, float]:
    stem = normStem(surface)
    profile = model.surfaceLaneProfiles.get(stem)
    if profile is not None:
        return profile
    return (1.0, 0.0, 0.0)


def routeLanePenalty(
    surface: str, target: str, compound: float, contrast: float, el: float, resonance: float, model: Model
) -> float:
    querySentence, queryArtifact, queryOwner = surfaceLaneProfile(surface, model)
    targetSentence, targetArtifact, targetOwner = surfaceLaneProfile(target, model)

    artifactMismatch = max(0.0, abs(queryArtifact - targetArtifact) - 0.16)
    ownerMismatch = max(0.0, abs(queryOwner - targetOwner) - 0.18)
    weakExperience = max(0.0, ROUTE_MIN_EXPERIENCE - (contrast + el))
    bridgeReliance = max(0.0, compound - COMPOUND_ASSOC_ACCEPT_MIN) if weakExperience > 0 else 0.0
    artifactReliance = max(queryArtifact, targetArtifact) * (1.0 - min(querySentence, targetSentence))
    ownerTransfer = 0.0
    if resonance < RESONANCE_ACCEPT_MIN:
        ownerTransfer = max(0.0, targetOwner - queryOwner - 0.10) * 0.75

    return (
        artifactMismatch * LANE_MISMATCH_PENALTY
        + ownerMismatch * LANE_MISMATCH_PENALTY * 0.65
        + artifactReliance * LANE_ARTIFACT_PENALTY * min(1.0, bridgeReliance * 8.0)
        + ownerTransfer
    )


def route(surface: str, model: Model):
    query = inferSignature(surface, model)
    rows = []
    for target in TARGETS:
        targetSig = inferSignature(target, model)
        xp = cosine(
            pref(query, ("xp:", "hx:", "relay:xp", "relay:hx", "compoundProxy:xp", "compoundProxy:hx")),
            pref(targetSig, ("xp:", "hx:", "relay:xp", "relay:hx", "compoundProxy:xp", "compoundProxy:hx")),
        )
        contrast = cosine(contrastSignature(surface, query, model), contrastSignature(target, targetSig, model))
        el = cosine(
            pref(query, ("el:", "relay:el", "compoundProxy:el")),
            pref(targetSig, ("el:", "relay:el", "compoundProxy:el")),
        )
        cx = cosine(pref(query, ("cx:",)), pref(targetSig, ("cx:",)))
        resonance = coordResonance(surface, target, model)
        compound = compoundAssociation(surface, target, model)
        lanePenalty = routeLanePenalty(surface, target, compound, contrast, el, resonance, model)
        sameSuffix = longestCommonSuffixSize(surface, target) >= COHORT_SUFFIX_MIN
        suffixNoResonance = sameSuffix and resonance < RESONANCE_ACCEPT_MIN
        commonPenalty = max(0.0, xp - contrast) * 0.75
        suffixPenalty = 0.20 if suffixNoResonance else 0.0
        score = (
            contrast * 2.6
            + el * 1.2
            + cx * 0.20
            + resonance * 0.45
            + compound * 1.8
            - commonPenalty
            - suffixPenalty
            - lanePenalty
        )
        baseAccepted = (
            score >= ROUTE_MIN_SCORE
            and not suffixNoResonance
            and not (
                not sameSuffix
                and compound < COMPOUND_ASSOC_ACCEPT_MIN
                and resonance < RESONANCE_ACCEPT_MIN
                and cx < 0.20
            )
            and (
                (contrast + el) >= ROUTE_MIN_EXPERIENCE
                or (sameSuffix and resonance >= RESONANCE_ACCEPT_MIN)
                or compound >= COMPOUND_ASSOC_ACCEPT_MIN
            )
            and (
                contrast >= CONTRAST_ACCEPT_MIN
                or resonance >= RESONANCE_ACCEPT_MIN
                or compound >= COMPOUND_ASSOC_ACCEPT_MIN
            )
        )
        rows.append((score, target, xp, contrast, el, cx, resonance, compound, baseAccepted))
    ordered = sorted(rows, reverse=True)
    if not ordered:
        return ordered
    topScore, topTarget, *_ = ordered[0]
    topCompound = ordered[0][7]
    adjusted = []
    for row in ordered:
        score, target, xp, contrast, el, cx, resonance, compound, accepted = row
        if target == topTarget and not accepted and score >= 0.055 and cx >= 0.20 and resonance >= 0.050:
            accepted = True
        if accepted and target != topTarget and topScore > 0:
            scoreGap = topScore - score
            scoreRatio = score / max(topScore, 1e-9)
            compoundOnly = compound >= COMPOUND_ASSOC_ACCEPT_MIN and (contrast + el) < ROUTE_MIN_EXPERIENCE
            weakCompetitor = scoreRatio < ROUTE_ACCEPT_MARGIN_RATIO and scoreGap >= ROUTE_ACCEPT_MARGIN_GAP
            weakBridge = compoundOnly and compound < topCompound * 0.62 and scoreGap >= ROUTE_ACCEPT_MARGIN_GAP
            if weakCompetitor or weakBridge:
                accepted = False
        adjusted.append((score, target, xp, contrast, el, cx, resonance, compound, accepted))
    return (
        sorted(adjusted, key=lambda row: (row[8], row[0]), reverse=True)
        if any(row[8] for row in adjusted)
        else adjusted
    )


def allPositions(text: str, terms: list[str]) -> list[int]:
    positions: list[int] = []
    for term in terms:
        if not term:
            continue
        start = 0
        while True:
            index = text.find(term, start)
            if index < 0:
                break
            positions.append(index)
            start = index + max(1, len(term))
    return positions


def spanStrengthFromDistance(distance: int) -> float:
    if distance <= 64:
        return 1.00
    if distance <= 96:
        return 0.82
    if distance <= SPAN_MAX_DISTANCE:
        return 0.58
    return 0.0


def relationOrderFrameStrength(
    text: str,
    surfacePos: int,
    surfaceSize: int,
    relationPos: int,
    relationSize: int,
    interveningSurface: bool,
) -> float:
    if relationPos >= surfacePos:
        between = text[surfacePos + surfaceSize : relationPos]
        distance = relationPos - surfacePos
        if distance > FRAME_MAX_DISTANCE:
            return 0.0
        if interveningSurface:
            if distance <= 64 and not FRAME_FENCE_RE.search(between):
                return 0.34
            return 0.16
        if VALUE_RE.search(between):
            return 1.0
        if distance <= 72 and not FRAME_FENCE_RE.search(between):
            return 0.82
        if distance <= 120 and not FRAME_FENCE_RE.search(between):
            return 0.55
        return 0.22
    between = text[relationPos + relationSize : surfacePos]
    distance = surfacePos - relationPos
    if distance > FRAME_MAX_DISTANCE:
        return 0.0
    if FRAME_FENCE_RE.search(between):
        return 0.08
    if distance <= 42:
        return 0.32
    if VALUE_RE.search(between) and distance <= 96:
        return 0.24
    return 0.08


def relationTableLeakStrength(
    text: str,
    surfacePos: int,
    surfaceSize: int,
    relationPos: int,
    relationSize: int,
) -> float:
    if relationPos >= surfacePos:
        between = text[surfacePos + surfaceSize : relationPos]
        distance = relationPos - surfacePos
        if distance <= FRAME_MAX_DISTANCE and FRAME_FENCE_RE.search(between):
            return 0.70
        return 0.0
    between = text[relationPos + relationSize : surfacePos]
    distance = surfacePos - relationPos
    if not FRAME_FENCE_RE.search(between):
        return 0.0
    if distance <= FRAME_MAX_DISTANCE:
        return 1.0
    if distance <= FRAME_MAX_DISTANCE * 2:
        return 0.72
    return 0.0


def gapDistance(leftPos: int, leftSize: int, rightPos: int, rightSize: int) -> int:
    if rightPos >= leftPos:
        return max(0, rightPos - (leftPos + leftSize))
    return max(0, leftPos - (rightPos + rightSize))


def relationOccurrenceUseMultiplier(text: str, relationPos: int, relationSize: int) -> float:
    after = text[relationPos + relationSize : relationPos + relationSize + 6]
    if BOUND_RELATION_NOUN_RE.match(after):
        return 0.24
    return 1.0


def sameClause(text: str, leftPos: int, leftSize: int, rightPos: int, rightSize: int) -> bool:
    start = min(leftPos + leftSize, rightPos + rightSize)
    end = max(leftPos, rightPos)
    if start >= end:
        return True
    return CLAUSE_BOUNDARY_RE.search(text[start:end]) is None


def surfaceOwnerMatch(surface: str, ownerSurface: str) -> bool:
    surface = normStem(surface)
    ownerSurface = normStem(ownerSurface)
    if surface == ownerSurface:
        return True
    if len(surface) >= 4 and len(ownerSurface) >= 4 and (surface in ownerSurface or ownerSurface in surface):
        return True
    return nonSuffixCompoundOverlap(surface, ownerSurface) >= 0.45


@lru_cache(maxsize=200_000)
def relationOwnerCandidate(surface: str) -> bool:
    surface = normStem(surface)
    if not isContentStem(surface) or surface in STOP_STEMS:
        return False
    if any(surface.endswith(suffix) for suffix in OWNER_STOP_SUFFIXES):
        return False
    if any(surface.startswith(term) or surface.endswith(term) for _, terms in RELATIONS for term in terms):
        return False
    return True


def relationBoundStrength(
    text: str,
    surface: str,
    surfacePos: int,
    surfaceSize: int,
    relationPos: int,
    relationSize: int,
    allSurfacePositions: list[tuple[int, int, str]],
) -> float:
    distance = gapDistance(surfacePos, surfaceSize, relationPos, relationSize)
    if distance > FRAME_MAX_DISTANCE:
        return 0.0
    if not sameClause(text, surfacePos, surfaceSize, relationPos, relationSize):
        return 0.08
    between = text[min(surfacePos + surfaceSize, relationPos + relationSize) : max(surfacePos, relationPos)]
    if FRAME_FENCE_RE.search(between):
        return 0.06

    localOwners: list[tuple[int, str]] = []
    for otherPos, otherSize, otherSurface in allSurfacePositions:
        otherDistance = gapDistance(otherPos, otherSize, relationPos, relationSize)
        if otherDistance > FRAME_MAX_DISTANCE:
            continue
        if not sameClause(text, otherPos, otherSize, relationPos, relationSize):
            continue
        localOwners.append((otherDistance, otherSurface))
    if not localOwners:
        ownerMatches = True
    else:
        bestDistance = min(distance for distance, _ in localOwners)
        ownerMatches = any(
            surfaceOwnerMatch(surface, ownerSurface)
            for distance, ownerSurface in localOwners
            if distance == bestDistance
        )

    if relationPos >= surfacePos:
        if distance <= 32:
            base = 1.0
        elif distance <= 72:
            base = 0.82
        elif distance <= 120:
            base = 0.58
        else:
            base = 0.34
    else:
        if distance <= 32:
            base = 0.34
        elif distance <= 72:
            base = 0.24
        else:
            base = 0.12
    if not ownerMatches:
        base = min(base, 0.18)
    return base * relationOccurrenceUseMultiplier(text, relationPos, relationSize)


def relationOwnerFrame(
    text: str,
    relationPos: int,
    relationSize: int,
    localOwnerRows: list[tuple[int, int, str]],
) -> tuple[str, ...]:
    localOwners: list[tuple[int, str]] = []
    for otherPos, otherSize, otherSurface in localOwnerRows:
        otherDistance = gapDistance(otherPos, otherSize, relationPos, relationSize)
        if otherDistance > FRAME_MAX_DISTANCE:
            continue
        if not sameClause(text, otherPos, otherSize, relationPos, relationSize):
            continue
        localOwners.append((otherDistance, otherSurface))
    if not localOwners:
        return tuple()
    bestDistance = min(distance for distance, _ in localOwners)
    return tuple(sorted({ownerSurface for distance, ownerSurface in localOwners if distance == bestDistance}))


def relationBoundStrengthWithOwnerFrame(
    text: str,
    surface: str,
    surfacePos: int,
    surfaceSize: int,
    relationPos: int,
    relationSize: int,
    bestOwnerSurfaces: tuple[str, ...],
) -> float:
    distance = gapDistance(surfacePos, surfaceSize, relationPos, relationSize)
    if distance > FRAME_MAX_DISTANCE:
        return 0.0
    if not sameClause(text, surfacePos, surfaceSize, relationPos, relationSize):
        return 0.08
    between = text[min(surfacePos + surfaceSize, relationPos + relationSize) : max(surfacePos, relationPos)]
    if FRAME_FENCE_RE.search(between):
        return 0.06

    ownerMatches = (
        True
        if not bestOwnerSurfaces
        else any(surfaceOwnerMatch(surface, ownerSurface) for ownerSurface in bestOwnerSurfaces)
    )
    if relationPos >= surfacePos:
        if distance <= 32:
            base = 1.0
        elif distance <= 72:
            base = 0.82
        elif distance <= 120:
            base = 0.58
        else:
            base = 0.34
    else:
        if distance <= 32:
            base = 0.34
        elif distance <= 72:
            base = 0.24
        else:
            base = 0.12
    if not ownerMatches:
        base = min(base, 0.18)
    return base * relationOccurrenceUseMultiplier(text, relationPos, relationSize)


def buildRelationSpanIndex(
    caches: list[Cache],
) -> tuple[dict[tuple[str, str], list[int]], dict[tuple[int, str, str], float]]:
    postings: dict[tuple[str, str], list[int]] = defaultdict(list)
    scores: dict[tuple[int, str, str], float] = {}
    relationPositionsByUnit: dict[int, dict[str, list[int]]] = {}
    for cache in caches:
        text = SPACE_RE.sub(" ", cache.unit.text)
        relationPositionsByUnit[cache.unit.unitId] = {
            name: allPositions(text, list(terms)) for name, terms in RELATIONS
        }
        surfaces = sorted({occ.surface for occ in cache.occs if isContentStem(occ.surface)})
        for surface in surfaces:
            surfacePositions = allPositions(text, [surface])
            if not surfacePositions:
                continue
            for relation, relPositions in relationPositionsByUnit[cache.unit.unitId].items():
                if not relPositions:
                    continue
                bestDistance = min(abs(left - right) for left in surfacePositions for right in relPositions)
                strength = spanStrengthFromDistance(bestDistance)
                if strength <= 0:
                    continue
                key = (surface, relation)
                postings[key].append(cache.unit.unitId)
                scores[(cache.unit.unitId, surface, relation)] = max(
                    scores.get((cache.unit.unitId, surface, relation), 0.0), strength
                )
    return dict(postings), scores


def buildRelationFrameIndex(
    caches: list[Cache],
) -> tuple[
    dict[tuple[str, str], list[int]],
    dict[tuple[int, str, str], float],
    dict[tuple[int, str, str], float],
    dict[tuple[str, str], list[int]],
    dict[tuple[int, str, str], float],
]:
    postings: dict[tuple[str, str], list[int]] = defaultdict(list)
    scores: dict[tuple[int, str, str], float] = {}
    leaks: dict[tuple[int, str, str], float] = {}
    boundPostings: dict[tuple[str, str], list[int]] = defaultdict(list)
    boundScores: dict[tuple[int, str, str], float] = {}
    for cache in caches:
        text = SPACE_RE.sub(" ", cache.unit.text)
        relationPositions = {
            name: [(pos, len(term)) for term in terms for pos in allPositions(text, [term])]
            for name, terms in RELATIONS
        }
        surfaces = sorted({occ.surface for occ in cache.occs if isContentStem(occ.surface)})
        allSurfacePositions: list[tuple[int, int, str]] = []
        surfacePositionMap: dict[str, list[tuple[int, int]]] = {}
        for surface in surfaces:
            surfacePositions = [(pos, len(surface)) for pos in allPositions(text, [surface])]
            surfacePositionMap[surface] = surfacePositions
            allSurfacePositions.extend((pos, size, surface) for pos, size in surfacePositions)
        ownerSurfacePositions = [
            (pos, size, surface) for pos, size, surface in allSurfacePositions if relationOwnerCandidate(surface)
        ]
        for surface in surfaces:
            surfacePositions = surfacePositionMap.get(surface, [])
            if not surfacePositions:
                continue
            for relation, relPositions in relationPositions.items():
                best = 0.0
                bestLeak = 0.0
                bestBound = 0.0
                for surfacePos, surfaceSize in surfacePositions:
                    for relationPos, relationSize in relPositions:
                        intervening = any(
                            otherSurface != surface and surfacePos + surfaceSize <= otherPos < relationPos
                            for otherPos, _, otherSurface in allSurfacePositions
                        )
                        best = max(
                            best,
                            relationOrderFrameStrength(
                                text, surfacePos, surfaceSize, relationPos, relationSize, intervening
                            ),
                        )
                        bestLeak = max(
                            bestLeak,
                            relationTableLeakStrength(text, surfacePos, surfaceSize, relationPos, relationSize),
                        )
                        bestBound = max(
                            bestBound,
                            relationBoundStrength(
                                text,
                                surface,
                                surfacePos,
                                surfaceSize,
                                relationPos,
                                relationSize,
                                ownerSurfacePositions,
                            ),
                        )
                if bestLeak > 0:
                    leaks[(cache.unit.unitId, surface, relation)] = max(
                        leaks.get((cache.unit.unitId, surface, relation), 0.0),
                        bestLeak,
                    )
                if bestBound > 0:
                    key = (surface, relation)
                    boundPostings[key].append(cache.unit.unitId)
                    boundScores[(cache.unit.unitId, surface, relation)] = max(
                        boundScores.get((cache.unit.unitId, surface, relation), 0.0),
                        bestBound,
                    )
                if best <= 0:
                    continue
                key = (surface, relation)
                postings[key].append(cache.unit.unitId)
                scores[(cache.unit.unitId, surface, relation)] = max(
                    scores.get((cache.unit.unitId, surface, relation), 0.0), best
                )
    return dict(postings), scores, leaks, dict(boundPostings), boundScores


def focusedSurfacePositionMap(
    text: str,
    cache: Cache,
    bridgeSeedIndex: BridgeSeedIndex | None = None,
) -> dict[str, list[tuple[int, int]]]:
    allowedSurfaces = {occ.surface for occ in cache.occs if isContentStem(occ.surface)}
    out: dict[str, list[tuple[int, int]]] = {}
    for surface, positions in sideSurfacePositionMap(text, bridgeSeedIndex).items():
        if surface not in allowedSurfaces:
            continue
        seen: set[tuple[int, int]] = set()
        deduped: list[tuple[int, int]] = []
        for pos, size in positions:
            key = (pos, size)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        if deduped:
            out[surface] = deduped
    return out


def positionRows(
    surfacePositionMap: dict[str, list[tuple[int, int]]],
    *,
    ownersOnly: bool = False,
) -> tuple[list[tuple[int, int, str]], list[int]]:
    rows = sorted(
        (pos, size, surface)
        for surface, positions in surfacePositionMap.items()
        if not ownersOnly or relationOwnerCandidate(surface)
        for pos, size in positions
    )
    return rows, [pos for pos, _, _ in rows]


def rowsInPositionWindow(
    rows: list[tuple[int, int, str]],
    starts: list[int],
    left: int,
    right: int,
) -> list[tuple[int, int, str]]:
    start = bisect_left(starts, left)
    end = bisect_right(starts, right)
    return rows[start:end]


def buildFocusedRelationFrameIndex(
    caches: list[Cache],
) -> tuple[
    dict[tuple[str, str], list[int]],
    dict[tuple[int, str, str], float],
    dict[tuple[int, str, str], float],
    dict[tuple[str, str], list[int]],
    dict[tuple[int, str, str], float],
]:
    postings: dict[tuple[str, str], list[int]] = defaultdict(list)
    scores: dict[tuple[int, str, str], float] = {}
    leaks: dict[tuple[int, str, str], float] = {}
    boundPostings: dict[tuple[str, str], list[int]] = defaultdict(list)
    boundScores: dict[tuple[int, str, str], float] = {}
    relationOccurrences = 0
    localPairChecks = 0
    for cache in caches:
        text = SPACE_RE.sub(" ", cache.unit.text)
        relationPositions = {
            name: [(pos, len(term)) for term in terms for pos in allPositions(text, [term])]
            for name, terms in RELATIONS
        }
        surfacePositionMap = focusedSurfacePositionMap(text, cache)
        allSurfaceRows, allSurfaceStarts = positionRows(surfacePositionMap)
        ownerRows, ownerStarts = positionRows(surfacePositionMap, ownersOnly=True)
        if not allSurfaceRows:
            continue
        frameBest: dict[tuple[str, str], float] = {}
        leakBest: dict[tuple[str, str], float] = {}
        boundBest: dict[tuple[str, str], float] = {}
        for relation, relPositions in relationPositions.items():
            for relationPos, relationSize in relPositions:
                relationOccurrences += 1
                localRows = rowsInPositionWindow(
                    allSurfaceRows,
                    allSurfaceStarts,
                    relationPos - FOCUSED_FRAME_DISTANCE,
                    relationPos + relationSize + FOCUSED_FRAME_DISTANCE,
                )
                if not localRows:
                    continue
                localOwnerRows = rowsInPositionWindow(
                    ownerRows,
                    ownerStarts,
                    relationPos - FRAME_MAX_DISTANCE,
                    relationPos + relationSize + FRAME_MAX_DISTANCE,
                )
                for surfacePos, surfaceSize, surface in localRows:
                    if gapDistance(surfacePos, surfaceSize, relationPos, relationSize) > FOCUSED_FRAME_DISTANCE:
                        continue
                    localPairChecks += 1
                    key = (surface, relation)
                    intervening = relationPos >= surfacePos and any(
                        otherSurface != surface and surfacePos + surfaceSize <= otherPos < relationPos
                        for otherPos, _, otherSurface in localRows
                    )
                    frameBest[key] = max(
                        frameBest.get(key, 0.0),
                        relationOrderFrameStrength(
                            text, surfacePos, surfaceSize, relationPos, relationSize, intervening
                        ),
                    )
                    leakBest[key] = max(
                        leakBest.get(key, 0.0),
                        relationTableLeakStrength(text, surfacePos, surfaceSize, relationPos, relationSize),
                    )
                    boundBest[key] = max(
                        boundBest.get(key, 0.0),
                        relationBoundStrength(
                            text,
                            surface,
                            surfacePos,
                            surfaceSize,
                            relationPos,
                            relationSize,
                            localOwnerRows,
                        ),
                    )
        for (surface, relation), bestLeak in leakBest.items():
            if bestLeak > 0:
                leaks[(cache.unit.unitId, surface, relation)] = max(
                    leaks.get((cache.unit.unitId, surface, relation), 0.0),
                    bestLeak,
                )
        for (surface, relation), bestBound in boundBest.items():
            if bestBound > 0:
                key = (surface, relation)
                boundPostings[key].append(cache.unit.unitId)
                boundScores[(cache.unit.unitId, surface, relation)] = max(
                    boundScores.get((cache.unit.unitId, surface, relation), 0.0),
                    bestBound,
                )
        for (surface, relation), best in frameBest.items():
            if best <= 0:
                continue
            key = (surface, relation)
            postings[key].append(cache.unit.unitId)
            scores[(cache.unit.unitId, surface, relation)] = max(
                scores.get((cache.unit.unitId, surface, relation), 0.0),
                best,
            )
    print(f"[focusedFrame] relationOcc={relationOccurrences} localPairs={localPairChecks}")
    return dict(postings), scores, leaks, dict(boundPostings), boundScores


def buildFocusedRelationIndexes(
    caches: list[Cache],
    bridgeSeedIndex: BridgeSeedIndex,
) -> tuple[
    dict[tuple[str, str], list[int]],
    dict[tuple[int, str, str], float],
    dict[tuple[str, str], list[int]],
    dict[tuple[int, str, str], float],
    dict[tuple[int, str, str], float],
    dict[tuple[str, str], list[int]],
    dict[tuple[int, str, str], float],
]:
    spanPostings: dict[tuple[str, str], list[int]] = defaultdict(list)
    spanScores: dict[tuple[int, str, str], float] = {}
    framePostings: dict[tuple[str, str], list[int]] = defaultdict(list)
    frameScores: dict[tuple[int, str, str], float] = {}
    frameLeaks: dict[tuple[int, str, str], float] = {}
    boundPostings: dict[tuple[str, str], list[int]] = defaultdict(list)
    boundScores: dict[tuple[int, str, str], float] = {}
    relationOccurrences = 0
    localPairChecks = 0
    spanPairChecks = 0
    ownerFrames = 0
    for cache in caches:
        text = SPACE_RE.sub(" ", cache.unit.text)
        relationPositions = {
            name: [(pos, len(term)) for term in terms for pos in allPositions(text, [term])]
            for name, terms in RELATIONS
        }
        surfacePositionMap = focusedSurfacePositionMap(text, cache, bridgeSeedIndex)
        allSurfaceRows, allSurfaceStarts = positionRows(surfacePositionMap)
        ownerRows, ownerStarts = positionRows(surfacePositionMap, ownersOnly=True)
        if not allSurfaceRows:
            continue
        spanBest: dict[tuple[str, str], float] = {}
        frameBest: dict[tuple[str, str], float] = {}
        leakBest: dict[tuple[str, str], float] = {}
        boundBest: dict[tuple[str, str], float] = {}
        for relation, relPositions in relationPositions.items():
            for relationPos, relationSize in relPositions:
                relationOccurrences += 1
                localRows = rowsInPositionWindow(
                    allSurfaceRows,
                    allSurfaceStarts,
                    relationPos - FOCUSED_FRAME_DISTANCE,
                    relationPos + relationSize + FOCUSED_FRAME_DISTANCE,
                )
                if not localRows:
                    continue
                localOwnerRows = rowsInPositionWindow(
                    ownerRows,
                    ownerStarts,
                    relationPos - FRAME_MAX_DISTANCE,
                    relationPos + relationSize + FRAME_MAX_DISTANCE,
                )
                bestOwnerSurfaces = relationOwnerFrame(text, relationPos, relationSize, localOwnerRows)
                ownerFrames += 1
                for surfacePos, surfaceSize, surface in localRows:
                    key = (surface, relation)
                    startDistance = abs(surfacePos - relationPos)
                    spanStrength = spanStrengthFromDistance(startDistance)
                    if spanStrength > 0:
                        spanPairChecks += 1
                        spanBest[key] = max(spanBest.get(key, 0.0), spanStrength)
                    if gapDistance(surfacePos, surfaceSize, relationPos, relationSize) > FOCUSED_FRAME_DISTANCE:
                        continue
                    localPairChecks += 1
                    intervening = relationPos >= surfacePos and any(
                        otherSurface != surface and surfacePos + surfaceSize <= otherPos < relationPos
                        for otherPos, _, otherSurface in localRows
                    )
                    frameBest[key] = max(
                        frameBest.get(key, 0.0),
                        relationOrderFrameStrength(
                            text, surfacePos, surfaceSize, relationPos, relationSize, intervening
                        ),
                    )
                    leakBest[key] = max(
                        leakBest.get(key, 0.0),
                        relationTableLeakStrength(text, surfacePos, surfaceSize, relationPos, relationSize),
                    )
                    boundBest[key] = max(
                        boundBest.get(key, 0.0),
                        relationBoundStrengthWithOwnerFrame(
                            text,
                            surface,
                            surfacePos,
                            surfaceSize,
                            relationPos,
                            relationSize,
                            bestOwnerSurfaces,
                        ),
                    )
        for (surface, relation), bestSpan in spanBest.items():
            if bestSpan <= 0:
                continue
            key = (surface, relation)
            spanPostings[key].append(cache.unit.unitId)
            spanScores[(cache.unit.unitId, surface, relation)] = max(
                spanScores.get((cache.unit.unitId, surface, relation), 0.0),
                bestSpan,
            )
        for (surface, relation), bestLeak in leakBest.items():
            if bestLeak > 0:
                frameLeaks[(cache.unit.unitId, surface, relation)] = max(
                    frameLeaks.get((cache.unit.unitId, surface, relation), 0.0),
                    bestLeak,
                )
        for (surface, relation), bestBound in boundBest.items():
            if bestBound > 0:
                key = (surface, relation)
                boundPostings[key].append(cache.unit.unitId)
                boundScores[(cache.unit.unitId, surface, relation)] = max(
                    boundScores.get((cache.unit.unitId, surface, relation), 0.0),
                    bestBound,
                )
        for (surface, relation), bestFrame in frameBest.items():
            if bestFrame <= 0:
                continue
            key = (surface, relation)
            framePostings[key].append(cache.unit.unitId)
            frameScores[(cache.unit.unitId, surface, relation)] = max(
                frameScores.get((cache.unit.unitId, surface, relation), 0.0),
                bestFrame,
            )
    print(
        f"[focusedRelation] relationOcc={relationOccurrences} "
        f"spanPairs={spanPairChecks} localPairs={localPairChecks} ownerFrames={ownerFrames}"
    )
    return (
        dict(spanPostings),
        spanScores,
        dict(framePostings),
        frameScores,
        frameLeaks,
        dict(boundPostings),
        boundScores,
    )


def buildSideBoundIndex(
    caches: list[Cache],
) -> tuple[dict[tuple[str, str], list[int]], dict[tuple[int, str, str], float]]:
    postings: dict[tuple[str, str], list[int]] = defaultdict(list)
    scores: dict[tuple[int, str, str], float] = {}
    for cache in caches:
        text = SPACE_RE.sub(" ", cache.unit.text)
        relationPositions = {
            name: [(pos, len(term)) for term in terms for pos in allPositions(text, [term])]
            for name, terms in RELATIONS
        }
        surfaces = sorted({occ.surface for occ in cache.occs if isContentStem(occ.surface)})
        allSurfacePositions: list[tuple[int, int, str]] = []
        surfacePositionMap: dict[str, list[tuple[int, int]]] = {}
        for surface in surfaces:
            surfacePositions = [(pos, len(surface)) for pos in allPositions(text, [surface])]
            surfacePositionMap[surface] = surfacePositions
            allSurfacePositions.extend((pos, size, surface) for pos, size in surfacePositions)
        ownerSurfacePositions = [
            (pos, size, surface) for pos, size, surface in allSurfacePositions if relationOwnerCandidate(surface)
        ]
        for surface in surfaces:
            surfacePositions = surfacePositionMap.get(surface, [])
            if not surfacePositions:
                continue
            for relation, relPositions in relationPositions.items():
                bestBound = 0.0
                for surfacePos, surfaceSize in surfacePositions:
                    for relationPos, relationSize in relPositions:
                        bestBound = max(
                            bestBound,
                            relationBoundStrength(
                                text,
                                surface,
                                surfacePos,
                                surfaceSize,
                                relationPos,
                                relationSize,
                                ownerSurfacePositions,
                            ),
                        )
                if bestBound <= 0:
                    continue
                key = (surface, relation)
                postings[key].append(cache.unit.unitId)
                scores[(cache.unit.unitId, surface, relation)] = max(
                    scores.get((cache.unit.unitId, surface, relation), 0.0),
                    bestBound,
                )
    return dict(postings), scores


def sideSurfacePositionMap(
    text: str,
    bridgeSeedIndex: BridgeSeedIndex | None = None,
) -> dict[str, list[tuple[int, int]]]:
    surfacePositions: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for match in TOKEN_RE.finditer(text):
        raw = match.group(0)
        stem, _ = splitStemMarker(raw)
        stem = normStem(stem)
        if not isContentStem(stem):
            continue
        surfacePositions[stem].append((match.start(), len(stem)))
        for bridgeSurface in rawBridgeSubsurfaces(stem, bridgeSeedIndex):
            offset = stem.find(bridgeSurface)
            if offset < 0:
                offset = 0
            surfacePositions[bridgeSurface].append((match.start() + offset, len(bridgeSurface)))
    return dict(surfacePositions)


def buildSideBoundPayloadIndex(
    payloads: list[SidePayload],
    bridgeSeedIndex: BridgeSeedIndex,
) -> tuple[dict[tuple[str, str], list[int]], dict[tuple[int, str, str], float]]:
    postings: dict[tuple[str, str], list[int]] = defaultdict(list)
    scores: dict[tuple[int, str, str], float] = {}
    relationOccurrences = 0
    localPairChecks = 0
    ownerFrames = 0
    for payload in payloads:
        text = SPACE_RE.sub(" ", payload.text)
        relationPositions = {
            name: [(pos, len(term)) for term in terms for pos in allPositions(text, [term])]
            for name, terms in RELATIONS
        }
        surfacePositionMap = sideSurfacePositionMap(text, bridgeSeedIndex)
        allSurfaceRows, allSurfaceStarts = positionRows(surfacePositionMap)
        ownerRows, ownerStarts = positionRows(surfacePositionMap, ownersOnly=True)
        if not allSurfaceRows:
            continue
        boundBest: dict[tuple[str, str], float] = {}
        for relation, relPositions in relationPositions.items():
            for relationPos, relationSize in relPositions:
                relationOccurrences += 1
                localRows = rowsInPositionWindow(
                    allSurfaceRows,
                    allSurfaceStarts,
                    relationPos - FRAME_MAX_DISTANCE,
                    relationPos + relationSize + FRAME_MAX_DISTANCE,
                )
                if not localRows:
                    continue
                localOwnerRows = rowsInPositionWindow(
                    ownerRows,
                    ownerStarts,
                    relationPos - FRAME_MAX_DISTANCE,
                    relationPos + relationSize + FRAME_MAX_DISTANCE,
                )
                bestOwnerSurfaces = relationOwnerFrame(text, relationPos, relationSize, localOwnerRows)
                ownerFrames += 1
                for surfacePos, surfaceSize, surface in localRows:
                    localPairChecks += 1
                    key = (surface, relation)
                    boundBest[key] = max(
                        boundBest.get(key, 0.0),
                        relationBoundStrengthWithOwnerFrame(
                            text,
                            surface,
                            surfacePos,
                            surfaceSize,
                            relationPos,
                            relationSize,
                            bestOwnerSurfaces,
                        ),
                    )
        for (surface, relation), bestBound in boundBest.items():
            if bestBound <= 0:
                continue
            key = (surface, relation)
            postings[key].append(payload.sideId)
            scores[(payload.sideId, surface, relation)] = max(
                scores.get((payload.sideId, surface, relation), 0.0),
                bestBound,
            )
    print(
        f"[sideFocusedBound] payloads={len(payloads)} relationOcc={relationOccurrences} "
        f"localPairs={localPairChecks} ownerFrames={ownerFrames}"
    )
    return dict(postings), scores


def buildUnitAtomView(signatures: dict[str, Counter[str]]) -> dict[str, tuple[tuple[str, float], ...]]:
    view: dict[str, tuple[tuple[str, float], ...]] = {}
    for surface, signature in signatures.items():
        atoms = tuple(
            (atom, min(float(weight), 4.0))
            for atom, weight in signature.most_common(12)
            if atom.startswith(("xp:", "el:", "hx:", "relay:"))
        )
        if atoms:
            view[surface] = atoms
    return view


def buildUnitIndex(model: Model) -> None:
    started = time.perf_counter()
    unitAtomView = buildUnitAtomView(model.signatures)
    viewBuilt = time.perf_counter()
    signatures: dict[int, Counter[str]] = {}
    postings: dict[str, list[int]] = defaultdict(list)
    totalOccs = 0
    uniqueUnitSurfaces = 0
    for cache in model.caches:
        sig: Counter[str] = Counter()
        surfaceCounts = Counter(occ.surface for occ in cache.occs)
        totalOccs += sum(surfaceCounts.values())
        uniqueUnitSurfaces += len(surfaceCounts)
        for surface, count in surfaceCounts.items():
            sig[f"surf:{surface}"] += 2 * count
            for atom, weight in unitAtomView.get(surface, ()):
                sig[atom] += weight * count
        for term in cache.terms:
            if term.startswith("rel:"):
                sig[term] += 3
        signatures[cache.unit.unitId] = sig
        for atom, _ in sig.most_common(80):
            if len(postings[atom]) < POSTING_LIMIT:
                postings[atom].append(cache.unit.unitId)
    model.unitSignatures = signatures
    model.unitPostings = dict(postings)
    finished = time.perf_counter()
    print(
        f"[unitIndex] surfaceViews={len(unitAtomView)} occs={totalOccs} "
        f"uniqueUnitSurfaces={uniqueUnitSurfaces} view={viewBuilt - started:.1f}s "
        f"build={finished - viewBuilt:.1f}s"
    )


def buildModel() -> Model:
    started = time.perf_counter()
    lastStage = started

    def stage(name: str) -> None:
        nonlocal lastStage
        now = time.perf_counter()
        print(f"[stage] {name} seconds={now - lastStage:.1f} total={now - started:.1f}")
        lastStage = now

    units = collectUnits()
    stage("collectUnits")
    sidePayloads = collectSidePayloads({stableHash(unit.text, 16) for unit in units})
    stage("collectSidePayloads")
    baseCaches = [tokenize(unit) for unit in units]
    print(f"[tokenizeBase] caches={len(baseCaches)}")
    stage("tokenizeBase")
    bridgeSeedIndex = buildCorpusBridgeSeedIndex(baseCaches)
    stage("buildCorpusBridgeSeedIndex")
    caches = [augmentCacheWithBridgeSurfaces(cache, bridgeSeedIndex) for cache in baseCaches]
    stage("augmentBridgeSurfaces")
    bridgeSurfaceUniverse = {surface for cache in caches for surface in cache.bridgeSurfaces}
    bridgeSurfaceHits = sum(len(cache.bridgeSurfaces) for cache in caches)
    print(
        f"[rawBridge] mode=relationAnchoredCorpusSeed surfaces={len(bridgeSurfaceUniverse)} "
        f"hits={bridgeSurfaceHits} cache={len(bridgeSeedIndex.cache)}"
    )
    horizonTokenViews = buildHorizonTokenViews(caches)
    stage("buildHorizonTokenViews")
    horizonAtomCache: dict[tuple[int, int], set[str]] = {}
    sketches = buildSketches(caches, horizonAtomCache, horizonTokenViews)
    stage("buildSketches")
    signatures, signatureCoordPostings = buildSignatures(caches, sketches, horizonAtomCache, horizonTokenViews)
    stage("buildSignatures")
    cohortAtomDf, cohortSurfaceCounts, coordGramDf = buildContrastIndexes(signatures)
    stage("buildContrastIndexes")
    surfaceDf, surfacePairDf = buildSurfacePairIndex(caches)
    stage("buildSurfacePairIndex")
    surfaceLaneProfiles = buildSurfaceLaneProfiles(caches)
    stage("buildSurfaceLaneProfiles")
    compoundGramPostings = buildCompoundGramPostings(list(signatures))
    stage("buildCompoundGramPostings")
    (
        relationSpanPostings,
        relationSpanScores,
        relationFramePostings,
        relationFrameScores,
        relationFrameLeaks,
        relationBoundPostings,
        relationBoundScores,
    ) = buildFocusedRelationIndexes(caches, bridgeSeedIndex)
    stage("buildFocusedRelationIndexes")
    sideRelationBoundPostings, sideRelationBoundScores = buildSideBoundPayloadIndex(sidePayloads, bridgeSeedIndex)
    stage("buildSideBoundPayloadIndex")
    print(
        f"[contrast] suffixCohorts={len(cohortSurfaceCounts)} "
        f"cohortAtoms={sum(len(counter) for counter in cohortAtomDf.values())} coordGrams={len(coordGramDf)}"
    )
    print(
        f"[compound] surfaceDf={len(surfaceDf)} surfacePairs={len(surfacePairDf)} compoundGrams={len(compoundGramPostings)}"
    )
    print(
        f"[span] keys={len(relationSpanPostings)} hits={sum(len(values) for values in relationSpanPostings.values())}"
    )
    print(
        f"[frame] keys={len(relationFramePostings)} hits={sum(len(values) for values in relationFramePostings.values())} "
        f"leaks={len(relationFrameLeaks)}"
    )
    print(
        f"[bound] keys={len(relationBoundPostings)} hits={sum(len(values) for values in relationBoundPostings.values())}"
    )
    print(
        f"[side] payloads={len(sidePayloads)} boundKeys={len(sideRelationBoundPostings)} "
        f"boundHits={sum(len(values) for values in sideRelationBoundPostings.values())}"
    )
    model = Model(
        units,
        caches,
        sidePayloads,
        sketches,
        signatures,
        signatureCoordPostings,
        {},
        {},
        cohortAtomDf,
        cohortSurfaceCounts,
        coordGramDf,
        surfaceDf,
        surfacePairDf,
        surfaceLaneProfiles,
        compoundGramPostings,
        relationSpanPostings,
        relationSpanScores,
        relationFramePostings,
        relationFrameScores,
        relationFrameLeaks,
        relationBoundPostings,
        relationBoundScores,
        sideRelationBoundPostings,
        sideRelationBoundScores,
    )
    buildUnitIndex(model)
    stage("buildUnitIndex")
    print(f"[model] seconds={time.perf_counter() - started:.1f}")
    return model


def preview(rows, limit: int = 3) -> str:
    return " | ".join(
        f"{target}:{score:.3f}/xp{xp:.3f}/ct{contrast:.3f}/el{el:.3f}/cx{cx:.3f}/rs{resonance:.3f}/cp{compound:.3f}/{'Y' if ok else 'N'}"
        for score, target, xp, contrast, el, cx, resonance, compound, ok in rows[:limit]
    )


def formatLaneProfile(surface: str, model: Model) -> str:
    sentence, artifact, owner = surfaceLaneProfile(surface, model)
    return f"{surface}:S{sentence:.2f}/A{artifact:.2f}/O{owner:.2f}"


def querySurface(query: str) -> str:
    relTerms = {term for _, terms in RELATIONS for term in terms}
    stems = [normStem(match.group(0)) for match in TOKEN_RE.finditer(query)]
    stems = [stem for stem in stems if stem and stem not in relTerms and isContentStem(stem)]
    return max(stems, key=len) if stems else normStem(query)


def searchEvidenceTerms(surface: str, target: str, polarity: str, model: Model) -> list[str]:
    terms: set[str] = {normStem(surface), normStem(target)}
    for _, proxy in compoundProxySurfaces(surface, model)[:8]:
        if directPairAssociation(proxy, target, model) > 0 or nonSuffixCompoundOverlap(proxy, target) > 0.0:
            terms.add(proxy)
    if polarity:
        for name, relTerms in RELATIONS:
            if name == polarity:
                terms.update(relTerms)
    return sorted((term for term in terms if len(term) >= 2), key=len, reverse=True)


def spanEvidenceScore(unitId: int, surface: str, target: str, polarity: str, model: Model) -> float:
    if not polarity:
        return 0.0
    terms = searchEvidenceTerms(surface, target, "", model)
    scores = [model.relationSpanScores.get((unitId, term, polarity), 0.0) for term in terms]
    return max(scores) if scores else 0.0


def frameEvidenceScore(unitId: int, surface: str, target: str, polarity: str, model: Model) -> float:
    if not polarity:
        return 0.0
    terms = searchEvidenceTerms(surface, target, "", model)
    scores = [model.relationFrameScores.get((unitId, term, polarity), 0.0) for term in terms]
    return max(scores) if scores else 0.0


def frameLeakScore(unitId: int, surface: str, target: str, polarity: str, model: Model) -> float:
    if not polarity:
        return 0.0
    terms = searchEvidenceTerms(surface, target, "", model)
    scores = [model.relationFrameLeaks.get((unitId, term, polarity), 0.0) for term in terms]
    return max(scores) if scores else 0.0


def boundEvidenceScore(unitId: int, surface: str, target: str, polarity: str, model: Model) -> float:
    if not polarity:
        return 0.0
    terms = searchEvidenceTerms(surface, target, "", model)
    scores = [model.relationBoundScores.get((unitId, term, polarity), 0.0) for term in terms]
    return max(scores) if scores else 0.0


def sideBoundEvidenceScore(sideId: int, surface: str, target: str, polarity: str, model: Model) -> float:
    if not polarity:
        return 0.0
    terms = searchEvidenceTerms(surface, target, "", model)
    scores = [model.sideRelationBoundScores.get((sideId, term, polarity), 0.0) for term in terms]
    return max(scores) if scores else 0.0


def searchReliabilityStatus(
    polarity: str,
    evidence: float,
    spanScore: float,
    frameScore: float,
    leakScore: float,
    boundScore: float,
) -> str:
    if not polarity:
        return "reliable" if evidence >= 0.50 else "weak"
    if leakScore >= 0.82 and frameScore < 0.55:
        return "abstain"
    if boundScore >= RELIABLE_BOUND_MIN and evidence >= RELIABLE_EVIDENCE_MIN:
        return "reliable"
    if boundScore >= WEAK_BOUND_MIN and (evidence >= 0.50 or frameScore >= 0.55 or spanScore >= 0.82):
        return "weak"
    return "abstain"


def relationNearEvidence(text: str, focusTerms: list[str], polarity: str, maxDistance: int = 96) -> float:
    if not polarity:
        return 0.0
    relTerms = [term for name, terms in RELATIONS if name == polarity for term in terms]
    focusPositions = [text.find(term) for term in focusTerms if term and text.find(term) >= 0]
    relPositions = [text.find(term) for term in relTerms if text.find(term) >= 0]
    if not relPositions:
        return 0.0
    if not focusPositions:
        return 0.15
    best = min(abs(left - right) for left in focusPositions for right in relPositions)
    if best <= maxDistance:
        return 1.0
    if best <= maxDistance * 2:
        return 0.20
    return 0.0


def unitEvidenceScore(
    unitId: int, unitSig: Counter[str], text: str, surface: str, target: str, polarity: str, model: Model
) -> float:
    surface = normStem(surface)
    target = normStem(target)
    targetHit = unitSig.get(f"surf:{target}", 0.0) > 0 or target in text
    queryHit = surface != target and (unitSig.get(f"surf:{surface}", 0.0) > 0 or surface in text)
    bridgeTerms = []
    bridgeHit = False
    for term in searchEvidenceTerms(surface, target, "", model):
        if term in {surface, target}:
            continue
        bridgeTerms.append(term)
        if unitSig.get(f"surf:{term}", 0.0) > 0 or term in text:
            bridgeHit = True
    nearRel = relationNearEvidence(text, [target, surface, *bridgeTerms], polarity)
    spanScore = spanEvidenceScore(unitId, surface, target, polarity, model)
    frameScore = frameEvidenceScore(unitId, surface, target, polarity, model)
    leakScore = frameLeakScore(unitId, surface, target, polarity, model)
    boundScore = boundEvidenceScore(unitId, surface, target, polarity, model)
    if polarity:
        if targetHit and boundScore >= 0.82:
            score = 1.0
        elif targetHit and boundScore >= 0.55:
            score = 0.90
        elif targetHit and frameScore >= 0.82:
            score = 0.84
        elif targetHit and frameScore >= 0.55:
            score = 0.72
        elif targetHit and spanScore >= 0.82:
            score = 0.74
        elif targetHit and spanScore >= 0.58:
            score = 0.62
        elif targetHit and nearRel >= 1.0:
            score = 0.56
        elif targetHit and nearRel >= 0.20:
            score = 0.40
        elif (queryHit or bridgeHit) and nearRel >= 1.0:
            score = 0.62
        elif targetHit:
            score = 0.24
        else:
            score = 0.10
    else:
        score = 0.0
        if targetHit:
            score += 0.50
        if queryHit:
            score += 0.25
        if bridgeHit:
            score += 0.18
    if targetHit and (queryHit or bridgeHit):
        score += 0.08
    if polarity and leakScore >= 0.82 and frameScore < 0.55:
        score = min(score, TABLE_ROW_LEAK_EVIDENCE_CAP)
    elif polarity and leakScore >= 0.70 and frameScore < 0.55:
        score = min(score, TABLE_ROW_LEAK_EVIDENCE_CAP + 0.08)
    if polarity and frameScore >= 0.55 and boundScore < 0.34:
        score = min(score, ROLE_BOUND_EVIDENCE_CAP)
    elif polarity and spanScore >= 0.82 and boundScore < 0.34:
        score = min(score, ROLE_BOUND_EVIDENCE_CAP + 0.02)
    return min(1.0, score)


def evidenceSnippet(text: str, surface: str, target: str, polarity: str, model: Model, width: int = 126) -> str:
    compact = SPACE_RE.sub(" ", text)
    if polarity:
        focusTerms = searchEvidenceTerms(surface, target, "", model)
        relTerms = [term for name, terms in RELATIONS if name == polarity for term in terms]
        focusPositions = [(pos, len(term), term) for term in focusTerms for pos in allPositions(compact, [term])]
        relPositions = [(pos, len(term)) for term in relTerms for pos in allPositions(compact, [term])]
        if focusPositions and relPositions:
            focusPos, focusSize, focusTerm, relPos, relSize = min(
                (
                    (fpos, fsize, fterm, rpos, rsize)
                    for fpos, fsize, fterm in focusPositions
                    for rpos, rsize in relPositions
                ),
                key=lambda item: (
                    -relationBoundStrength(compact, item[2], item[0], item[1], item[3], item[4], focusPositions),
                    relationTableLeakStrength(compact, item[0], item[1], item[3], item[4]) >= 0.82,
                    relationTableLeakStrength(compact, item[0], item[1], item[3], item[4]),
                    abs(item[0] - item[3]),
                ),
            )
            center = (min(focusPos, relPos) + max(focusPos + focusSize, relPos + relSize)) // 2
            left = max(0, center - width // 2)
            right = min(len(compact), left + width)
            left = max(0, right - width)
            return compact[left:right]
    priorityGroups = [
        [normStem(target), normStem(surface)],
        [
            term
            for term in searchEvidenceTerms(surface, target, "", model)
            if term not in {normStem(target), normStem(surface)}
        ],
    ]
    if polarity:
        priorityGroups.append([term for name, terms in RELATIONS if name == polarity for term in terms])
    for terms in priorityGroups:
        positions = [(compact.find(term), len(term)) for term in terms if term and compact.find(term) >= 0]
        if positions:
            pos, size = min(positions, key=lambda item: item[0])
            left = max(0, pos - max(12, (width - size) // 2))
            right = min(len(compact), left + width)
            left = max(0, right - width)
            return compact[left:right]
    return compact[:width]


def scoreSearchHit(
    unitId: int,
    base: float,
    seed: Counter[str],
    surface: str,
    target: str,
    polarity: str,
    model: Model,
):
    unitSig = model.unitSignatures.get(unitId, Counter())
    unit = model.units[unitId]
    evidence = unitEvidenceScore(unitId, unitSig, unit.text, surface, target, polarity, model)
    spanScore = spanEvidenceScore(unitId, surface, target, polarity, model)
    frameScore = frameEvidenceScore(unitId, surface, target, polarity, model)
    leakScore = frameLeakScore(unitId, surface, target, polarity, model)
    boundScore = boundEvidenceScore(unitId, surface, target, polarity, model)
    nearScore = relationNearEvidence(unit.text, searchEvidenceTerms(surface, target, "", model), polarity)
    if polarity and leakScore >= 0.70 and frameScore < 0.55 and evidence < 0.40:
        return None
    if polarity and evidence < SEARCH_EVIDENCE_MIN and spanScore < 0.58 and frameScore < 0.34 and nearScore < 1.0:
        return None
    score = cosine(seed, unitSig) * 5 + base * 0.01
    score += evidence * 9.0
    score += spanScore * 2.5
    score += frameScore * 3.0
    score += boundScore * 8.0
    if polarity and leakScore >= 0.70 and frameScore < 0.55:
        score -= leakScore * TABLE_ROW_LEAK_SEARCH_PENALTY
    if polarity and frameScore >= 0.55 and boundScore < 0.34:
        score -= ROLE_BOUND_SEARCH_PENALTY
    elif polarity and spanScore >= 0.82 and boundScore < 0.34:
        score -= ROLE_BOUND_SEARCH_PENALTY * 0.8
    if evidence < SEARCH_EVIDENCE_MIN:
        score -= 3.0
    elif polarity and evidence < 0.70:
        score -= 4.0
    if polarity and frameScore < 0.55:
        score -= 6.0
    score += nearScore * 3.0
    status = searchReliabilityStatus(polarity, evidence, spanScore, frameScore, leakScore, boundScore)
    if status == "weak":
        score -= 2.0
    elif status == "abstain":
        score -= 10.0
    return (
        score,
        evidence,
        spanScore,
        frameScore,
        leakScore,
        boundScore,
        status,
        target,
        unit.ref,
        evidenceSnippet(unit.text, surface, target, polarity, model),
    )


def scoreSideSearchHit(
    sideId: int,
    base: float,
    surface: str,
    target: str,
    polarity: str,
    model: Model,
):
    payload = model.sidePayloads[sideId]
    text = payload.text
    surface = normStem(surface)
    target = normStem(target)
    targetHit = target in text
    queryHit = surface != target and surface in text
    bridgeTerms = [term for term in searchEvidenceTerms(surface, target, "", model) if term not in {surface, target}]
    bridgeHit = any(term in text for term in bridgeTerms)
    boundScore = sideBoundEvidenceScore(sideId, surface, target, polarity, model)
    spanScore = boundScore
    frameScore = boundScore
    leakScore = 0.0
    if targetHit and boundScore >= 0.82:
        evidence = 1.0
    elif targetHit and boundScore >= 0.55:
        evidence = 0.90
    elif (queryHit or bridgeHit) and boundScore >= 0.82:
        evidence = 0.78
    elif targetHit and boundScore >= 0.34:
        evidence = 0.58
    else:
        evidence = 0.10
    if targetHit and (queryHit or bridgeHit):
        evidence = min(1.0, evidence + 0.08)
    status = searchReliabilityStatus(polarity, evidence, spanScore, frameScore, leakScore, boundScore)
    score = base * 0.01
    score += evidence * 9.0
    score += boundScore * 11.0
    score += (1.0 if targetHit else 0.0) * 2.0
    score += (1.0 if queryHit or bridgeHit else 0.0) * 1.0
    score += 1.5
    if status == "weak":
        score -= 2.0
    elif status == "abstain":
        score -= 10.0
    return (
        score,
        evidence,
        spanScore,
        frameScore,
        leakScore,
        boundScore,
        status,
        target,
        payload.ref,
        evidenceSnippet(text, surface, target, polarity, model),
    )


def search(query: str, polarity: str, model: Model):
    surface = querySurface(query)
    best = route(surface, model)[0]
    target = best[1]
    seed = inferSignature(surface, model) + inferSignature(target, model)
    seed[f"surf:{surface}"] += 5
    seed[f"surf:{target}"] += 4
    if polarity:
        seed[f"rel:{polarity}"] += 7
    candidates: Counter[int] = Counter()
    for atom, weight in seed.most_common(80):
        for unitId in model.unitPostings.get(atom, ()):
            candidates[unitId] += min(weight, 4)
    if polarity:
        for term in searchEvidenceTerms(surface, target, "", model):
            for unitId in model.relationBoundPostings.get((term, polarity), ())[:SEARCH_RELATION_POSTING_LIMIT]:
                candidates[unitId] += 17
            for unitId in model.relationFramePostings.get((term, polarity), ())[:SEARCH_RELATION_POSTING_LIMIT]:
                candidates[unitId] += 14
            for unitId in model.relationSpanPostings.get((term, polarity), ())[:SEARCH_RELATION_POSTING_LIMIT]:
                candidates[unitId] += 9
    hits = []
    for unitId, base in candidates.most_common(SEARCH_CANDIDATE_LIMIT):
        hit = scoreSearchHit(unitId, base, seed, surface, target, polarity, model)
        if hit is not None:
            hits.append(hit)
    if polarity and not any(hit[6] == "reliable" for hit in hits):
        sideCandidates: Counter[int] = Counter()
        for term in searchEvidenceTerms(surface, target, "", model):
            for unitId in model.sideRelationBoundPostings.get((term, polarity), ())[:SIDE_FALLBACK_LIMIT]:
                sideCandidates[unitId] += 24
        for unitId, base in sideCandidates.most_common(SIDE_FALLBACK_LIMIT):
            hit = scoreSideSearchHit(unitId, base, surface, target, polarity, model)
            if hit is not None:
                hits.append(hit)
    statusRank = {"reliable": 2, "weak": 1, "abstain": 0}
    return sorted(hits, key=lambda row: (statusRank.get(row[6], 0), row[0]), reverse=True)[:3]


def main() -> None:
    started = time.perf_counter()
    print(
        f"[config] files={MAX_FILES_PER_SOURCE} rows={MAX_RECORDS_PER_SOURCE} units={MAX_UNITS} windows={MAX_WINDOWS_PER_RECORD}"
    )
    model = buildModel()
    print("[coordinate] 사=0.%05d 과=0.%05d 는=0.%05d" % (ord("사"), ord("과"), ord("는")))
    print(f"[coordinate] 사과={coordDecimal('사과')} 사과는(raw)={coordDecimal('사과는')}")
    for surface in ("대손충당금", "손실충당금", "복구충당금", "매출채권", "대출채권"):
        sig = inferSignature(surface, model)
        print(
            f"[surface] {surface} coord={coordDecimal(surface)} sig={len(sig)} xp={sum(k.startswith(('xp:', 'relay:xp')) for k in sig)} el={sum(k.startswith(('el:', 'relay:el')) for k in sig)} cx={sum(k.startswith('cx:') for k in sig)}"
        )
    print(
        "[laneProbe] "
        + " | ".join(
            formatLaneProfile(surface, model)
            for surface in (
                "외상매출금",
                "매출채권",
                "매출액",
                "영업손익",
                "영업이익",
                "복구충당금",
                "대손충당금",
                "대출채권",
            )
        )
    )
    pos = 0
    bad = 0
    print("[routes:positive]")
    for surface, expected in POSITIVE_PROBES:
        rows = route(surface, model)
        ok = rows[0][1] == expected and rows[0][8]
        pos += int(ok)
        print(f"  {surface}->{expected} ok={ok} {preview(rows)}")
    print("[routes:negative]")
    for surface, forbidden in NEGATIVE_PROBES:
        rows = route(surface, model)
        targetRow = next(row for row in rows if row[1] == forbidden)
        isBad = rows[0][1] == forbidden and targetRow[8]
        bad += int(isBad)
        print(
            f"  {surface}-/->{forbidden} bad={isBad} "
            f"forbidden={targetRow[0]:.3f}/xp{targetRow[2]:.3f}/ct{targetRow[3]:.3f}/el{targetRow[4]:.3f}/cp{targetRow[7]:.3f} "
            f"top={preview(rows, 2)}"
        )
    searchOk = 0
    reliableSearch = 0
    print("[search]")
    for query, expected, polarity in SEARCH_PROBES:
        rows = route(querySurface(query), model)
        hits = search(query, polarity, model)
        ok = rows[0][1] == expected
        searchOk += int(ok)
        reliable = bool(hits and hits[0][6] == "reliable")
        reliableSearch += int(ok and reliable)
        print(
            f"  {query} route={rows[0][1]} expected={expected} ok={ok} accepted={rows[0][8]} "
            f"hit={(hits[0][0] if hits else 0):.2f} ev={(hits[0][1] if hits else 0):.2f} "
            f"sp={(hits[0][2] if hits else 0):.2f} fr={(hits[0][3] if hits else 0):.2f} "
            f"lk={(hits[0][4] if hits else 0):.2f} bd={(hits[0][5] if hits else 0):.2f} "
            f"status={(hits[0][6] if hits else 'abstain')} text={(hits[0][9] if hits else '')}"
        )
    print(
        f"[summary] positiveHits={pos}/{len(POSITIVE_PROBES)} badAccepted={bad}/{len(NEGATIVE_PROBES)} "
        f"searchTop1={searchOk}/{len(SEARCH_PROBES)} reliableSearch={reliableSearch}/{len(SEARCH_PROBES)} "
        f"totalSeconds={time.perf_counter() - started:.1f}"
    )


if __name__ == "__main__":
    main()
