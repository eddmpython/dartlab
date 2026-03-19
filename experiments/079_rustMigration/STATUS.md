# 079 Rust 마이그레이션 실험

## 결론: 현 시점 불필요 (기각)

### 실측 결과 (2026-03-20)

| 접근 | Python | Rust | 배수 |
|------|--------|------|------|
| 잎 함수 batch (splitContentBlocks) | 232ms | 344ms | **0.7x (느림)** |
| 잎 함수 batch (detect_heading) | 221ms | 311ms | **0.7x (느림)** |
| 파이프라인 합성 (Phase 2+3) | 1,453ms | 1,149ms | **1.3x** |

### 왜 효과 없는가

1. Python `@lru_cache` — 40기간 반복 heading이 캐시 히트 → 사실상 0비용
2. Python `re` 모듈이 C 구현 — Rust regex와 순수 속도 차이 미미
3. FFI 문자열 복사 오버헤드 — Python str ↔ Rust String 변환 비용
4. 종목당 3초가 사용자 체감 충분히 빠름

### 코드 구조

```
079_rustMigration/
├── Cargo.toml
├── STATUS.md
└── src/
    ├── lib.rs         # PyO3 모듈 (9개 단일 + 3개 batch + 1개 pipeline)
    ├── content.rs     # _splitContentBlocks (23 테스트)
    ├── heading.rs     # _detect_heading + normalize + key
    ├── mapper.rs      # normalizeSectionTitle + mapSectionTitle (HashMap + 85 regex)
    ├── chunker.rs     # parseMajorNum
    ├── pipeline.rs    # Phase 2+3 합성 (process_period)
    └── sectionMappings.json
```

### 검증 상태

- Rust 단위 테스트: 23/23 통과
- 실데이터 동일성: 삼성전자 78,231행 Python ≡ Rust (0개 불일치)
- Golden test: `sections/dev/golden_samples.json` (detect_heading 11/11, mapSectionTitle 20/20, parseMajorNum 20/20)

### 재활용 조건

2,000종목 일괄 처리가 필요해지면 이 코드를 기반으로 재검토.
그때는 전체 기간 루프 + DataFrame 조립까지 1개 Rust 함수로 합성해야 의미 있음.
