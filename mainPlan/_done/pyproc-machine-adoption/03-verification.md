# 검증 증거

검증일: 2026-07-23

## 자동 검증

| 게이트 | 결과 | 확인 범위 |
|---|---|---|
| targeted Vitest | PASS | 실행 정책과 마크다운 투영 2 files, 15 tests |
| landing full Vitest | PASS | 22 files, 186 tests |
| Svelte check | PASS | error 0, 기존 warning 109 |
| production build | PASS | worker bundle 포함 static build |
| pyproc Gate A | PASS | exact versions, C 확장, FS, stdout, branch, ASGI |
| pyproc Gate B | PASS | 실제 Chromium COI와 JSPI, branch, 2 process lanes |
| notebook public contract | PASS | 은퇴한 `Company.show`와 비공개 `Company.cik` 예제 제거 |

Gate A에서 DartLab 0.10.9와 `polars`, `pyarrow`, `lxml`, `numpy` import, history branch parent, ASGI `/health` 200을 확인했다.

Gate B에서 pyproc 0.0.10, Pyodide 0.27.5, DartLab 0.10.9, history branch와 2-lane map을 확인했다.

## 실제 제품 smoke

production build를 Vite preview로 띄우고 실제 Chrome에서 확인했다.

1. `dartlab 이야기` 13편의 Python 코드펜스 96개가 production 화면의 CodeMirror 셀 96개로 정확히 투영됐다. 모든 글의 초기 output은 0개였다.
2. `/blog/pick-company-by-code`에는 편집 가능한 Python 셀 13개가 즉시 표시됐고 초기 Python, wheel 요청은 없었다.
3. 첫 셀을 실행해 `dartlab.Company("005930").market`이 `'KR'`을 반환했다.
4. 첫 셀을 `polars` 버전, `edited-ok`, `21 * 2` 코드로 교체해 다시 실행했고 `polars=1.18.0`, `edited-ok`, `42`가 나왔다.
5. 전체 화면은 마크다운 셀을 포함한 23셀, 그중 코드 셀 13개로 생성됐다. 초기 output과 중복 정의 오류는 0개였고 툴바는 순차 실행 상태였다.
6. 인라인 실행 뒤 전체 화면 첫 셀을 실행해 새 machine에서 `'KR'`을 확인했다. `c`와 `code`를 다시 정의하는 네 번째 코드 셀도 dataframe을 반환했고 오류와 중복 정의 배너는 0개였다.
7. 두 번째 코드 셀을 `print("second-cell-only")`, `6 * 7`로 바꿔 개별 실행했고 `second-cell-only`, `42`가 나왔다.
8. reactive 전환 시 중복 정의 배너 7개가 나타났고 순차 모드로 돌아오자 모두 사라졌다.
9. 실행 정책이 없고 `Multiple definitions error:` 출력이 저장된 옛 IndexedDB 문서를 다시 열었다. `sourceKind: blog-post`, `mode: sequential`, `autoRun: false`로 정규화됐고 옛 오류 출력만 제거됐으며 편집 코드와 정상 출력은 보존됐다.
10. 마이그레이션 뒤 첫 셀을 다시 실행해 `'KR'`을 확인했고 Chrome console 및 page error는 0개였다.
11. 일반 non-COI 페이지에서 발견된 `SharedArrayBuffer is not defined` 회귀를 수정한 뒤 같은 smoke를 다시 통과했다.

## 발견해 수정한 회귀

- 초기 사용자 오류: Pyodide가 DartLab 지연 import의 `polars`를 자동 설치하지 못했다.
- 실제 제품 smoke 오류: 일반 페이지에는 `SharedArrayBuffer` 전역이 없는데 `instanceof SharedArrayBuffer`가 먼저 평가돼 기본 machine boot가 죽었다.
- 유지보수 오류: pyproc 0.0.10을 옛 `Runtime` value와 subpath 계약으로 다루던 gate와 ambient type이 남아 있었다.
- 라우팅 오류: Service Worker `/pyapi`가 base path와 multi-tab 요청 client를 잃었다.
- 비용 오류: 블로그 진입만으로 runtime과 데이터를 조용히 prewarm했다.

## 알려진 제한

- durable history는 비활성이다.
- process pool은 제품 worker에서 비활성이다. Gate B는 upstream 능력 검증용이다.
- hard interrupt는 worker를 재시작하므로 현재 세션 변수를 잃는다.
- 손수 ASGI fallback은 안정화 기간 동안 남아 있다.
- 기존 Svelte a11y warning과 npm audit 취약점은 이 변경 범위 밖의 기존 부채다.
