# 071_visualization — 시각화 실험 시리즈

## 목표
dartlab Company 데이터 위에 시각화 레이어를 기획·검증한다.
Python(분석) + Svelte(렌더링) 양쪽에서 장기적으로 이어나갈 수 있는 구조를 만든다.

## 핵심 결정 사항

- **차트 라이브러리**: LayerChart 2.0 (@next) — Svelte 5 runes 네이티브, SVG SSR 안전
- **아키텍처**: ChartSpec JSON 프로토콜로 Python↔Server↔Svelte↔AI 4계층 통합
- **Python 분석**: Plotly + ChartSpec spec_xxx() 함수 8개 + chart_from_spec() 변환기
- **AI 통합**: create_chart 도구 (38개 도구 중 22번째) + SSE chart 이벤트
- **통합 전략**: 전략 A (프론트엔드 전환) — 서버 변경 최소, finance 블록에 표/차트 토글
- **컬러**: chart.py COLORS 계승 (8색 팔레트)

## 로드맵

### Phase 1: 기반 — 전체 완료
| # | 파일 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 001 | chartLibraryAudit.py | **완료** | **LayerChart 2.0 채택** (9.15점). 차선 D3+Svelte (9.10). Chart.js/ECharts/uPlot 기각 |
| 002 | dataShapeInventory.py | **완료** | 5대 범주 15+ 소스 카탈로그. 재무 시계열 75% 비중. combo→sparkline→radar 순서 확정 |
| 003 | svelteChartPOC.md | **완료** | LayerChart 2.0 POC 설계. 6개 컴포넌트 구조, ChartSpec props 인터페이스, Tailwind 테마 연동 확정 |

### Phase 2: 재무 차트 — 전체 완료
| # | 파일 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 004 | financeTrend.py | **완료** | IS combo 10/10종목 성공. 매출+영업이익 bar+line. BS stacked 2시리즈 |
| 005 | ratioSparklines.py | **완료** | 35개 비율 × 39분기 시계열. 5/5종목 전부 10+ 유효 포인트 |
| 006 | insightRadar.py | **완료** | 10/10종목 레이더 성공. 비교 레이더(3종목 overlay) ChartSpec 생성 |
| 007 | cashflowWaterfall.py | **완료** | 5/5종목 워터폴 성공. 기초→영업→투자→재무→기말 브릿지. 연도별 비교 |

### Phase 3: 문서·텍스트 시각화 — 전체 완료
| # | 파일 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 008 | diffHeatmap.py | **완료** | 3/3종목 히트맵 성공. 핫스팟 23~43%. colorScale 3단계 |
| 009 | sectionCoverage.py | **완료** | topic 커버리지 매트릭스. 삼성전자 64topic, 100% 20개, sparse 25개 |
| 010 | timelineAnnotation.py | **완료** | 타임라인 annotation 구조 확정. 메타/기간 컬럼 분리 개선 필요 |

### Phase 4: 통합 설계 — 전체 완료
| # | 파일 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 011 | chartBlockType.py | **완료** | 전략 A(프론트엔드 전환) 채택. 서버 변경 0, TopicRenderer에 토글 추가 |
| 012 | dashboardComposition.py | **완료** | 4차트 대시보드 3/3종목 성공. radar+combo+sparklines ~250ms, diff 포함 ~3.5초 |

### Phase 5: ChartSpec 구현 + AI 통합 — 전체 완료
| # | 파일 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 013 | chartSpecRoundtrip.py | **완료** | 10/10종목 auto_chart() 성공(최소6~최대7개). chart_from_spec() 35/35 왕복 실패0. JSON ~11KB |
| 014 | aiChartTool.py | **완료** | create_chart 도구 등록(38개 중 22번째). auto 7개 차트 10.6KB. 개별/에러 처리 모두 정상 |

### Phase 6: 확장 실험 — 대기
| # | 파일 | 상태 | 목표 |
|---|------|------|------|
| 015 | sseChartEvent.py | 대기 | chart SSE 이벤트 end-to-end 검증 (서버 실행 필요) |
| 016 | affiliateGraph.py | 대기 | 070_affiliateMap 네트워크 그래프 → ChartSpec |
| 017 | multiCompanyCombo.py | 대기 | 복수 기업 비교 combo 차트 |
| 018 | sectorHeatmap.py | 대기 | WICS 11섹터 × 82업종 히트맵 |
| 019 | financeSankey.py | 대기 | 매출→영업이익→순이익 분해 Sankey |
| 020 | reportTimeline.py | 대기 | report 28개 API 시간축 시각화 |
| 021 | edgarComparison.py | 대기 | DART vs EDGAR 병렬 차트 |

## 구현 완료 사항

### chart.py 확장 (Phase A)
- `spec_xxx()` 8개 함수: revenue_trend, cashflow_waterfall, balance_sheet, profitability, dividend, insight_radar, ratio_sparklines, diff_heatmap
- `chart_from_spec(spec)`: ChartSpec → Plotly Figure 범용 변환기 (combo/radar/waterfall/heatmap/sparkline/pie)
- `auto_chart(company)`: 데이터 가용성 기반 자동 ChartSpec 리스트 생성
- `_SPEC_GENERATORS` dict: chart_type → 함수 매핑

### AI 도구 통합 (Phase B)
- `tools_registry.py`: `create_chart` 도구 등록 (chart_type: auto + 8개 개별)
- `streaming.py`: `_on_tool_result`에서 create_chart 결과 감지 → `chart` SSE 이벤트 분리

## 다음 단계 (Svelte UI 구현)

1. `npm install layerchart@next d3-scale d3-shape` — 차트 라이브러리 설치
2. `$lib/chart/` 디렉토리 생성 — colors.js + 6개 차트 컴포넌트
3. TopicRenderer.svelte — finance 블록에 표/차트 토글 추가
4. InsightDashboard.svelte — RadarChart 통합
5. api.js — SSE chart 이벤트 핸들러 추가
6. 대시보드 뷰 구현 (2×2 그리드)

## 성능 참고

| 차트 | 생성 시간 | JSON 크기 | 비고 |
|------|----------|----------|------|
| combo (IS) | ~0ms | 525B | 캐시된 annual 데이터 |
| bar (BS) | ~0ms | 585B | |
| line (수익성) | ~0ms | 944B | ratioSeries 기반 |
| waterfall (CF) | ~0ms | 355B | |
| radar (인사이트) | ~0ms | 295B | insights 캐시 |
| sparkline (비율) | ~0ms | 5.2KB | 20분기 데이터 |
| heatmap (diff) | ~600ms | 2.9KB | diff() 계산 병목 |
| **auto_chart 전체** | **~3.5초** | **~11KB** | diff 제외 시 ~50ms |

## ChartSpec 프로토콜

```json
{
  "chartType": "combo|radar|waterfall|sparkline|heatmap|pie|bar|line",
  "title": "삼성전자 손익 추이",
  "series": [{"name": "매출액", "data": [1,2,3], "color": "#3b82f6", "type": "bar"}],
  "categories": ["2021", "2022", "2023"],
  "options": {"unit": "백만원", "stacked": false, "maxValue": 5},
  "meta": {"source": "finance", "stockCode": "005930", "corpName": "삼성전자"}
}
```
