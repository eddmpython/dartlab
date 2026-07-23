# 검증 증거

검증일: 2026-07-23

## 자동 검증

| 게이트 | 결과 | 확인 범위 |
|---|---|---|
| targeted Vitest | PASS | DartLab 의존성, checkpoint adapter, SharedArrayBuffer 부재 |
| landing full Vitest | PASS | 21 files, 178 tests |
| Svelte check | PASS | error 0, 기존 warning 109 |
| production build | PASS | worker bundle 포함 static build |
| pyproc Gate A | PASS | exact versions, C 확장, FS, stdout, branch, ASGI |
| pyproc Gate B | PASS | 실제 Chromium COI와 JSPI, branch, 2 process lanes |

Gate A에서 DartLab 0.10.9와 `polars`, `pyarrow`, `lxml`, `numpy` import, history branch parent, ASGI `/health` 200을 확인했다.

Gate B에서 pyproc 0.0.10, Pyodide 0.27.5, DartLab 0.10.9, history branch와 2-lane map을 확인했다.

## 실제 제품 smoke

production build를 Vite preview로 띄우고 in-app Chromium에서 확인했다.

1. `/blog/pick-company-by-code`에 편집 가능한 Python 셀 13개가 즉시 표시됐다.
2. 초기 페이지에는 실행 output이 없고 Python boot가 시작되지 않았다.
3. 첫 셀을 실행해 `dartlab.Company("005930").market`이 `'KR'`을 반환했다.
4. 첫 셀을 `print("edited-ok")`와 `21 * 2`로 교체해 다시 실행했고 `edited-ok`와 `42`가 나왔다.
5. 일반 non-COI 페이지에서 발견된 `SharedArrayBuffer is not defined` 회귀를 수정한 뒤 같은 smoke를 다시 통과했다.

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
