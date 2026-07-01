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
  2. slug 로 캐러셀 → `og:title`(제목) · `og:description`(캡션 첫 문단) · `og:image`(워커 `/og/<slug>` 프록시).
  3. 크롤러는 메타만 읽고 워커 페이지에 머문다(canonical=self). 사람은 **JS(`location.replace`)로만** `LANDING_BASE/cards?post=<slug>` 로 이동. ⚠ `<meta http-equiv="refresh">` 는 쓰지 않는다(크롤러가 따라가 OG 없는 landing SPA 로 넘어가 미리보기가 빔).
- `GET /og/<slug>` (또는 `/og/<slug>.webp`): 첫 슬라이드 이미지를 워커가 **직접 프록시**해 안정 200 `image/webp` 로 서빙.
  - 이슈 카드: 이미지가 `issues/<slug>/...` hfMedia 경로라 그대로.
  - 회사 카드: `companies/index.json` 으로 semantic 파일명 해석.
- 없는 slug → `/c` 는 `/cards` 로 리다이렉트, `/og` 는 404 (graceful).

## ⚠ og:image 는 왜 프록시인가 (HF Xet 이관 회귀 가드)
`og:image` 를 hfMedia `resolve/main` URL 로 **직접** 가리키면 크롤러(카톡·페북·스레드·X)가 못 읽는다.
HF 가 Xet 백엔드로 이관한 뒤 resolve 응답이 이렇게 바뀌었다:
1. **302 크로스도메인 리다이렉트** (`us.aws.cdn.hf.co/xet-bridge-us/...`),
2. 리다이렉트 응답 `Content-Type: text/plain` (이미지 아님),
3. 최종 URL 은 `Expires` **서명 만료** + `Cache-Control: no-store`.
크롤러는 이걸 이미지로 인식·캐시하지 못해 미리보기가 빈다. 워커가 서버사이드에서 302 를 풀어 이미지 바이트를
안정된 `Content-Type: image/webp` + 장수명 `Cache-Control` 로 재서빙하면(리다이렉트·만료·no-store·크로스도메인
전부 제거) 문제가 사라진다. og:image 는 워커 자기 오리진 `/og/<slug>.webp` 를 가리킨다.
정적 굽기가 아니라 요청 시점 SSOT 라이브 read 라 "런타임-SSOT" 원칙 유지.

## 배포
```
cd infra/workers/cardShare
wrangler deploy
```
secret 불필요(공개 dartlab-media 만 읽음). 배포 후 워커 URL(`https://dartlab-card-share.<account>.workers.dev`)을
landing 빌드 env `VITE_DARTLAB_CARD_SHARE_BASE` 에 넣으면 /cards 공유 버튼이 `/c/<slug>` 링크를 복사한다
(미설정 시 공유 버튼은 `/cards?post=<slug>` 딥링크로 graceful, OG 미리보기만 일반).

배포 후 검증(카톡·페북 캐시 갱신 전 원천 확인):
```
curl -sL <worker>/c/<slug> | grep og:image          # 프록시 URL 가리키는지
curl -s -o /dev/null -w "%{http_code} %{content_type} %{num_redirects}\n" <worker>/og/<slug>.webp
# 기대: 200 image/webp 0  (리다이렉트 0, 이미지 타입)
```
페북/카톡은 자체 캐시가 있어 재공유 시 옛 미리보기가 잠깐 남을 수 있다. 페북은 Sharing Debugger 로 강제 재스크랩,
카톡은 URL 뒤 더미 쿼리(`?v=2`) 로 새 캐시 유도.

## 한 번 배포 → 영구
워커 1회 deploy + landing env 1회 설정 후, 새 캐러셀은 데이터(carousels/index.json)만 올리면
그 공유 링크가 즉시 작동한다(추가 배포 0).
