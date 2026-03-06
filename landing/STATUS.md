# landing/ 현황

## 기술 스택
- SvelteKit 5 + TypeScript
- Tailwind CSS 4
- Adapter Static (GitHub Pages)
- Lucide Svelte (아이콘)

## 브랜딩
- Primary: Amber (#f59e0b) — 금융 데이터, 통찰
- Accent: Blue (#3b82f6) — 신뢰, 분석
- Background: Stone Dark (#0c0a09)
- 태그라인: "공시의 숫자 너머를 읽다"
- 폰트: Pretendard Variable (한글), Inter (영문), JetBrains Mono (코드)

## 섹션 구성
```
+page.svelte
├── Header        — 고정 네비게이션
├── Hero          — 메인 타이틀, 배지, 통계, CTA
├── Problem       — 기존 도구 vs DartLab 비교
├── Alignment     — 공시 수평 정렬 시각화
├── Layers        — 3개 분석 레이어 카드
├── CodeDemo      — 코드 예제 (syntax highlight)
├── Install       — 설치 방법 (pip, uv)
├── CTA           — 행동 유도
└── Footer        — 링크, Buy Me a Coffee
```

## 배포
- GitHub Actions (`docs.yml`) → GitHub Pages
- BASE_PATH: `/dartlab`
- URL: https://eddmpython.github.io/dartlab/

## 빌드
```bash
cd landing
npm install
npm run build   # → build/ 폴더
npm run dev     # 로컬 개발 서버
```

## 진행 상태
- [x] 프로젝트 초기화 (SvelteKit + Tailwind)
- [x] 8개 섹션 컴포넌트 구현
- [x] 빌드 성공 확인
- [ ] favicon, OG 이미지 생성
- [ ] 블로그 시스템 (추후)
