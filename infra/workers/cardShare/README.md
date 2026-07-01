# dartlab-card-share, 캐러셀 공유/OG 동적 워커

스레드·인스타·카톡·X 에 캐러셀 링크를 공유하면 **첫 슬라이드가 미리보기(OG)** 로 뜨고, 누르면 **그 캐러셀로 바로 이동**하게 하는 엣지 엔드포인트.

## 왜 워커인가 (정공법)
캐러셀 SSOT 는 hfMedia(`carousels/index.json`, 라이브 발행)다. landing 정적 빌드엔 캐러셀 데이터가 없다.
정적 사이트에 캐러셀마다 OG HTML 을 굽는 방식은 라이브 데이터를 정적 빌드에 복사·박제(drift + 캐러셀마다
재배포)라 우회다. 이 워커는 요청 시점에 SSOT 를 라이브로 읽어 OG 만 낸다. **워커·landing 재배포 0**.
`/cards` 가 브라우저에서 hfMedia 를 읽는 것과 동일 원리를 크롤러용으로 서버사이드에서 하는 것.

## 동작
- `GET /c/<slug>`:
  1. `carousels/index.json` 라이브 read(엣지 캐시 10분, index 는 가변).
  2. slug 로 캐러셀 → `og:title`(제목) · `og:description`(캡션 첫 문단) · `og:image`(첫 슬라이드).
  3. 크롤러는 메타만 읽고 워커 페이지에 머문다(canonical=self). 사람은 **JS(`location.replace`)로만** `LANDING_BASE/cards?post=<slug>` 로 이동.
- 없는 slug → `LANDING_BASE/cards?post=<slug>` 로 302 (graceful).

## ⚠ OG 회귀 가드 2 가지 (실전에서 부서졌던 지점)

### (A) 크롤러 리다이렉트 금지
`<meta http-equiv="refresh">` 를 쓰면 크롤러(스레드·페북)가 **따라가서** OG 없는 landing SPA
(`github.io/cards`)로 넘어가 미리보기가 빈다(도메인이 github.io 로 뜨고 이미지·제목 없음). 크롤러는 JS 를 안
돌리지만 meta refresh 는 따라간다. 사람 이동은 **JS(`location.replace`)로만**, `canonical` 도 **self**(워커
shareUrl)로 둬 Meta 가 OG 를 landing 으로 재귀속하지 않게 한다. JS 꺼진 사람은 body 폴백 링크로 이동.

### (B) og:image = wsrv.nl 변환 JPEG 직접 링크
hfMedia 원본은 webp 다. og:image 를 그대로 두면 두 가지가 겹쳐 미리보기가 빈다:
1. **WebP 미지원 크롤러** (특히 카톡): WebP OG 를 안 띄운다.
2. **HF Xet 이관**: `resolve/main` 이 302 크로스도메인 리다이렉트(`us.aws.cdn.hf.co/xet-bridge-us/...`) +
   `Content-Type: text/plain` + `Expires` 서명 만료 + `Cache-Control: no-store` 라 크롤러가 이미지로 인식·
   캐시 못 한다.

그래서 og:image 를 `https://wsrv.nl/?url=<HF원본>&output=jpg&w=1080&h=1350&fit=cover&q=88` 로 낸다.
wsrv(images.weserv.nl, 무료 이미지 CDN)가 HF resolve 302 를 서버사이드에서 풀고 1080x1350 4:5 baseline
JPEG 로 변환해 **안정 200 image/jpeg** 로 서빙한다. 크롤러(Meta 등)는 wsrv 에서 바로 받는다.
HTML 에는 `&` 가 `&amp;` 로 이스케이프돼 나가고(정상), 크롤러가 디코드해 올바른 URL 로 fetch 한다.

> 워커가 직접 이미지를 프록시(`/og/<slug>`)하려 했으나 **Cloudflare Worker → wsrv 아웃바운드가 막혀**
> webp 폴백만 돼 제거했다. Meta → wsrv 경로는 정상이라 og:image 를 wsrv 로 직접 가리키는 게 확실히 뜬다.

## 배포
```
cd infra/workers/cardShare
wrangler deploy   # CLOUDFLARE_API_TOKEN·CLOUDFLARE_ACCOUNT_ID 는 repo .env 에 있음
```
secret(HF)은 불필요(공개 dartlab-media 만 읽음). 배포 후 워커 URL 을 landing 빌드 env
`VITE_DARTLAB_CARD_SHARE_BASE` 에 넣으면 /cards 공유 버튼이 `/c/<slug>` 링크를 복사한다(미설정 시
`/cards?post=<slug>` 딥링크로 graceful, OG 미리보기만 일반).

검증(크롤러 관점):
```
curl -s -A "facebookexternalhit/1.1" <worker>/c/<slug> | grep -E 'og:image"|http-equiv|canonical'
# 기대: og:image = wsrv jpg URL · http-equiv(refresh) 없음 · canonical = 워커 self
# og:image 를 HTML 디코드(&amp;→&)한 URL 을 curl → 200 image/jpeg
```

## 플랫폼 캐시 재스크랩
페북/카톡/스레드는 한 번 스크랩한 URL 을 캐시한다. 고치기 전에 공유한 링크는 옛 미리보기가 남는다.
- 페북/스레드: [Sharing Debugger](https://developers.facebook.com/tools/debug/) 에서 URL 넣고 "Scrape Again".
- 카톡: URL 뒤 더미 쿼리(`?v=2`) 로 새 캐시 유도.
- **새로 공유하는 링크(또는 한 번도 안 올린 slug)는 바로 정상.**

## 한 번 배포 → 영구
워커 1회 deploy + landing env 1회 설정 후, 새 캐러셀은 데이터(carousels/index.json)만 올리면
그 공유 링크가 즉시 작동한다(추가 배포 0).
