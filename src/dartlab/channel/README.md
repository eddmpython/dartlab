# channel/ — 외부 채널 전송

> dartlab 결과를 블로그 / SNS / 차트 export 등 *다른 매체* 로 전송.

| 모듈 | 역할 |
|------|------|
| `channel/blog/` | 블로그 자동 발간 (corporate / quant / industry — T12-3 트랙) |
| `channel/sns/` | shorts / reels / carousel 자동 생성 |
| `channel/export/` | 차트 export (PNG / SVG) |

## 룰

- 비즈니스 로직 0
- 외부 publish 는 사용자 명시 지시 필요 (자동 푸시 금지)
- 캐러셀 cards 시퀀스 템플릿화 금지 (memory/engineering.md 11절)

## 관련

- [src/dartlab/skills/specs/runtime/channel.md](../skills/specs/runtime/channel.md)
- [blog/BLOG.md](../../../blog/) — 블로그 운영
