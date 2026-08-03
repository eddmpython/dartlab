# Architecture

구현을 바꿔도 유지해야 하는 구조와 신뢰 경계를 기록한다. 변하는 파일 목록이나 수기 capability 개수 대신 코드가 강제하는 불변식을 설명한다.

현재 공통 기반은 저장소 루트 `ARCHITECTURE.md`와 Skill OS의 architecture 계약이다.

- [Agent Runtime](agentRuntime.md): 설치형 CLI, 세션, 도구, 근거, 공개 이벤트 경계
- [데이터 작업대](dataWorkbench.md): 수집, 저장, 공개 UI를 잇는 단일 데이터 경로
- [분석 결과 조립](analysisProducts.md): 시뮬레이션, 기대 원장, 리포트의 현재 구조
