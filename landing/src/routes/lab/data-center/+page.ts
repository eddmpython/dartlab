// 데이터 센터 (mainPlan/data-download-center) — 브라우저에서 HF parquet 직독 → 다운로드 + 라이브 URL 빌더.
// 클라이언트 전용(parquet range-fetch). prerender 는 정적 셸만, 데이터는 브라우저에서.
export const prerender = true;
export const ssr = false;
