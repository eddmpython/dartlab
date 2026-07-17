// HF 데이터셋 resolve base URL 의 단일 SSOT.
//
// 여러 로더(hfRange·dartlabData·duckdb·scan worker 등)가 각자 복제하던 base URL + VITE_DARTLAB_HF_RESOLVE
// override 로직을 여기로 통합한다. 데이터 호출 경로를 한곳에서 관리(SSOT) · 데이터 워크벤치 Phase 0.
//
// 전환(가역, 한 줄): 빌드 env 에 VITE_DARTLAB_HF_RESOLVE 지정 시 전체 로더가 그 base 로 전환.
//   예) Cloudflare hfProxy 워커: VITE_DARTLAB_HF_RESOLVE=https://dartlab-hf-proxy.<sub>.workers.dev/hf
//       (infra/workers/hfProxy · 콜드 HF CDN 403 흡수 + range 보존). 비우면 HF 직결로 즉시 롤백.
const DEFAULT_HF_DATASET_RESOLVE = 'https://huggingface.co/datasets/eddmpython/dartlab-data/resolve';
const DEFAULT_HF_RESOLVE = `${DEFAULT_HF_DATASET_RESOLVE}/main`;

// vite env 안전 접근 · runtime 패키지 tsc 는 vite/client 타입 없이 검사된다 (소비 앱이 번들 시 치환).
const viteEnv = (import.meta as { env?: Record<string, string | undefined> }).env;
export const HF_RESOLVE = (viteEnv?.VITE_DARTLAB_HF_RESOLVE ?? DEFAULT_HF_RESOLVE).replace(/\/+$/, '');

/** 데이터셋 상대 경로 → 절대 resolve URL. (선행 슬래시 정규화) */
export const hfUrl = (path: string): string => `${HF_RESOLVE}/${String(path).replace(/^\/+/, '')}`;

// 레인지(byte-range) 읽기 전용 resolve · 항상 HF 직결(cas-bridge CDN)이 기본. 공동호출(공유 runtime)이라
// public·local 양쪽 parquet range 읽기가 같은 경로를 재사용한다.
//
// 왜 분리하나: 회사 panel parquet(10~13MB)를 hyparquet 가 byte-range 직독하는데, 프록시(HF_RESOLVE)는 206
// 부분응답을 엣지캐시하지 않는다(worker.js 2층 정책: range 는 브라우저 캐시에만 위임). 그래서 프록시 경유
// range 한 건이 ~2.8s, HF 직결은 ~0.38s · 7~9배 차이(실측). 프록시는 range 엔 순수 오버헤드일 뿐 이득이 없다.
// → range 는 직결, 소형 통파일/JSON 씨드는 프록시(엣지캐시·per-file cache-control·403 흡수)로 · worker 가
//   명시한 책임경계와 정확히 일치. HF 직결은 CORS(ACAO echo)도 정상이라 브라우저에서 그대로 동작한다.
// 가역(한 줄): VITE_DARTLAB_HF_RANGE_RESOLVE 지정 시 range 도 그 base 로 전환.
export const HF_RANGE_RESOLVE = (viteEnv?.VITE_DARTLAB_HF_RANGE_RESOLVE ?? DEFAULT_HF_RESOLVE).replace(/\/+$/, '');

/** range 읽기 전용 절대 URL · HF 직결(엣지캐시 불가능한 206 을 프록시에 보내 7~9배 느려지는 것 차단). */
export const hfRangeUrl = (path: string): string => `${HF_RANGE_RESOLVE}/${String(path).replace(/^\/+/, '')}`;

/** immutable HF revision의 원본을 해소한다. Knowledge Universe의 exact content preview 전용. */
export const hfRevisionUrl = (revision: string, path: string): string =>
	`${DEFAULT_HF_DATASET_RESOLVE}/${encodeURIComponent(revision)}/${String(path).replace(/^\/+/, '')}`;

// 회사 hero 이미지 serve SSOT · 전용 media 데이터셋 HF 직결. blog·캐러셀(/cards)·SNS 공용 자산.
// dartlab-data(hf origin)와 **별개 repo**(eddmpython/dartlab-media)라 base 가 다르다 → 평행 resolver.
//   왜 프록시 안 씀: hfProxy `/hf` 라우트는 dartlab-data 전용이라 의존 불가(worker.js 21). 게다가
//   캐시버스트=파일명 콘텐츠해시(`{semantic}.{hash8}.webp`)라 변경=새 파일명=새 URL → staleness 무관,
//   프록시 엣지캐시/TTL 이 줄 이득이 없다. HF CDN 직결이면 CORS(ACAO echo)도 정상이라 <img>·fetch 동작.
//   SSOT(개념): src/dartlab/core/dataConfig.py HF_MEDIA_BASE_URL (TS 는 Python import 불가라 상수 미러 ·
//   둘이 drift 하면 안 됨, 변경 시 동반 수정).
// 가역(한 줄): 빌드 env 에 VITE_DARTLAB_HF_MEDIA_RESOLVE 지정 시 그 base 로 전환(미러/CDN 교체).
const DEFAULT_HF_MEDIA_RESOLVE = 'https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main';
export const HF_MEDIA_RESOLVE = (viteEnv?.VITE_DARTLAB_HF_MEDIA_RESOLVE ?? DEFAULT_HF_MEDIA_RESOLVE).replace(
	/\/+$/,
	''
);

/** 중앙 미디어 객체와 manifests 상대경로를 절대 resolve URL로 바꾼다. */
export const hfMediaUrl = (path: string): string => `${HF_MEDIA_RESOLVE}/${String(path).replace(/^\/+/, '')}`;
