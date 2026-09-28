"""네이버 금융 그룹/상품 수집 — 로컬 개인용 (재배포 금지).

- ``groups`` : 네이버증권 그룹 JSON API (테마·업종) 공통 collector. 목록→편입종목→결합, freshness 저장.
- ``products`` : ETF·ETN 상품 목록 (JSON) — 별 스키마.

호출자는 명시 path 사용 (facade re-export 안 함, alias 금지 룰):
    from dartlab.gather.sources.naver import groups
"""
