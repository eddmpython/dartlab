# 이미지 출처와 역할

이 에피소드의 배경/커버 이미지는 아직 수급 전이다(발행 대기).

수급 후 채울 것:
- `source-gray.webp`: 재사용 원본 배경. Openverse(`blog/_scripts/fetch_cc0_images.py`) 실사 또는 image_gen. 주제 = 자사주/금고/소각. CC0 또는 라이선스 명시.
- `cover.jpg`: 정사각 RSS 커버(원본 배경 흑백 처리 + 짧은 제목). `_lib/render_episode_image.py` 로 생성.
- `static-video.jpg`: 16:9 유튜브 정적 영상 이미지. 같은 원본에서 생성.

렌더 명령:
`uv run python -X utf8 blog/_podcasts/_lib/render_episode_image.py --episode P05-economy-treasury-stock-cancellation`

| 파일 | 출처 | 라이선스 | 역할 |
|---|---|---|---|
| source-gray.webp | (수급 전) | | 재사용 원본 배경 |
| cover.jpg | source-gray 파생 | | RSS 정사각 커버 |
| static-video.jpg | source-gray 파생 | | 16:9 정적 영상 이미지 |
