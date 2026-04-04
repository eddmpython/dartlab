window.BENCHMARK_DATA = {
  "lastUpdate": 1775288309761,
  "repoUrl": "https://github.com/eddmpython/dartlab",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "5c6164e427ba2c6850931f599e105f084dd21489",
          "message": "docs: v0.8.0 CHANGELOG 추가",
          "timestamp": "2026-04-01T15:54:05+09:00",
          "tree_id": "77a52900fc0a63bb45e0b26edb322e19fe8fdd6a",
          "url": "https://github.com/eddmpython/dartlab/commit/5c6164e427ba2c6850931f599e105f084dd21489"
        },
        "date": 1775026501462,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 546869.4490555265,
            "unit": "iter/sec",
            "range": "stddev: 4.99526731478057e-7",
            "extra": "mean: 1.8285899893055917 usec\nrounds: 55701"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 651737.1475012731,
            "unit": "iter/sec",
            "range": "stddev: 6.114281216901017e-7",
            "extra": "mean: 1.5343609058252226 usec\nrounds: 148324"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 529041.3635868324,
            "unit": "iter/sec",
            "range": "stddev: 6.156232310031569e-7",
            "extra": "mean: 1.8902113687673276 usec\nrounds: 128950"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 687179.6400337861,
            "unit": "iter/sec",
            "range": "stddev: 4.0328533838778977e-7",
            "extra": "mean: 1.4552235569011238 usec\nrounds: 139025"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 808302.4108786039,
            "unit": "iter/sec",
            "range": "stddev: 3.9943103116942385e-7",
            "extra": "mean: 1.2371607291298632 usec\nrounds: 188715"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268331.98383657215,
            "unit": "iter/sec",
            "range": "stddev: 7.135564518422637e-7",
            "extra": "mean: 3.7267268169159102 usec\nrounds: 24738"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7320700.001347644,
            "unit": "iter/sec",
            "range": "stddev: 1.2367218723601132e-8",
            "extra": "mean: 136.59895909078546 nsec\nrounds: 73282"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8841629.102834336,
            "unit": "iter/sec",
            "range": "stddev: 1.120439687829756e-8",
            "extra": "mean: 113.10132876750426 nsec\nrounds: 88488"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1487471.3437082495,
            "unit": "iter/sec",
            "range": "stddev: 2.787555935320362e-7",
            "extra": "mean: 672.2818588941763 nsec\nrounds: 177305"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "caf41df1e489c5a933d45c466a42ae710c640f13",
          "message": "refactor: TUI 제거 + textual/vector extras 삭제 (919줄, 의존성 경량화)",
          "timestamp": "2026-04-01T16:16:50+09:00",
          "tree_id": "ce68cc1b17a2518ad0fa0034d1713f7c5801c5bd",
          "url": "https://github.com/eddmpython/dartlab/commit/caf41df1e489c5a933d45c466a42ae710c640f13"
        },
        "date": 1775027867761,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 532566.485312297,
            "unit": "iter/sec",
            "range": "stddev: 4.6044947638294484e-7",
            "extra": "mean: 1.877699832000506 usec\nrounds: 55359"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 674509.050270702,
            "unit": "iter/sec",
            "range": "stddev: 4.432972360534505e-7",
            "extra": "mean: 1.4825597960452395 usec\nrounds: 124147"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 531267.8577643866,
            "unit": "iter/sec",
            "range": "stddev: 4.947244202707225e-7",
            "extra": "mean: 1.882289668733343 usec\nrounds: 119105"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 674411.6432395213,
            "unit": "iter/sec",
            "range": "stddev: 4.0649823555556615e-7",
            "extra": "mean: 1.4827739260202009 usec\nrounds: 126985"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 794643.482131006,
            "unit": "iter/sec",
            "range": "stddev: 3.5204702924063947e-7",
            "extra": "mean: 1.2584259765376626 usec\nrounds: 185529"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268220.7595209965,
            "unit": "iter/sec",
            "range": "stddev: 6.437995030322588e-7",
            "extra": "mean: 3.728272195581936 usec\nrounds: 67536"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7216185.720398385,
            "unit": "iter/sec",
            "range": "stddev: 1.2008899647526808e-8",
            "extra": "mean: 138.5773646558521 nsec\nrounds: 71706"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8999424.345543005,
            "unit": "iter/sec",
            "range": "stddev: 1.4854944243469362e-8",
            "extra": "mean: 111.11821841085352 nsec\nrounds: 88567"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1464902.4255476329,
            "unit": "iter/sec",
            "range": "stddev: 2.8124597076076894e-7",
            "extra": "mean: 682.6393229748147 nsec\nrounds: 32439"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "fb382bcd20546cca1bdebc8dba423e099a6a2679",
          "message": "docs: README에서 camelCase 강제 제거",
          "timestamp": "2026-04-01T16:27:00+09:00",
          "tree_id": "1b021d93df091a7c749da591065f85cc03ee9e2a",
          "url": "https://github.com/eddmpython/dartlab/commit/fb382bcd20546cca1bdebc8dba423e099a6a2679"
        },
        "date": 1775028481131,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542508.8377228001,
            "unit": "iter/sec",
            "range": "stddev: 5.406341781622163e-7",
            "extra": "mean: 1.8432879438379937 usec\nrounds: 46839"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 642523.6619022924,
            "unit": "iter/sec",
            "range": "stddev: 6.063483874450505e-7",
            "extra": "mean: 1.5563629159420256 usec\nrounds: 122775"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 533103.7118186867,
            "unit": "iter/sec",
            "range": "stddev: 5.859796156307281e-7",
            "extra": "mean: 1.8758076108464778 usec\nrounds: 109554"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 683291.4894120331,
            "unit": "iter/sec",
            "range": "stddev: 3.95001567856857e-7",
            "extra": "mean: 1.4635042518391264 usec\nrounds: 165810"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 808142.2478773975,
            "unit": "iter/sec",
            "range": "stddev: 3.6892392636399737e-7",
            "extra": "mean: 1.2374059178647336 usec\nrounds: 166918"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266713.0933150812,
            "unit": "iter/sec",
            "range": "stddev: 7.262094182370551e-7",
            "extra": "mean: 3.749347238902333 usec\nrounds: 62349"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7325177.371361389,
            "unit": "iter/sec",
            "range": "stddev: 1.2390774768421013e-8",
            "extra": "mean: 136.51546567453963 nsec\nrounds: 72701"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8784699.062075103,
            "unit": "iter/sec",
            "range": "stddev: 1.2577627566440155e-8",
            "extra": "mean: 113.83429220895613 nsec\nrounds: 61805"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1394623.9108963136,
            "unit": "iter/sec",
            "range": "stddev: 3.7575093863553367e-7",
            "extra": "mean: 717.0391904132118 nsec\nrounds: 148965"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "be3784515421cd171d7002de61475508b5e26759",
          "message": "refactor: DDG 제거 + 의존성 경량화\n\n- duckduckgo-search 완전 제거 (코드 + 의존성)\n- search.py: Tavily only, DDG fallback 삭제\n- _preGroundSearch: 검색 실패 시 graceful fallback (AI 파이프라인 보호)\n- base 의존성: plotly, mcp, openpyxl, diff-match-patch, fastapi, uvicorn, sse-starlette → optional extras\n- 새 extras: server, mcp, search, export, charts, diff\n- anthropic → ai extras (lazy import이므로 base 불필요)",
          "timestamp": "2026-04-01T16:47:53+09:00",
          "tree_id": "720c2a5a5baa8590a7465dbda9639fef998f67f9",
          "url": "https://github.com/eddmpython/dartlab/commit/be3784515421cd171d7002de61475508b5e26759"
        },
        "date": 1775029724448,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 544708.6051281659,
            "unit": "iter/sec",
            "range": "stddev: 4.776405448611868e-7",
            "extra": "mean: 1.8358439550715513 usec\nrounds: 65071"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 669913.9948819864,
            "unit": "iter/sec",
            "range": "stddev: 5.437235800984829e-7",
            "extra": "mean: 1.4927289288472954 usec\nrounds: 152602"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 531846.9039402992,
            "unit": "iter/sec",
            "range": "stddev: 5.633342963263298e-7",
            "extra": "mean: 1.8802403334329683 usec\nrounds: 129803"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 690574.7637215335,
            "unit": "iter/sec",
            "range": "stddev: 3.787576473671868e-7",
            "extra": "mean: 1.4480691339066059 usec\nrounds: 171204"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 910501.0052803219,
            "unit": "iter/sec",
            "range": "stddev: 1.586373495042346e-7",
            "extra": "mean: 1.0982964260342836 usec\nrounds: 173281"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271385.7820746336,
            "unit": "iter/sec",
            "range": "stddev: 6.799162864937641e-7",
            "extra": "mean: 3.6847914152149315 usec\nrounds: 76717"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7382502.915093933,
            "unit": "iter/sec",
            "range": "stddev: 1.4199210765721408e-8",
            "extra": "mean: 135.45541552790246 nsec\nrounds: 73557"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8866002.650960607,
            "unit": "iter/sec",
            "range": "stddev: 1.6675051586166938e-8",
            "extra": "mean: 112.79040164641196 nsec\nrounds: 77979"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1482768.7981449303,
            "unit": "iter/sec",
            "range": "stddev: 2.7251337434555377e-7",
            "extra": "mean: 674.4139755645554 nsec\nrounds: 198060"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "6514cd32efbaabd2e65c7d223822e4317a30024e",
          "message": "refactor: altair 제거 + extras 3개로 축소\n\n- altairChart.py 삭제 + altair extras 제거\n- tavily extras 제거 (SDK 있는 사용자만 자동 동작)\n- channel 관련 extras 제거\n- 최종 extras: [server], [viz], [all] 3개만\n- base: core + ai(openai/gemini) + openpyxl + diff-match-patch",
          "timestamp": "2026-04-01T17:06:47+09:00",
          "tree_id": "af8e0d6569e143e5501fcf8b013eaf7bc5b19ae4",
          "url": "https://github.com/eddmpython/dartlab/commit/6514cd32efbaabd2e65c7d223822e4317a30024e"
        },
        "date": 1775030857949,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 538668.14287016,
            "unit": "iter/sec",
            "range": "stddev: 4.989229378926532e-7",
            "extra": "mean: 1.8564305560595198 usec\nrounds: 54994"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 675717.0311383978,
            "unit": "iter/sec",
            "range": "stddev: 4.76705806297913e-7",
            "extra": "mean: 1.4799094205384677 usec\nrounds: 144238"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 533707.9242251798,
            "unit": "iter/sec",
            "range": "stddev: 8.444771074816417e-7",
            "extra": "mean: 1.8736840031966326 usec\nrounds: 115248"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 655185.8880593366,
            "unit": "iter/sec",
            "range": "stddev: 6.385323912747566e-7",
            "extra": "mean: 1.5262843999311466 usec\nrounds: 152602"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 909375.31178435,
            "unit": "iter/sec",
            "range": "stddev: 2.1743654939617583e-7",
            "extra": "mean: 1.0996559803650585 usec\nrounds: 176026"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271055.9024223658,
            "unit": "iter/sec",
            "range": "stddev: 6.886101022512106e-7",
            "extra": "mean: 3.6892758691591827 usec\nrounds: 73234"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7195888.778925501,
            "unit": "iter/sec",
            "range": "stddev: 1.3622948174551781e-8",
            "extra": "mean: 138.96824016078264 nsec\nrounds: 72643"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9024428.326346414,
            "unit": "iter/sec",
            "range": "stddev: 1.5332930366257433e-8",
            "extra": "mean: 110.8103431970915 nsec\nrounds: 87559"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1497117.64179396,
            "unit": "iter/sec",
            "range": "stddev: 2.8913985685091587e-7",
            "extra": "mean: 667.9501811238588 nsec\nrounds: 158454"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "3eb2014be91e0c49a2e5c768afab86c0ab24285c",
          "message": "feat: guide server/mcp checker 추가 + optional 의존성 안내 강화\n\n- guide readiness: server, mcp checker 등록 (fastapi/uvicorn/mcp 미설치 안내)\n- dartlab share: 서버 패키지 미설치 시 pip install dartlab[server] 안내\n- MCP: 에러 메시지를 dartlab[server] extras 안내로 통일",
          "timestamp": "2026-04-01T17:15:57+09:00",
          "tree_id": "a0937ba6733625dabc55c8592ec359b3bd85a056",
          "url": "https://github.com/eddmpython/dartlab/commit/3eb2014be91e0c49a2e5c768afab86c0ab24285c"
        },
        "date": 1775031408207,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 524291.5621860495,
            "unit": "iter/sec",
            "range": "stddev: 4.979637782145544e-7",
            "extra": "mean: 1.907335673743193 usec\nrounds: 47570"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 629738.3891471458,
            "unit": "iter/sec",
            "range": "stddev: 4.5986926425425825e-7",
            "extra": "mean: 1.5879609965565213 usec\nrounds: 124348"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 511222.57967832533,
            "unit": "iter/sec",
            "range": "stddev: 5.576034558115965e-7",
            "extra": "mean: 1.9560951330225402 usec\nrounds: 123732"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 669210.198864572,
            "unit": "iter/sec",
            "range": "stddev: 3.8839875390285336e-7",
            "extra": "mean: 1.4942988043168928 usec\nrounds: 148368"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 788500.4248976173,
            "unit": "iter/sec",
            "range": "stddev: 3.9756541183365386e-7",
            "extra": "mean: 1.268230134599921 usec\nrounds: 36244"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 248224.7879927388,
            "unit": "iter/sec",
            "range": "stddev: 6.734625027126616e-7",
            "extra": "mean: 4.028606522686415 usec\nrounds: 57584"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 6821633.752783422,
            "unit": "iter/sec",
            "range": "stddev: 1.377734064079437e-8",
            "extra": "mean: 146.59244929295292 nsec\nrounds: 67101"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 7913149.210603265,
            "unit": "iter/sec",
            "range": "stddev: 1.1389906229457248e-8",
            "extra": "mean: 126.37193781965401 nsec\nrounds: 78996"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1488630.0953787747,
            "unit": "iter/sec",
            "range": "stddev: 2.627043459310693e-7",
            "extra": "mean: 671.7585537900568 nsec\nrounds: 158731"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "9d15e60515ebf64f3cb0cc4d13df0943d90fdb1f",
          "message": "refactor: 엔진 호출방식 전체 재정비 — 엔진(\"그룹\", \"축\") 통일\n\n- analysis: 2단계 호출 지원 — analysis(\"financial\", \"수익성\"), analysis(\"valuation\", \"DCF\") 등\n  - _GROUPS 그룹 매핑 (financial/valuation/forecast/governance)\n  - 영문↔한글 양방향 alias 완전 지원\n  - 기존 1단계 호출 하위호환 유지\n- scan: 2단계 호출 지원 — scan(\"financial\", \"profitability\") 등\n  - _SCAN_GROUPS 그룹 매핑 (financial → 8축)\n  - _financialGuide() 그룹 가이드\n- __init__.py: __all__ 정리 — 축 함수 26개 제거, 엔진 함수만 유지\n- ops/README.md: 엔진 체계 + 호출 패턴 섹션 추가\n- 시스템 프롬프트: 2단계 호출 예시로 전면 변경\n- behavior.md: 엔진 호출 체계 메모리 확정",
          "timestamp": "2026-04-01T18:35:32+09:00",
          "tree_id": "62648d9ab8db23c24ac72a0d21a6a893636cefe4",
          "url": "https://github.com/eddmpython/dartlab/commit/9d15e60515ebf64f3cb0cc4d13df0943d90fdb1f"
        },
        "date": 1775036194800,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 533044.4522149721,
            "unit": "iter/sec",
            "range": "stddev: 5.443810421690161e-7",
            "extra": "mean: 1.8760161480804771 usec\nrounds: 55115"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 648859.16428553,
            "unit": "iter/sec",
            "range": "stddev: 4.784966994618701e-7",
            "extra": "mean: 1.5411664888807068 usec\nrounds: 127486"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 516831.21491099324,
            "unit": "iter/sec",
            "range": "stddev: 5.233365259353283e-7",
            "extra": "mean: 1.9348676534025064 usec\nrounds: 124922"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 678740.977796329,
            "unit": "iter/sec",
            "range": "stddev: 3.968672949270105e-7",
            "extra": "mean: 1.473316084799689 usec\nrounds: 191939"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 862502.1802546512,
            "unit": "iter/sec",
            "range": "stddev: 1.5704834450221853e-7",
            "extra": "mean: 1.1594173590433743 usec\nrounds: 175747"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 265994.62453773635,
            "unit": "iter/sec",
            "range": "stddev: 6.589512114285829e-7",
            "extra": "mean: 3.75947446959828 usec\nrounds: 66274"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7157754.534634754,
            "unit": "iter/sec",
            "range": "stddev: 1.1959985925780787e-8",
            "extra": "mean: 139.70861883586903 nsec\nrounds: 72171"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8819171.77924229,
            "unit": "iter/sec",
            "range": "stddev: 1.0959978726347764e-8",
            "extra": "mean: 113.38933235813627 nsec\nrounds: 88176"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1456138.6706026949,
            "unit": "iter/sec",
            "range": "stddev: 2.7132886964746723e-7",
            "extra": "mean: 686.7477804061756 nsec\nrounds: 171204"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "d95458fdc5999023615f6ec05d6f308d6a05e711",
          "message": "refactor: 0.8 안정화 — 엔진 호출 완전 리팩토링 (v0.8.1)\n\nBreaking changes (하위호환 없음):\n- 루트 축 함수 14개 제거: governance(), forecast(), valuation() 등\n- Company 편의 메서드 4개 제거: c.forecast(), c.valuation() 등\n- __init__.py 700줄 삭제\n\n신규:\n- 2단계 호출 통일: analysis(\"financial\", \"수익성\"), scan(\"financial\", \"profitability\")\n- accessor 패턴: c.analysis.financial.profitability(), dartlab.scan.financial.growth()\n- 한글/영문 양방향 alias 완전 지원\n- 전체 문서/독스트링/AI 패턴/노트북 신 패턴 일괄 변환 (20파일 70곳+)",
          "timestamp": "2026-04-01T19:11:39+09:00",
          "tree_id": "fc71fea9ff89b680b2b789e71034524d8a0b7b05",
          "url": "https://github.com/eddmpython/dartlab/commit/d95458fdc5999023615f6ec05d6f308d6a05e711"
        },
        "date": 1775038349501,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 540402.82514031,
            "unit": "iter/sec",
            "range": "stddev: 5.257282184572826e-7",
            "extra": "mean: 1.850471451070524 usec\nrounds: 48268"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 650517.1539569579,
            "unit": "iter/sec",
            "range": "stddev: 5.079932314905105e-7",
            "extra": "mean: 1.5372384785200701 usec\nrounds: 132188"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 514284.842014101,
            "unit": "iter/sec",
            "range": "stddev: 5.634992421296594e-7",
            "extra": "mean: 1.9444477423905513 usec\nrounds: 116605"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 671873.3324003583,
            "unit": "iter/sec",
            "range": "stddev: 4.1883298727214775e-7",
            "extra": "mean: 1.4883757871850112 usec\nrounds: 128304"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 786487.0385077678,
            "unit": "iter/sec",
            "range": "stddev: 4.6470697177221205e-7",
            "extra": "mean: 1.271476770802655 usec\nrounds: 199641"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267700.0109048105,
            "unit": "iter/sec",
            "range": "stddev: 7.794685429316539e-7",
            "extra": "mean: 3.7355246890728844 usec\nrounds: 69950"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7282168.484606218,
            "unit": "iter/sec",
            "range": "stddev: 1.2282005022765098e-8",
            "extra": "mean: 137.32173350752606 nsec\nrounds: 58921"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8858816.202849528,
            "unit": "iter/sec",
            "range": "stddev: 2.2902557854603967e-8",
            "extra": "mean: 112.88189946624469 nsec\nrounds: 89920"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1435858.1380587597,
            "unit": "iter/sec",
            "range": "stddev: 2.8343181736066246e-7",
            "extra": "mean: 696.447631903227 nsec\nrounds: 168891"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "bf7942cb0ceea98f85f556d4d6f5e3f0100a6e6d",
          "message": "fix: CI install에 [all] extras 추가 (fastapi 누락 해결)",
          "timestamp": "2026-04-01T19:19:15+09:00",
          "tree_id": "c30160f9d2aa337e8d98b6c80668879b48890268",
          "url": "https://github.com/eddmpython/dartlab/commit/bf7942cb0ceea98f85f556d4d6f5e3f0100a6e6d"
        },
        "date": 1775038802673,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 560657.1533238498,
            "unit": "iter/sec",
            "range": "stddev: 3.1887987950254496e-7",
            "extra": "mean: 1.7836212274676442 usec\nrounds: 61166"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 670787.3684593292,
            "unit": "iter/sec",
            "range": "stddev: 2.978442085859358e-7",
            "extra": "mean: 1.4907853770365556 usec\nrounds: 125802"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 564877.1102456064,
            "unit": "iter/sec",
            "range": "stddev: 3.4332678872791596e-7",
            "extra": "mean: 1.7702965509882387 usec\nrounds: 120121"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 693834.348862566,
            "unit": "iter/sec",
            "range": "stddev: 4.015274467132055e-7",
            "extra": "mean: 1.441266206608746 usec\nrounds: 156495"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 838519.2554445482,
            "unit": "iter/sec",
            "range": "stddev: 3.1634698577682675e-7",
            "extra": "mean: 1.1925784572112674 usec\nrounds: 161604"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 291651.8036233887,
            "unit": "iter/sec",
            "range": "stddev: 4.3013575700094134e-7",
            "extra": "mean: 3.428746154065635 usec\nrounds: 65134"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8394269.256245153,
            "unit": "iter/sec",
            "range": "stddev: 2.097670499941156e-8",
            "extra": "mean: 119.12889251866945 nsec\nrounds: 82954"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9875919.300282814,
            "unit": "iter/sec",
            "range": "stddev: 9.912456641533996e-9",
            "extra": "mean: 101.25639645226376 nsec\nrounds: 96516"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1527788.3715435066,
            "unit": "iter/sec",
            "range": "stddev: 1.6763778264464862e-7",
            "extra": "mean: 654.5409158925014 nsec\nrounds: 152789"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "78e415950e94573465b02bcdda25313c9c777ed8",
          "message": "fix: 독스트링 완비 + MCP 2단계 호출 + 노트북/docs 일관성 + spec 재생성",
          "timestamp": "2026-04-01T19:43:16+09:00",
          "tree_id": "7396bac52ba49f03c0c3350c6d3d235c1d232c93",
          "url": "https://github.com/eddmpython/dartlab/commit/78e415950e94573465b02bcdda25313c9c777ed8"
        },
        "date": 1775040247885,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 517771.2937137854,
            "unit": "iter/sec",
            "range": "stddev: 7.223767055949551e-7",
            "extra": "mean: 1.9313546582070305 usec\nrounds: 57007"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 666745.0626719415,
            "unit": "iter/sec",
            "range": "stddev: 4.5339713361305915e-7",
            "extra": "mean: 1.4998236297282188 usec\nrounds: 124301"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 533196.2677609583,
            "unit": "iter/sec",
            "range": "stddev: 5.099265412834542e-7",
            "extra": "mean: 1.8754819950246133 usec\nrounds: 118134"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 679252.0312775116,
            "unit": "iter/sec",
            "range": "stddev: 4.170226710516922e-7",
            "extra": "mean: 1.4722075959334824 usec\nrounds: 186916"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 793804.9566929911,
            "unit": "iter/sec",
            "range": "stddev: 3.7826103182099826e-7",
            "extra": "mean: 1.2597552982863978 usec\nrounds: 198413"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268477.9377599997,
            "unit": "iter/sec",
            "range": "stddev: 6.468027675423469e-7",
            "extra": "mean: 3.7247008388969722 usec\nrounds: 75217"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7307842.479395377,
            "unit": "iter/sec",
            "range": "stddev: 1.2398108975617994e-8",
            "extra": "mean: 136.8392932414077 nsec\nrounds: 71552"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8761917.022295747,
            "unit": "iter/sec",
            "range": "stddev: 1.0993707295517374e-8",
            "extra": "mean: 114.13027508196897 nsec\nrounds: 88410"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1448172.2976904062,
            "unit": "iter/sec",
            "range": "stddev: 2.6141887406705596e-7",
            "extra": "mean: 690.5255690879004 nsec\nrounds: 153799"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "8a6b44f0098c70f6c02dbb17e893481c3258bb06",
          "message": "style: test format",
          "timestamp": "2026-04-01T19:54:30+09:00",
          "tree_id": "a2c2cbc781fbdb833ebb090c1b48ab003bea8a4a",
          "url": "https://github.com/eddmpython/dartlab/commit/8a6b44f0098c70f6c02dbb17e893481c3258bb06"
        },
        "date": 1775040921914,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 541681.4285898193,
            "unit": "iter/sec",
            "range": "stddev: 4.7048507652226406e-7",
            "extra": "mean: 1.8461035346981336 usec\nrounds: 73444"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 645617.9220780352,
            "unit": "iter/sec",
            "range": "stddev: 4.6281590085955523e-7",
            "extra": "mean: 1.5489037181330463 usec\nrounds: 167477"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 530783.5019558882,
            "unit": "iter/sec",
            "range": "stddev: 5.069202249643461e-7",
            "extra": "mean: 1.8840073143100573 usec\nrounds: 142187"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 679102.2230685413,
            "unit": "iter/sec",
            "range": "stddev: 4.565419050928094e-7",
            "extra": "mean: 1.4725323611539272 usec\nrounds: 197629"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 894214.3632843378,
            "unit": "iter/sec",
            "range": "stddev: 1.6336356685770693e-7",
            "extra": "mean: 1.1183000867120105 usec\nrounds: 166058"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267575.5324874511,
            "unit": "iter/sec",
            "range": "stddev: 6.6413280927658e-7",
            "extra": "mean: 3.737262486983553 usec\nrounds: 79783"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7337829.464183813,
            "unit": "iter/sec",
            "range": "stddev: 1.1914794306498314e-8",
            "extra": "mean: 136.28008185268314 nsec\nrounds: 73180"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8930162.199552596,
            "unit": "iter/sec",
            "range": "stddev: 1.0422897931288977e-8",
            "extra": "mean: 111.98004892342273 nsec\nrounds: 89119"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1457887.8617574319,
            "unit": "iter/sec",
            "range": "stddev: 2.5758040021978104e-7",
            "extra": "mean: 685.9238122708118 nsec\nrounds: 174490"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "11276dfa25eb783ca88fa16ca47b38176a9eb774",
          "message": "fix: publish workflow에 [all] extras (fastapi 누락)",
          "timestamp": "2026-04-01T20:11:09+09:00",
          "tree_id": "35d9087a32f4dfbda72f3a8fe9b0de7b88611168",
          "url": "https://github.com/eddmpython/dartlab/commit/11276dfa25eb783ca88fa16ca47b38176a9eb774"
        },
        "date": 1775041913802,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 538712.7178738586,
            "unit": "iter/sec",
            "range": "stddev: 4.5590687794523865e-7",
            "extra": "mean: 1.856276948401566 usec\nrounds: 53519"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 650750.5314730423,
            "unit": "iter/sec",
            "range": "stddev: 4.5417495480935424e-7",
            "extra": "mean: 1.5366871813940663 usec\nrounds: 115527"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 525383.8064000766,
            "unit": "iter/sec",
            "range": "stddev: 5.055451257131359e-7",
            "extra": "mean: 1.903370427139709 usec\nrounds: 99118"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 684180.9058975533,
            "unit": "iter/sec",
            "range": "stddev: 3.9715412618977606e-7",
            "extra": "mean: 1.4616017362953655 usec\nrounds: 178540"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 809270.6844554257,
            "unit": "iter/sec",
            "range": "stddev: 3.9380692792613405e-7",
            "extra": "mean: 1.2356804950532958 usec\nrounds: 164420"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 257508.34799929944,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030623753773631747",
            "extra": "mean: 3.8833692490727354 usec\nrounds: 74879"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7329311.705055372,
            "unit": "iter/sec",
            "range": "stddev: 1.1824168016335594e-8",
            "extra": "mean: 136.43845974107674 nsec\nrounds: 73611"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8896626.112691553,
            "unit": "iter/sec",
            "range": "stddev: 1.0423126765268017e-8",
            "extra": "mean: 112.4021609240656 nsec\nrounds: 88402"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1458542.9994618446,
            "unit": "iter/sec",
            "range": "stddev: 2.619200206510959e-7",
            "extra": "mean: 685.615714016637 nsec\nrounds: 156446"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2e08a17ecdaa901c51e8d8831c8d6a6dfbc0c624",
          "message": "feat: 금융업(은행/보험) 수익성 분석 지원 — 이자수익 기반 marginTrend",
          "timestamp": "2026-04-01T21:23:56+09:00",
          "tree_id": "86d8b72142c5cebd922e3711baa39e1a234eb75d",
          "url": "https://github.com/eddmpython/dartlab/commit/2e08a17ecdaa901c51e8d8831c8d6a6dfbc0c624"
        },
        "date": 1775046283873,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 523244.2297564609,
            "unit": "iter/sec",
            "range": "stddev: 5.338448537445675e-7",
            "extra": "mean: 1.9111534215397665 usec\nrounds: 44922"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 637778.2939717931,
            "unit": "iter/sec",
            "range": "stddev: 5.308764284832097e-7",
            "extra": "mean: 1.5679429818353565 usec\nrounds: 129450"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 510687.1225349824,
            "unit": "iter/sec",
            "range": "stddev: 6.888428307708519e-7",
            "extra": "mean: 1.9581461052633051 usec\nrounds: 126183"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 659292.9538438648,
            "unit": "iter/sec",
            "range": "stddev: 4.29530614045486e-7",
            "extra": "mean: 1.5167764105011536 usec\nrounds: 132381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 793957.3221192278,
            "unit": "iter/sec",
            "range": "stddev: 3.8620353450451655e-7",
            "extra": "mean: 1.2595135432856817 usec\nrounds: 191571"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267552.19783440174,
            "unit": "iter/sec",
            "range": "stddev: 7.254175478549361e-7",
            "extra": "mean: 3.7375884335621796 usec\nrounds: 76255"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7308962.92051586,
            "unit": "iter/sec",
            "range": "stddev: 1.2342321179161812e-8",
            "extra": "mean: 136.8183162064011 nsec\nrounds: 73180"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8654458.568808869,
            "unit": "iter/sec",
            "range": "stddev: 1.5179182537933252e-8",
            "extra": "mean: 115.54737850430682 nsec\nrounds: 77616"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1401936.7400204255,
            "unit": "iter/sec",
            "range": "stddev: 3.1412268349990127e-7",
            "extra": "mean: 713.2989467024244 nsec\nrounds: 163106"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "eac16fe03b9400a6b1a376463afa3e79436ecbc7",
          "message": "feat: AI 종합분석 프롬프트 추가 — 기업 전반 질문에 analysis 3축 자동 실행",
          "timestamp": "2026-04-01T22:01:08+09:00",
          "tree_id": "542910edcffac42c9e2d967b4ca1f3855228f82e",
          "url": "https://github.com/eddmpython/dartlab/commit/eac16fe03b9400a6b1a376463afa3e79436ecbc7"
        },
        "date": 1775048520087,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 535418.767654597,
            "unit": "iter/sec",
            "range": "stddev: 5.053238585145311e-7",
            "extra": "mean: 1.8676969512677006 usec\nrounds: 54219"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 657329.8477685277,
            "unit": "iter/sec",
            "range": "stddev: 4.696070383187414e-7",
            "extra": "mean: 1.5213062412953753 usec\nrounds: 129300"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 525336.5565597758,
            "unit": "iter/sec",
            "range": "stddev: 5.492069458579747e-7",
            "extra": "mean: 1.9035416201541537 usec\nrounds: 132556"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 687160.3950816216,
            "unit": "iter/sec",
            "range": "stddev: 4.181341760640488e-7",
            "extra": "mean: 1.4552643126081488 usec\nrounds: 183824"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 801518.5041112575,
            "unit": "iter/sec",
            "range": "stddev: 3.717834542731818e-7",
            "extra": "mean: 1.247631832416425 usec\nrounds: 185220"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 272752.631605027,
            "unit": "iter/sec",
            "range": "stddev: 6.862759264203339e-7",
            "extra": "mean: 3.66632576234168 usec\nrounds: 60274"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7291357.363166953,
            "unit": "iter/sec",
            "range": "stddev: 1.2025964699607756e-8",
            "extra": "mean: 137.14867482035694 nsec\nrounds: 73341"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8929216.72678852,
            "unit": "iter/sec",
            "range": "stddev: 1.530106162481306e-8",
            "extra": "mean: 111.99190596414829 nsec\nrounds: 88732"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1490547.670015393,
            "unit": "iter/sec",
            "range": "stddev: 2.663969277322776e-7",
            "extra": "mean: 670.8943431441363 nsec\nrounds: 163908"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "1825fee23337c4e289d0e39b53c5997fb3e3205c",
          "message": "fix: VSCode 확장 SSE 안정성 + 새세션 버그 수정 + CI 배포\n\n- sseHandler: onDone 중복 호출 방지 (done 플래그)\n- sseHandler: code_round 이벤트 중복 표시 방지 (replace, not append)\n- stdioProxy: done 이벤트 ID 불일치 시에도 콜백 정리\n- MessageBubble: 중복 실행 표시 제거 (inline-exec → code-rounds 통합)\n- ChatPanel: 새세션 시 스크롤/상태 리셋 (startNewConversation)\n- chatPanelManager: 패널 새 생성 시 newConversation 메시지 전송\n- core.py: maxRounds 5→3 축소\n- vscode.yml: vsce-* 태그 자동 마켓플레이스 배포",
          "timestamp": "2026-04-01T22:33:37+09:00",
          "tree_id": "961ca1e128cbe1ee21c7206e33f19d25e201fab3",
          "url": "https://github.com/eddmpython/dartlab/commit/1825fee23337c4e289d0e39b53c5997fb3e3205c"
        },
        "date": 1775050520841,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 522813.02042643545,
            "unit": "iter/sec",
            "range": "stddev: 4.7214161799751834e-7",
            "extra": "mean: 1.9127297158443841 usec\nrounds: 52615"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 642561.5060826038,
            "unit": "iter/sec",
            "range": "stddev: 4.823525752492011e-7",
            "extra": "mean: 1.5562712526875926 usec\nrounds: 140194"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 515474.97699326114,
            "unit": "iter/sec",
            "range": "stddev: 5.584811415116953e-7",
            "extra": "mean: 1.9399583774811886 usec\nrounds: 124596"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 671636.3029485778,
            "unit": "iter/sec",
            "range": "stddev: 4.857234299357282e-7",
            "extra": "mean: 1.4889010549457489 usec\nrounds: 179534"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 868698.19273509,
            "unit": "iter/sec",
            "range": "stddev: 2.011636512016665e-7",
            "extra": "mean: 1.151147784538963 usec\nrounds: 188644"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 259454.98065967852,
            "unit": "iter/sec",
            "range": "stddev: 8.501583439269771e-7",
            "extra": "mean: 3.85423319859748 usec\nrounds: 66810"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7116302.293936984,
            "unit": "iter/sec",
            "range": "stddev: 2.408719486672593e-8",
            "extra": "mean: 140.52241721827778 nsec\nrounds: 193462"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8724637.236320434,
            "unit": "iter/sec",
            "range": "stddev: 1.2117589006924512e-8",
            "extra": "mean: 114.6179460433067 nsec\nrounds: 57528"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1452890.1616070936,
            "unit": "iter/sec",
            "range": "stddev: 2.68238633438253e-7",
            "extra": "mean: 688.2832759317912 nsec\nrounds: 163106"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "bcc61c89a24df1724fbe371003ce37468077100e",
          "message": "fix: vscode CI npm ci --legacy-peer-deps",
          "timestamp": "2026-04-01T22:37:37+09:00",
          "tree_id": "1364ede0dce6b6a39924f382bd675d125c069e6c",
          "url": "https://github.com/eddmpython/dartlab/commit/bcc61c89a24df1724fbe371003ce37468077100e"
        },
        "date": 1775050711986,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 523768.98863011756,
            "unit": "iter/sec",
            "range": "stddev: 5.329784525611862e-7",
            "extra": "mean: 1.9092386561782373 usec\nrounds: 44143"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 631303.6614110576,
            "unit": "iter/sec",
            "range": "stddev: 4.941893657550484e-7",
            "extra": "mean: 1.5840237608710384 usec\nrounds: 106225"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 507088.86651613814,
            "unit": "iter/sec",
            "range": "stddev: 6.424952729200879e-7",
            "extra": "mean: 1.972040930163421 usec\nrounds: 93232"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 683046.054372227,
            "unit": "iter/sec",
            "range": "stddev: 3.866750119107581e-7",
            "extra": "mean: 1.4640301244680762 usec\nrounds: 123886"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 790492.2148376363,
            "unit": "iter/sec",
            "range": "stddev: 3.75647317730734e-7",
            "extra": "mean: 1.2650345964575953 usec\nrounds: 159236"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 258452.30506508163,
            "unit": "iter/sec",
            "range": "stddev: 7.028838778606718e-7",
            "extra": "mean: 3.8691858435860618 usec\nrounds: 58221"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7179895.321309566,
            "unit": "iter/sec",
            "range": "stddev: 1.3440364807370937e-8",
            "extra": "mean: 139.2777965762329 nsec\nrounds: 69392"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8096694.228181633,
            "unit": "iter/sec",
            "range": "stddev: 1.1510787912166854e-8",
            "extra": "mean: 123.50719587746879 nsec\nrounds: 80724"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1459703.7390599842,
            "unit": "iter/sec",
            "range": "stddev: 2.9118971698959016e-7",
            "extra": "mean: 685.0705202988499 nsec\nrounds: 138485"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "ea77be8bdfc949c68892ec19dc6c8b19281f8709",
          "message": "fix: lint F541/F401 수정 + publish.yml vsce 태그 제외",
          "timestamp": "2026-04-01T22:50:15+09:00",
          "tree_id": "faaa733ac2fe513337b0a665796fa74fb0bcde44",
          "url": "https://github.com/eddmpython/dartlab/commit/ea77be8bdfc949c68892ec19dc6c8b19281f8709"
        },
        "date": 1775051456714,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 573363.5645439099,
            "unit": "iter/sec",
            "range": "stddev: 3.3028761030680866e-7",
            "extra": "mean: 1.7440940824265039 usec\nrounds: 60075"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 699403.9650181864,
            "unit": "iter/sec",
            "range": "stddev: 2.653829788472972e-7",
            "extra": "mean: 1.4297888631128899 usec\nrounds: 136968"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 566010.7301335281,
            "unit": "iter/sec",
            "range": "stddev: 2.89792752954824e-7",
            "extra": "mean: 1.766750958527039 usec\nrounds: 111620"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 758835.190941174,
            "unit": "iter/sec",
            "range": "stddev: 2.2390842392545088e-7",
            "extra": "mean: 1.3178092053950636 usec\nrounds: 165728"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 883839.3947129113,
            "unit": "iter/sec",
            "range": "stddev: 2.2299132640270393e-7",
            "extra": "mean: 1.1314272773786238 usec\nrounds: 184468"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 287972.25486417086,
            "unit": "iter/sec",
            "range": "stddev: 3.9893314428127583e-7",
            "extra": "mean: 3.4725567588852417 usec\nrounds: 71099"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8542059.31182703,
            "unit": "iter/sec",
            "range": "stddev: 8.133146609574107e-9",
            "extra": "mean: 117.06778933452682 nsec\nrounds: 77298"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9884927.407840794,
            "unit": "iter/sec",
            "range": "stddev: 8.780200429892177e-9",
            "extra": "mean: 101.16412177258813 nsec\nrounds: 85963"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1513704.6692143767,
            "unit": "iter/sec",
            "range": "stddev: 1.639614301816411e-7",
            "extra": "mean: 660.6308484990055 nsec\nrounds: 171645"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "56ec579e726db681b8e5f52adeeae28446befa4b",
          "message": "feat: quant 기술적 분석 프롬프트 추가 — 재무+기술적 교차 검증 패턴",
          "timestamp": "2026-04-01T22:57:00+09:00",
          "tree_id": "0c1b4a7bbe9ddf6f3c9ee773a40f41c4b8254ae5",
          "url": "https://github.com/eddmpython/dartlab/commit/56ec579e726db681b8e5f52adeeae28446befa4b"
        },
        "date": 1775051872028,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 526789.9762305735,
            "unit": "iter/sec",
            "range": "stddev: 5.200231773964986e-7",
            "extra": "mean: 1.8982897266866456 usec\nrounds: 54189"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 610645.3192790098,
            "unit": "iter/sec",
            "range": "stddev: 5.381466376545457e-7",
            "extra": "mean: 1.6376118319889885 usec\nrounds: 132556"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 517223.3559661252,
            "unit": "iter/sec",
            "range": "stddev: 5.298225343270399e-7",
            "extra": "mean: 1.9334007029363414 usec\nrounds: 130311"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 656603.5243510106,
            "unit": "iter/sec",
            "range": "stddev: 4.049779634698691e-7",
            "extra": "mean: 1.5229890838438673 usec\nrounds: 182482"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 783014.1295416835,
            "unit": "iter/sec",
            "range": "stddev: 3.778477137533585e-7",
            "extra": "mean: 1.277116162112328 usec\nrounds: 189072"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267809.07197114866,
            "unit": "iter/sec",
            "range": "stddev: 6.555587429847256e-7",
            "extra": "mean: 3.734003454923032 usec\nrounds: 69176"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7230667.4834058415,
            "unit": "iter/sec",
            "range": "stddev: 1.2809929481062478e-8",
            "extra": "mean: 138.29981841855806 nsec\nrounds: 55237"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8769998.502710339,
            "unit": "iter/sec",
            "range": "stddev: 1.1356124780447483e-8",
            "extra": "mean: 114.0251049861586 nsec\nrounds: 88488"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1428707.331556034,
            "unit": "iter/sec",
            "range": "stddev: 3.13806836547482e-7",
            "extra": "mean: 699.9334138720208 nsec\nrounds: 167197"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "091643c26ee03dc2a829cc08448f3bedb48bbf7e",
          "message": "style: ruff format credit/creditRating/scorecard/review",
          "timestamp": "2026-04-01T23:02:31+09:00",
          "tree_id": "a67df0a9a4939ed50eca1c744744c416fe99291f",
          "url": "https://github.com/eddmpython/dartlab/commit/091643c26ee03dc2a829cc08448f3bedb48bbf7e"
        },
        "date": 1775052199918,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 538284.3884940146,
            "unit": "iter/sec",
            "range": "stddev: 5.154852421009303e-7",
            "extra": "mean: 1.8577540448418917 usec\nrounds: 54514"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 656263.6952579968,
            "unit": "iter/sec",
            "range": "stddev: 6.279392502857991e-7",
            "extra": "mean: 1.5237777241461914 usec\nrounds: 132574"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 535922.1881812145,
            "unit": "iter/sec",
            "range": "stddev: 5.766858261285017e-7",
            "extra": "mean: 1.8659425230997606 usec\nrounds: 128469"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 657533.2493088031,
            "unit": "iter/sec",
            "range": "stddev: 7.957406386457597e-7",
            "extra": "mean: 1.5208356399485454 usec\nrounds: 162576"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 925875.0532371249,
            "unit": "iter/sec",
            "range": "stddev: 1.7346101673375537e-7",
            "extra": "mean: 1.0800593411645696 usec\nrounds: 174186"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269975.79066463996,
            "unit": "iter/sec",
            "range": "stddev: 7.011983531778673e-7",
            "extra": "mean: 3.704035823131214 usec\nrounds: 77436"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7509345.09145037,
            "unit": "iter/sec",
            "range": "stddev: 1.2492585936556078e-8",
            "extra": "mean: 133.1674051227892 nsec\nrounds: 73121"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8678110.123749489,
            "unit": "iter/sec",
            "range": "stddev: 1.1493021759861073e-8",
            "extra": "mean: 115.23246256846728 nsec\nrounds: 86491"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1466799.570730035,
            "unit": "iter/sec",
            "range": "stddev: 2.967511122589225e-7",
            "extra": "mean: 681.7564035025549 nsec\nrounds: 174826"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "245ea57013104b651338f832ef2d1a0c2d7a974c",
          "message": "refactor: AI 프롬프트 — review 금지, analysis 기반 6막 서사 해석 유도 (#28)",
          "timestamp": "2026-04-01T23:07:32+09:00",
          "tree_id": "9ccd7fd1afff9994aa7f0cf26aab5de680724235",
          "url": "https://github.com/eddmpython/dartlab/commit/245ea57013104b651338f832ef2d1a0c2d7a974c"
        },
        "date": 1775052507454,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 535616.0616177594,
            "unit": "iter/sec",
            "range": "stddev: 5.210777848129696e-7",
            "extra": "mean: 1.867008985838902 usec\nrounds: 54753"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 649083.3121944977,
            "unit": "iter/sec",
            "range": "stddev: 4.750380169914577e-7",
            "extra": "mean: 1.5406342779312592 usec\nrounds: 27983"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520375.96363884833,
            "unit": "iter/sec",
            "range": "stddev: 5.433579784531155e-7",
            "extra": "mean: 1.921687529545505 usec\nrounds: 124767"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675199.3801377225,
            "unit": "iter/sec",
            "range": "stddev: 3.9450820596315376e-7",
            "extra": "mean: 1.4810440136897445 usec\nrounds: 194553"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 895471.7843693487,
            "unit": "iter/sec",
            "range": "stddev: 3.9709697773675965e-7",
            "extra": "mean: 1.1167297702230419 usec\nrounds: 165810"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266622.8796862255,
            "unit": "iter/sec",
            "range": "stddev: 7.407085195303101e-7",
            "extra": "mean: 3.7506158555366578 usec\nrounds: 80691"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7225757.339353316,
            "unit": "iter/sec",
            "range": "stddev: 1.2131737492455309e-8",
            "extra": "mean: 138.39379777587396 nsec\nrounds: 71297"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8965752.464523312,
            "unit": "iter/sec",
            "range": "stddev: 1.1122414112540807e-8",
            "extra": "mean: 111.53553524446623 nsec\nrounds: 88567"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1421914.5241062944,
            "unit": "iter/sec",
            "range": "stddev: 5.030843043658204e-7",
            "extra": "mean: 703.2771541795191 nsec\nrounds: 160979"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "7173b8ba5ca65c7dbad203547338085f76bdd124",
          "message": "docs: ops/credit.md 현행화 — 보고서 7섹션 구조 + 발간 규칙 + 코드 구조 반영",
          "timestamp": "2026-04-01T23:28:36+09:00",
          "tree_id": "f178dbe57d61b2b9d4deec1de2a9104dbe8076ff",
          "url": "https://github.com/eddmpython/dartlab/commit/7173b8ba5ca65c7dbad203547338085f76bdd124"
        },
        "date": 1775053782663,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542288.9694569893,
            "unit": "iter/sec",
            "range": "stddev: 4.71364201409388e-7",
            "extra": "mean: 1.8440352954280648 usec\nrounds: 53548"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 656739.8910696809,
            "unit": "iter/sec",
            "range": "stddev: 4.535661602943932e-7",
            "extra": "mean: 1.5226728474970905 usec\nrounds: 124147"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 528857.2506676757,
            "unit": "iter/sec",
            "range": "stddev: 5.932324593532537e-7",
            "extra": "mean: 1.890869414643578 usec\nrounds: 118681"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 668975.6871563519,
            "unit": "iter/sec",
            "range": "stddev: 4.7013263337294655e-7",
            "extra": "mean: 1.4948226358580377 usec\nrounds: 164447"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 890590.9777228885,
            "unit": "iter/sec",
            "range": "stddev: 1.7822409889306882e-7",
            "extra": "mean: 1.1228499109174164 usec\nrounds: 190840"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268446.4776732413,
            "unit": "iter/sec",
            "range": "stddev: 6.554402091952053e-7",
            "extra": "mean: 3.7251373482993544 usec\nrounds: 67995"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7245710.430469539,
            "unit": "iter/sec",
            "range": "stddev: 1.2847434824138355e-8",
            "extra": "mean: 138.01269172927707 nsec\nrounds: 69799"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8864279.70964419,
            "unit": "iter/sec",
            "range": "stddev: 1.1529966359851365e-8",
            "extra": "mean: 112.81232460568867 nsec\nrounds: 89598"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1464987.2168363058,
            "unit": "iter/sec",
            "range": "stddev: 3.1684046596742345e-7",
            "extra": "mean: 682.5998128226245 nsec\nrounds: 167729"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "8d0e2e51744575a773e9fc038c18178b6702ad8d",
          "message": "fix: credit audit/publisher lint F541",
          "timestamp": "2026-04-01T23:32:44+09:00",
          "tree_id": "642068e5c83f2b9d6ee67d6d119399bbc46d074a",
          "url": "https://github.com/eddmpython/dartlab/commit/8d0e2e51744575a773e9fc038c18178b6702ad8d"
        },
        "date": 1775054011821,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 539919.6239264129,
            "unit": "iter/sec",
            "range": "stddev: 4.852466802757048e-7",
            "extra": "mean: 1.8521275309976375 usec\nrounds: 57931"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 664973.4332615159,
            "unit": "iter/sec",
            "range": "stddev: 4.618289255441825e-7",
            "extra": "mean: 1.5038194760582673 usec\nrounds: 135428"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527125.0252439416,
            "unit": "iter/sec",
            "range": "stddev: 5.493991081494401e-7",
            "extra": "mean: 1.8970831436758722 usec\nrounds: 110291"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 687521.7939895159,
            "unit": "iter/sec",
            "range": "stddev: 4.1291465557028103e-7",
            "extra": "mean: 1.4544993464094451 usec\nrounds: 190477"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 899678.9117675319,
            "unit": "iter/sec",
            "range": "stddev: 1.5849695971412583e-7",
            "extra": "mean: 1.1115076578102456 usec\nrounds: 177936"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270563.8155855691,
            "unit": "iter/sec",
            "range": "stddev: 6.382562306498591e-7",
            "extra": "mean: 3.69598572460898 usec\nrounds: 67949"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7506013.089036564,
            "unit": "iter/sec",
            "range": "stddev: 1.1774995449148676e-8",
            "extra": "mean: 133.22651961007375 nsec\nrounds: 53721"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8710995.63996512,
            "unit": "iter/sec",
            "range": "stddev: 1.0937774768585493e-8",
            "extra": "mean: 114.79744007815896 nsec\nrounds: 68088"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1455362.7009054483,
            "unit": "iter/sec",
            "range": "stddev: 2.691805869312812e-7",
            "extra": "mean: 687.1139403104489 nsec\nrounds: 157679"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "302a90eb2705ff28c5a37053eedd30a297e319e9",
          "message": "style: ruff format narrative.py",
          "timestamp": "2026-04-01T23:38:15+09:00",
          "tree_id": "13ba1053934a3226ad93d8e22f06d94f1fb8d471",
          "url": "https://github.com/eddmpython/dartlab/commit/302a90eb2705ff28c5a37053eedd30a297e319e9"
        },
        "date": 1775054343187,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 537513.1687151284,
            "unit": "iter/sec",
            "range": "stddev: 5.201980386056496e-7",
            "extra": "mean: 1.860419536121134 usec\nrounds: 50184"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 620472.9100088021,
            "unit": "iter/sec",
            "range": "stddev: 7.551357497718313e-7",
            "extra": "mean: 1.6116739085124827 usec\nrounds: 124922"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520054.48633048125,
            "unit": "iter/sec",
            "range": "stddev: 5.800409692743259e-7",
            "extra": "mean: 1.922875441486963 usec\nrounds: 113818"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 671449.8225729467,
            "unit": "iter/sec",
            "range": "stddev: 4.3276090862251144e-7",
            "extra": "mean: 1.4893145643677037 usec\nrounds: 179534"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 807313.2274297392,
            "unit": "iter/sec",
            "range": "stddev: 3.8388695136885657e-7",
            "extra": "mean: 1.2386765954321373 usec\nrounds: 185186"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268991.1836378122,
            "unit": "iter/sec",
            "range": "stddev: 7.239905080703243e-7",
            "extra": "mean: 3.7175939615421267 usec\nrounds: 79027"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7282121.824883185,
            "unit": "iter/sec",
            "range": "stddev: 1.2604840459475206e-8",
            "extra": "mean: 137.32261338762225 nsec\nrounds: 72649"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8778720.001200205,
            "unit": "iter/sec",
            "range": "stddev: 1.125364922159248e-8",
            "extra": "mean: 113.91182312037319 nsec\nrounds: 81547"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1458165.5019071496,
            "unit": "iter/sec",
            "range": "stddev: 2.866027216149158e-7",
            "extra": "mean: 685.7932098188372 nsec\nrounds: 168891"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "cac9f648cafc0da0f0157d5af3b9cf3008fe7d78",
          "message": "ci: ruff 0.11.4 → 0.11.6 (로컬 버전 일치)",
          "timestamp": "2026-04-01T23:45:05+09:00",
          "tree_id": "70c529aa8ebbf88c2f1bea943d2bf7de6c7fd7c6",
          "url": "https://github.com/eddmpython/dartlab/commit/cac9f648cafc0da0f0157d5af3b9cf3008fe7d78"
        },
        "date": 1775054756697,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 505092.5499417495,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011101958880657858",
            "extra": "mean: 1.979835180929369 usec\nrounds: 55206"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 658472.129604844,
            "unit": "iter/sec",
            "range": "stddev: 5.12371136982194e-7",
            "extra": "mean: 1.5186671615093421 usec\nrounds: 132031"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 528806.9314056084,
            "unit": "iter/sec",
            "range": "stddev: 6.074830997742327e-7",
            "extra": "mean: 1.891049342605864 usec\nrounds: 112033"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 697723.3174791199,
            "unit": "iter/sec",
            "range": "stddev: 3.881946751520585e-7",
            "extra": "mean: 1.4332328803529288 usec\nrounds: 183824"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 866541.5661495792,
            "unit": "iter/sec",
            "range": "stddev: 1.6895395565234802e-7",
            "extra": "mean: 1.154012731834013 usec\nrounds: 170329"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 259279.16930373939,
            "unit": "iter/sec",
            "range": "stddev: 7.440293997616989e-7",
            "extra": "mean: 3.856846667186456 usec\nrounds: 74322"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7365517.805245528,
            "unit": "iter/sec",
            "range": "stddev: 1.3555918409626951e-8",
            "extra": "mean: 135.76777986848748 nsec\nrounds: 71757"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8804348.190605674,
            "unit": "iter/sec",
            "range": "stddev: 1.1232426086122777e-8",
            "extra": "mean: 113.58024221111677 nsec\nrounds: 88559"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1446059.7344927255,
            "unit": "iter/sec",
            "range": "stddev: 3.417754695219847e-7",
            "extra": "mean: 691.5343648309229 nsec\nrounds: 166362"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "6fb509dad69539f2a8059754d43ad9783191b26e",
          "message": "style: ruff format credit/history.py",
          "timestamp": "2026-04-01T23:55:04+09:00",
          "tree_id": "d810e6aa986f29d1417bcfa88ec76475b4b353bc",
          "url": "https://github.com/eddmpython/dartlab/commit/6fb509dad69539f2a8059754d43ad9783191b26e"
        },
        "date": 1775055354912,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 562169.0617146484,
            "unit": "iter/sec",
            "range": "stddev: 2.7935703169977925e-7",
            "extra": "mean: 1.7788243219040583 usec\nrounds: 60497"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 686015.2810750366,
            "unit": "iter/sec",
            "range": "stddev: 3.5482371971964564e-7",
            "extra": "mean: 1.457693476496509 usec\nrounds: 108132"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 565492.6091542928,
            "unit": "iter/sec",
            "range": "stddev: 4.206944543660903e-7",
            "extra": "mean: 1.768369707776593 usec\nrounds: 100171"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 709007.7994577757,
            "unit": "iter/sec",
            "range": "stddev: 2.5938528500113724e-7",
            "extra": "mean: 1.4104217199934401 usec\nrounds: 131234"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 841873.5553271247,
            "unit": "iter/sec",
            "range": "stddev: 2.6581790335980323e-7",
            "extra": "mean: 1.1878268341751541 usec\nrounds: 177431"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 298162.10634691204,
            "unit": "iter/sec",
            "range": "stddev: 4.355487177195657e-7",
            "extra": "mean: 3.35388025075359 usec\nrounds: 71917"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8517032.975046137,
            "unit": "iter/sec",
            "range": "stddev: 1.0324844416870587e-8",
            "extra": "mean: 117.41177977470292 nsec\nrounds: 74605"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9808139.983507315,
            "unit": "iter/sec",
            "range": "stddev: 1.297772582612247e-8",
            "extra": "mean: 101.95613048768986 nsec\nrounds: 85158"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1529227.3575823442,
            "unit": "iter/sec",
            "range": "stddev: 2.0968595634543974e-7",
            "extra": "mean: 653.925000126185 nsec\nrounds: 153187"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "e285acaf263a52bceaa40dc77d43bf49284ce010",
          "message": "test: credit 모듈 단위 테스트 51건 추가 — 커버리지 회복",
          "timestamp": "2026-04-02T00:13:40+09:00",
          "tree_id": "31d42f4e1f1b01b8770eb551711dcdfffdcab5ad",
          "url": "https://github.com/eddmpython/dartlab/commit/e285acaf263a52bceaa40dc77d43bf49284ce010"
        },
        "date": 1775056465438,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 282437.0696955891,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012421739705153814",
            "extra": "mean: 3.540611723092159 usec\nrounds: 48929"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 657980.2453282089,
            "unit": "iter/sec",
            "range": "stddev: 5.164088946406786e-7",
            "extra": "mean: 1.51980246686766 usec\nrounds: 81480"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 516135.8553483944,
            "unit": "iter/sec",
            "range": "stddev: 5.776546418736128e-7",
            "extra": "mean: 1.9374743870971622 usec\nrounds: 88881"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675040.5078235925,
            "unit": "iter/sec",
            "range": "stddev: 4.1971458107048504e-7",
            "extra": "mean: 1.4813925807565445 usec\nrounds: 98339"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 777194.7318269337,
            "unit": "iter/sec",
            "range": "stddev: 5.754306846677246e-7",
            "extra": "mean: 1.2866788194116077 usec\nrounds: 175132"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270971.61459946074,
            "unit": "iter/sec",
            "range": "stddev: 7.096892520255551e-7",
            "extra": "mean: 3.690423447039497 usec\nrounds: 70141"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7381805.189445134,
            "unit": "iter/sec",
            "range": "stddev: 1.7903446371331013e-8",
            "extra": "mean: 135.4682187264775 nsec\nrounds: 73992"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8796145.206253981,
            "unit": "iter/sec",
            "range": "stddev: 1.2238876599022349e-8",
            "extra": "mean: 113.6861632626311 nsec\nrounds: 88961"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1457782.9393456564,
            "unit": "iter/sec",
            "range": "stddev: 2.877975938031534e-7",
            "extra": "mean: 685.9731809242205 nsec\nrounds: 176367"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "101a6eb21a197e2e1789e545c06af39753bc510d",
          "message": "fix: test_credit.py import sort",
          "timestamp": "2026-04-02T00:21:09+09:00",
          "tree_id": "c979d7e6a1f3d169ac803480757cff15cb936684",
          "url": "https://github.com/eddmpython/dartlab/commit/101a6eb21a197e2e1789e545c06af39753bc510d"
        },
        "date": 1775056919730,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 529168.7704353209,
            "unit": "iter/sec",
            "range": "stddev: 5.253520064025129e-7",
            "extra": "mean: 1.8897562665637837 usec\nrounds: 57727"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 648959.3921273444,
            "unit": "iter/sec",
            "range": "stddev: 4.86831661923147e-7",
            "extra": "mean: 1.5409284650645314 usec\nrounds: 153799"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 523664.03065171686,
            "unit": "iter/sec",
            "range": "stddev: 5.964850041539481e-7",
            "extra": "mean: 1.909621324870199 usec\nrounds: 135063"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 673849.8558809463,
            "unit": "iter/sec",
            "range": "stddev: 4.09416732148193e-7",
            "extra": "mean: 1.4840101118559517 usec\nrounds: 162285"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 876734.0764775632,
            "unit": "iter/sec",
            "range": "stddev: 1.686535683277997e-7",
            "extra": "mean: 1.1405967063783806 usec\nrounds: 163346"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 262306.5498966487,
            "unit": "iter/sec",
            "range": "stddev: 6.799608391028065e-7",
            "extra": "mean: 3.812333319141324 usec\nrounds: 70488"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7264509.806481862,
            "unit": "iter/sec",
            "range": "stddev: 1.3423227772824862e-8",
            "extra": "mean: 137.6555372129494 nsec\nrounds: 71964"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8566652.822891394,
            "unit": "iter/sec",
            "range": "stddev: 1.3167248892074883e-8",
            "extra": "mean: 116.73170614873624 nsec\nrounds: 86200"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1457883.7074373718,
            "unit": "iter/sec",
            "range": "stddev: 2.7141965695937853e-7",
            "extra": "mean: 685.9257668485592 nsec\nrounds: 184163"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "5622455c4932342ac10b5af05361284cc1bcdf70",
          "message": "refactor: quant를 analysis 축으로 이동 + credit을 analysis에서 분리 (독립 엔진)",
          "timestamp": "2026-04-02T01:54:13+09:00",
          "tree_id": "0f712086101afa51c00969148e79ad8859b00207",
          "url": "https://github.com/eddmpython/dartlab/commit/5622455c4932342ac10b5af05361284cc1bcdf70"
        },
        "date": 1775062502076,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 540258.5592524051,
            "unit": "iter/sec",
            "range": "stddev: 4.926908392291718e-7",
            "extra": "mean: 1.850965584670741 usec\nrounds: 57794"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 661936.1241390987,
            "unit": "iter/sec",
            "range": "stddev: 4.6929884383479797e-7",
            "extra": "mean: 1.5107197862944564 usec\nrounds: 162840"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 537203.93788605,
            "unit": "iter/sec",
            "range": "stddev: 5.83313462461415e-7",
            "extra": "mean: 1.8614904498561529 usec\nrounds: 133977"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 682188.0424907195,
            "unit": "iter/sec",
            "range": "stddev: 3.9902513508368884e-7",
            "extra": "mean: 1.4658714866196207 usec\nrounds: 196890"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 899618.6399873854,
            "unit": "iter/sec",
            "range": "stddev: 1.640427662591402e-7",
            "extra": "mean: 1.111582125526014 usec\nrounds: 29461"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 272419.004950841,
            "unit": "iter/sec",
            "range": "stddev: 6.657803095757958e-7",
            "extra": "mean: 3.670815845540782 usec\nrounds: 78407"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7380176.009138394,
            "unit": "iter/sec",
            "range": "stddev: 1.1815418468263558e-8",
            "extra": "mean: 135.4981234542055 nsec\nrounds: 73987"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8812279.529197048,
            "unit": "iter/sec",
            "range": "stddev: 1.2137280009359633e-8",
            "extra": "mean: 113.47801629382917 nsec\nrounds: 88254"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1462532.7620485506,
            "unit": "iter/sec",
            "range": "stddev: 2.57162318784094e-7",
            "extra": "mean: 683.7453669067304 nsec\nrounds: 186916"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "0f176507dd5b1958e7af51846b4fd5eeaaca2132",
          "message": "docs: 엔진 독립 규칙 명시 — analysis↛credit, review가 블록식 조합",
          "timestamp": "2026-04-02T01:55:55+09:00",
          "tree_id": "dc7853e0b65c764f1c8dfabbe56c08001c6c282e",
          "url": "https://github.com/eddmpython/dartlab/commit/0f176507dd5b1958e7af51846b4fd5eeaaca2132"
        },
        "date": 1775062602573,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 541075.1089062516,
            "unit": "iter/sec",
            "range": "stddev: 5.34286968916135e-7",
            "extra": "mean: 1.8481722473270585 usec\nrounds: 57998"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 666359.4950557252,
            "unit": "iter/sec",
            "range": "stddev: 4.953022939691613e-7",
            "extra": "mean: 1.5006914547175074 usec\nrounds: 116064"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 533000.2516882921,
            "unit": "iter/sec",
            "range": "stddev: 5.457646589211635e-7",
            "extra": "mean: 1.8761717219316012 usec\nrounds: 114732"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675743.848746438,
            "unit": "iter/sec",
            "range": "stddev: 4.148716490992543e-7",
            "extra": "mean: 1.4798506887707294 usec\nrounds: 150558"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 818619.5626536291,
            "unit": "iter/sec",
            "range": "stddev: 4.0949933951989436e-7",
            "extra": "mean: 1.2215686573118407 usec\nrounds: 189754"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269566.51422414853,
            "unit": "iter/sec",
            "range": "stddev: 7.091231645719345e-7",
            "extra": "mean: 3.709659572807642 usec\nrounds: 64986"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7246692.121289978,
            "unit": "iter/sec",
            "range": "stddev: 1.266458696934431e-8",
            "extra": "mean: 137.99399550342574 nsec\nrounds: 73390"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8943780.123503389,
            "unit": "iter/sec",
            "range": "stddev: 1.1686904264919507e-8",
            "extra": "mean: 111.80954654420637 nsec\nrounds: 88013"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1447846.1225576475,
            "unit": "iter/sec",
            "range": "stddev: 3.059528318152818e-7",
            "extra": "mean: 690.6811327667067 nsec\nrounds: 139199"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "d64f55e7ee04e34974c0435b90bf250a0d5af1a7",
          "message": "refactor: analysis↔credit 상호의존 완전 제거 + ops/ 문서 체계 정비\n\n상호의존 제거:\n- credit/metrics.py: analysis._helpers 대신 자체 _toDict/_annualCols 구현\n- credit/metrics.py: analysis.revenue 대신 Company에서 직접 데이터 접근\n- credit/calcs.py: creditRating.py의 6 calc 함수를 credit 모듈로 이동\n- analysis/creditRating.py: migration stub으로 전환\n- review/registry.py: import 경로를 credit.calcs로 변경\n\n문서 정비:\n- ops/analysis.md: 15축→14축, 신용평가 독립 엔진 명시, quant 추가\n- ops/review.md: analysis + credit 블록식 조합 명시\n- ops/search.md: vectorStore.py 참조 제거\n- ops/gather.md: DDG fallback 참조 제거 (Tavily only)\n- ops/credit.md: analysis 독립 명시",
          "timestamp": "2026-04-02T02:08:15+09:00",
          "tree_id": "ef6f852d4f714caa328f77e6457446a83e8abb95",
          "url": "https://github.com/eddmpython/dartlab/commit/d64f55e7ee04e34974c0435b90bf250a0d5af1a7"
        },
        "date": 1775063370335,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 537781.6679303439,
            "unit": "iter/sec",
            "range": "stddev: 4.947281803198685e-7",
            "extra": "mean: 1.8594906811318175 usec\nrounds: 50006"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 639556.1858546985,
            "unit": "iter/sec",
            "range": "stddev: 5.789030233711283e-7",
            "extra": "mean: 1.563584282534312 usec\nrounds: 121419"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 521666.6826816248,
            "unit": "iter/sec",
            "range": "stddev: 5.507095034508034e-7",
            "extra": "mean: 1.9169328484991708 usec\nrounds: 103542"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 669501.1107844076,
            "unit": "iter/sec",
            "range": "stddev: 3.892706577350592e-7",
            "extra": "mean: 1.493649500937153 usec\nrounds: 150785"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 805770.2793825129,
            "unit": "iter/sec",
            "range": "stddev: 3.8256659757181305e-7",
            "extra": "mean: 1.241048504254006 usec\nrounds: 172088"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 264367.66297588,
            "unit": "iter/sec",
            "range": "stddev: 0.000001231852828343922",
            "extra": "mean: 3.7826108864579124 usec\nrounds: 76664"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7294536.486144207,
            "unit": "iter/sec",
            "range": "stddev: 1.2388917881271719e-8",
            "extra": "mean: 137.08890234485432 nsec\nrounds: 60939"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9045055.01792108,
            "unit": "iter/sec",
            "range": "stddev: 1.2217335574841433e-8",
            "extra": "mean: 110.55764702577126 nsec\nrounds: 71501"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1454200.9273720672,
            "unit": "iter/sec",
            "range": "stddev: 3.0128656572336577e-7",
            "extra": "mean: 687.662881502305 nsec\nrounds: 160979"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "ead1d23694105e13454371550eb6984f18439297",
          "message": "docs: README에 YouTube 데모 영상 썸네일 추가",
          "timestamp": "2026-04-02T02:22:18+09:00",
          "tree_id": "5bfba71ad43c61510901cee71b7657ace13084bc",
          "url": "https://github.com/eddmpython/dartlab/commit/ead1d23694105e13454371550eb6984f18439297"
        },
        "date": 1775064184574,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 538713.6966448866,
            "unit": "iter/sec",
            "range": "stddev: 4.988370610730242e-7",
            "extra": "mean: 1.8562735757936142 usec\nrounds: 81747"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 649936.0615730643,
            "unit": "iter/sec",
            "range": "stddev: 4.891805699612917e-7",
            "extra": "mean: 1.5386128869040794 usec\nrounds: 150106"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 537453.4268126881,
            "unit": "iter/sec",
            "range": "stddev: 5.313486960075236e-7",
            "extra": "mean: 1.8606263354396984 usec\nrounds: 127486"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 679041.3237550855,
            "unit": "iter/sec",
            "range": "stddev: 3.972388714241562e-7",
            "extra": "mean: 1.4726644241178417 usec\nrounds: 181786"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 882832.5407681108,
            "unit": "iter/sec",
            "range": "stddev: 1.821798591470502e-7",
            "extra": "mean: 1.1327176489551998 usec\nrounds: 187266"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 244305.75870764814,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020135117446941733",
            "extra": "mean: 4.093231388772394 usec\nrounds: 52643"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7444837.837422318,
            "unit": "iter/sec",
            "range": "stddev: 1.4750034818477823e-8",
            "extra": "mean: 134.32126015873536 nsec\nrounds: 74935"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8899864.14416361,
            "unit": "iter/sec",
            "range": "stddev: 1.4503510427150327e-8",
            "extra": "mean: 112.3612657228913 nsec\nrounds: 88803"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1459896.2713107495,
            "unit": "iter/sec",
            "range": "stddev: 2.6077806647005215e-7",
            "extra": "mean: 684.9801726681325 nsec\nrounds: 175717"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "fbf10c462cd0c6e9f36f066497036619ed5f5ec3",
          "message": "feat: credit 독립 엔진 + quant 통합 + 금융업 지원 + AI 서사 해석 (v0.8.2)\n\nAdded:\n- credit 독립 엔진 (dCR) — 7축 가중, 업종 세분화, CHS 부도확률\n- quant → analysis(\"quant\") 축 통합\n- 금융업(은행/보험) 수익성 분석 — 이자수익 기반 marginTrend\n- AI 종합분석 6막 서사 + quant+재무 교차 검증\n- 보고서 렌더링 개편 — 게이지바, 문단서사, 변화화살표\n\nChanged:\n- analysis↔credit 상호의존 완전 제거\n- AI 프롬프트 #26~#28\n- ops/ 문서 전면 정비",
          "timestamp": "2026-04-02T02:38:12+09:00",
          "tree_id": "43a20104004cae20835803cc7e97b6835501d7ee",
          "url": "https://github.com/eddmpython/dartlab/commit/fbf10c462cd0c6e9f36f066497036619ed5f5ec3"
        },
        "date": 1775065140611,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 522910.16333345755,
            "unit": "iter/sec",
            "range": "stddev: 4.994110642149733e-7",
            "extra": "mean: 1.912374381146431 usec\nrounds: 56552"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 658767.6108174986,
            "unit": "iter/sec",
            "range": "stddev: 5.120542383145638e-7",
            "extra": "mean: 1.5179859840999903 usec\nrounds: 182150"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 535511.6159821232,
            "unit": "iter/sec",
            "range": "stddev: 5.08407641642157e-7",
            "extra": "mean: 1.867373125354171 usec\nrounds: 132891"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 678419.5444879094,
            "unit": "iter/sec",
            "range": "stddev: 4.171474933061321e-7",
            "extra": "mean: 1.4740141378957894 usec\nrounds: 175132"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 888078.755048094,
            "unit": "iter/sec",
            "range": "stddev: 1.9024417168340516e-7",
            "extra": "mean: 1.1260262609770963 usec\nrounds: 175439"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269543.38363228366,
            "unit": "iter/sec",
            "range": "stddev: 6.573655966284916e-7",
            "extra": "mean: 3.7099779134783715 usec\nrounds: 74661"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7254493.143825722,
            "unit": "iter/sec",
            "range": "stddev: 1.2960575830544258e-8",
            "extra": "mean: 137.84560549913775 nsec\nrounds: 72015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8612032.133281963,
            "unit": "iter/sec",
            "range": "stddev: 1.0820441797873873e-8",
            "extra": "mean: 116.11661272551586 nsec\nrounds: 86267"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1461412.158493196,
            "unit": "iter/sec",
            "range": "stddev: 2.9132966061024985e-7",
            "extra": "mean: 684.2696594443695 nsec\nrounds: 183487"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2cbfb2676ba0e46e816c3fd838ffc1c9a369c53d",
          "message": "chore: vscode extension v0.1.1",
          "timestamp": "2026-04-02T07:21:48+09:00",
          "tree_id": "647fdaf61c560edd9fc02878f0bed000c8475bce",
          "url": "https://github.com/eddmpython/dartlab/commit/2cbfb2676ba0e46e816c3fd838ffc1c9a369c53d"
        },
        "date": 1775082157975,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 483577.0086990819,
            "unit": "iter/sec",
            "range": "stddev: 9.041480192185058e-7",
            "extra": "mean: 2.0679229616192845 usec\nrounds: 55362"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 658071.4422560744,
            "unit": "iter/sec",
            "range": "stddev: 4.879675427996814e-7",
            "extra": "mean: 1.5195918494376353 usec\nrounds: 126985"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 523206.718230628,
            "unit": "iter/sec",
            "range": "stddev: 5.752818736238687e-7",
            "extra": "mean: 1.9112904424885517 usec\nrounds: 114601"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 638680.3739232618,
            "unit": "iter/sec",
            "range": "stddev: 5.638807431204326e-7",
            "extra": "mean: 1.5657284000402856 usec\nrounds: 151447"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 809577.8909647836,
            "unit": "iter/sec",
            "range": "stddev: 3.8729355639070803e-7",
            "extra": "mean: 1.2352115975008755 usec\nrounds: 198060"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270172.68606697186,
            "unit": "iter/sec",
            "range": "stddev: 7.509213861040011e-7",
            "extra": "mean: 3.7013364102695214 usec\nrounds: 73883"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7224976.454100934,
            "unit": "iter/sec",
            "range": "stddev: 1.198859539524098e-8",
            "extra": "mean: 138.40875556520254 nsec\nrounds: 23360"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8813262.477839526,
            "unit": "iter/sec",
            "range": "stddev: 1.3391533098321591e-8",
            "extra": "mean: 113.46536002013401 nsec\nrounds: 83662"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1452928.2446705333,
            "unit": "iter/sec",
            "range": "stddev: 2.851377212801918e-7",
            "extra": "mean: 688.2652351677287 nsec\nrounds: 163372"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "05550e12a62a0fedd30fc3d69c0e09fe34cd54a5",
          "message": "docs: API 레퍼런스 전면 재작성 — 현재 엔진 체계 반영\n\n구식 docs/api/ 7개 삭제 + 현재 엔진별 9개 신규 작성:\n\n삭제 (존재하지 않는 모듈/구식):\n- finance-statements.md, finance-summary.md, finance-others.md\n- timeseries.md, insight.md, rank.md, sector.md\n\n신규 (현재 엔진 체계):\n- overview.md: 아키텍처 + 호출 패턴 + API 목록\n- company.md: Company facade (show/select/sections/notes)\n- finance.md: BS/IS/CF/ratios + 계정 표준화 (3파일 통합)\n- analysis.md: 14축 + 6막 서사 구조\n- credit.md: dCR 독립 신용평가 7축\n- scan.md: 전종목 횡단분석\n- gather.md: 외부 시장 데이터 4축\n- review.md: 보고서 렌더링\n- ai.md: ask/chat + provider\n- advanced.md: insight/rank/sector/quant 통합\n\nindex.md 재작성 (엔진 체계 + 보고서 링크)\nnavigation.ts 동기화 (Credit Reports 카테고리 추가)",
          "timestamp": "2026-04-02T08:52:29+09:00",
          "tree_id": "9033ecdd79d7bf60634d80c35dfc99d287e1a535",
          "url": "https://github.com/eddmpython/dartlab/commit/05550e12a62a0fedd30fc3d69c0e09fe34cd54a5"
        },
        "date": 1775089916795,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 578267.3645117773,
            "unit": "iter/sec",
            "range": "stddev: 3.1710444711068247e-7",
            "extra": "mean: 1.7293038849672684 usec\nrounds: 57581"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 703490.4732899151,
            "unit": "iter/sec",
            "range": "stddev: 3.380453346434024e-7",
            "extra": "mean: 1.421483357583281 usec\nrounds: 112033"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 563458.3540971322,
            "unit": "iter/sec",
            "range": "stddev: 5.518603338416605e-7",
            "extra": "mean: 1.774754057205112 usec\nrounds: 84048"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 756703.6385584112,
            "unit": "iter/sec",
            "range": "stddev: 2.581210840623103e-7",
            "extra": "mean: 1.3215213315282721 usec\nrounds: 122565"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 889045.1457516506,
            "unit": "iter/sec",
            "range": "stddev: 2.6128428885967927e-7",
            "extra": "mean: 1.1248022721664397 usec\nrounds: 161343"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 299661.47496386257,
            "unit": "iter/sec",
            "range": "stddev: 3.7795615073120054e-7",
            "extra": "mean: 3.337098971833447 usec\nrounds: 62634"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8402697.959750246,
            "unit": "iter/sec",
            "range": "stddev: 9.423529990455351e-9",
            "extra": "mean: 119.00939493363902 nsec\nrounds: 82305"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9679462.18819423,
            "unit": "iter/sec",
            "range": "stddev: 1.0536134269503023e-8",
            "extra": "mean: 103.31152501630433 nsec\nrounds: 88622"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1480311.3538881491,
            "unit": "iter/sec",
            "range": "stddev: 2.1571003336540435e-7",
            "extra": "mean: 675.5335608103153 nsec\nrounds: 126904"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "dd8d6ff17ee02d0af542cfa01437bc3f7ccbec33",
          "message": "fix: 보고서 파일명 영문화 + 사이드바 영어 통일\n\n- 보고서 파일명: 005930_삼성전자.md → 005930.md (URL 인코딩 404 해결)\n- publisher.py: 파일명에서 한글 기업명 제거\n- navigation.ts: 전체 영어 통일 (한글 카테고리명 제거)\n- index.md: 보고서 링크 영문화",
          "timestamp": "2026-04-02T10:01:52+09:00",
          "tree_id": "3ae2677b1c51f3b415b10878e8b875d50b7aaac1",
          "url": "https://github.com/eddmpython/dartlab/commit/dd8d6ff17ee02d0af542cfa01437bc3f7ccbec33"
        },
        "date": 1775091757240,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 534483.9855623122,
            "unit": "iter/sec",
            "range": "stddev: 4.6519080240435685e-7",
            "extra": "mean: 1.8709634470112972 usec\nrounds: 57232"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 651326.6299397667,
            "unit": "iter/sec",
            "range": "stddev: 5.440354610583717e-7",
            "extra": "mean: 1.535327981434565 usec\nrounds: 119833"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 532660.5493852901,
            "unit": "iter/sec",
            "range": "stddev: 5.359761433898563e-7",
            "extra": "mean: 1.877368243535281 usec\nrounds: 105843"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 667282.5463164499,
            "unit": "iter/sec",
            "range": "stddev: 3.985108365138856e-7",
            "extra": "mean: 1.498615549770072 usec\nrounds: 148105"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 801298.9719060193,
            "unit": "iter/sec",
            "range": "stddev: 4.758697794765678e-7",
            "extra": "mean: 1.2479736466169904 usec\nrounds: 114065"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266463.4277028581,
            "unit": "iter/sec",
            "range": "stddev: 7.231643937125142e-7",
            "extra": "mean: 3.752860227840092 usec\nrounds: 74879"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7329711.207112552,
            "unit": "iter/sec",
            "range": "stddev: 1.2520342159785874e-8",
            "extra": "mean: 136.43102323453445 nsec\nrounds: 74157"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8715338.527666762,
            "unit": "iter/sec",
            "range": "stddev: 1.862589062580987e-8",
            "extra": "mean: 114.74023605916271 nsec\nrounds: 88410"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1459655.2589140085,
            "unit": "iter/sec",
            "range": "stddev: 2.752863052206264e-7",
            "extra": "mean: 685.0932738350873 nsec\nrounds: 160463"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "d4aaa03dc142a6be6096968b62717c13151a36e5",
          "message": "fix: remove --extra hf from data sync workflows (hf is now a core dependency)",
          "timestamp": "2026-04-02T10:10:17+09:00",
          "tree_id": "a109814a289e3456f33b48b9c7d5a45359b8bbd9",
          "url": "https://github.com/eddmpython/dartlab/commit/d4aaa03dc142a6be6096968b62717c13151a36e5"
        },
        "date": 1775092265830,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 535682.45474374,
            "unit": "iter/sec",
            "range": "stddev: 4.800537424496733e-7",
            "extra": "mean: 1.86677758650576 usec\nrounds: 54601"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 645246.3762974637,
            "unit": "iter/sec",
            "range": "stddev: 6.460267874400835e-7",
            "extra": "mean: 1.54979560790124 usec\nrounds: 112020"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 513126.5416113838,
            "unit": "iter/sec",
            "range": "stddev: 5.406458932203553e-7",
            "extra": "mean: 1.9488370195384466 usec\nrounds: 109326"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 667585.7718624728,
            "unit": "iter/sec",
            "range": "stddev: 3.8195782620262935e-7",
            "extra": "mean: 1.4979348604301992 usec\nrounds: 158429"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 806397.1921463482,
            "unit": "iter/sec",
            "range": "stddev: 4.023601729005168e-7",
            "extra": "mean: 1.2400836830028494 usec\nrounds: 179212"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268827.86080263375,
            "unit": "iter/sec",
            "range": "stddev: 6.686816519533614e-7",
            "extra": "mean: 3.719852536914592 usec\nrounds: 69848"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7366963.435331824,
            "unit": "iter/sec",
            "range": "stddev: 1.2159676361782024e-8",
            "extra": "mean: 135.74113795706086 nsec\nrounds: 73175"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8701008.722358504,
            "unit": "iter/sec",
            "range": "stddev: 3.5353141416191645e-8",
            "extra": "mean: 114.9292032578194 nsec\nrounds: 88410"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1464628.6970966598,
            "unit": "iter/sec",
            "range": "stddev: 2.593949398456025e-7",
            "extra": "mean: 682.7669032993172 nsec\nrounds: 166639"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "a88fe3098766c3bdd74b2f5d6264c48e654014c6",
          "message": "feat: credit healthScore + 프롬프트 #29 (score 의미 명시 + quant divergence)",
          "timestamp": "2026-04-02T10:20:13+09:00",
          "tree_id": "b371e30b36e4c86485772ef539ca8641cd0db594",
          "url": "https://github.com/eddmpython/dartlab/commit/a88fe3098766c3bdd74b2f5d6264c48e654014c6"
        },
        "date": 1775092857982,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 599875.9064875526,
            "unit": "iter/sec",
            "range": "stddev: 3.0927088760328376e-7",
            "extra": "mean: 1.667011442175249 usec\nrounds: 53399"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 726748.4292803872,
            "unit": "iter/sec",
            "range": "stddev: 3.415982130411376e-7",
            "extra": "mean: 1.3759919660097255 usec\nrounds: 122355"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527528.8751218987,
            "unit": "iter/sec",
            "range": "stddev: 0.000001131530245275646",
            "extra": "mean: 1.8956308311444092 usec\nrounds: 102617"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 764208.2880686778,
            "unit": "iter/sec",
            "range": "stddev: 2.291306741343087e-7",
            "extra": "mean: 1.30854377741338 usec\nrounds: 142939"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 892860.4885476842,
            "unit": "iter/sec",
            "range": "stddev: 2.2244100338079847e-7",
            "extra": "mean: 1.1199958031815114 usec\nrounds: 161551"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 288625.25148195913,
            "unit": "iter/sec",
            "range": "stddev: 4.750443935013666e-7",
            "extra": "mean: 3.464700315947602 usec\nrounds: 68055"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8493717.436635364,
            "unit": "iter/sec",
            "range": "stddev: 1.3872047492965638e-8",
            "extra": "mean: 117.73407903667353 nsec\nrounds: 75307"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9874222.65807796,
            "unit": "iter/sec",
            "range": "stddev: 8.458824409621973e-9",
            "extra": "mean: 101.27379487254262 nsec\nrounds: 84991"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1495493.8381440656,
            "unit": "iter/sec",
            "range": "stddev: 2.0013275524047805e-7",
            "extra": "mean: 668.6754398406734 nsec\nrounds: 169722"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "730c172ca1a574d1b61dafc5b6ce372f3a29f477",
          "message": "feat: AI viz 도메인 차트 유도 — revenue/cashflow/profitability 1줄 차트 + sandbox import (#30)",
          "timestamp": "2026-04-02T10:51:38+09:00",
          "tree_id": "41dd7cb758b9b8240040e2d9f32481b90b6e2cf0",
          "url": "https://github.com/eddmpython/dartlab/commit/730c172ca1a574d1b61dafc5b6ce372f3a29f477"
        },
        "date": 1775094746910,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 536078.3808206759,
            "unit": "iter/sec",
            "range": "stddev: 5.014317325368675e-7",
            "extra": "mean: 1.8653988591539772 usec\nrounds: 51369"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 662190.8871055837,
            "unit": "iter/sec",
            "range": "stddev: 5.11991588524634e-7",
            "extra": "mean: 1.5101385710259012 usec\nrounds: 128288"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 524638.9159941752,
            "unit": "iter/sec",
            "range": "stddev: 5.737963306942558e-7",
            "extra": "mean: 1.9060728617606064 usec\nrounds: 108850"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 690163.7418217151,
            "unit": "iter/sec",
            "range": "stddev: 4.001446594953742e-7",
            "extra": "mean: 1.448931520743845 usec\nrounds: 135428"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 807697.129252769,
            "unit": "iter/sec",
            "range": "stddev: 3.679280138812753e-7",
            "extra": "mean: 1.2380878472666328 usec\nrounds: 144865"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271749.75109566835,
            "unit": "iter/sec",
            "range": "stddev: 7.627075478913969e-7",
            "extra": "mean: 3.679856176383227 usec\nrounds: 66366"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7372091.097034001,
            "unit": "iter/sec",
            "range": "stddev: 1.2128540720539535e-8",
            "extra": "mean: 135.6467231396975 nsec\nrounds: 73015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9022958.623616835,
            "unit": "iter/sec",
            "range": "stddev: 1.1155080254612011e-8",
            "extra": "mean: 110.8283925166834 nsec\nrounds: 88567"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1468745.3319833318,
            "unit": "iter/sec",
            "range": "stddev: 2.892140654700394e-7",
            "extra": "mean: 680.8532277339341 nsec\nrounds: 149858"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "89403feae359f49f022e5a4a746901477c3aba78",
          "message": "fix: docs frontmatter + title 영어화 + README 엔진 순서 정렬\n\n- 보고서 md에 frontmatter 추가 (mdsvex 렌더링 필수)\n- docs/api/ title 전부 영어 (API Overview, Financial Data 등)\n- 사이드바 엔진 순서: README와 동일 (Company→Scan→Gather→Analysis→Credit→Review→AI)\n- overview.md 엔진 테이블 영어화 + 순서 통일",
          "timestamp": "2026-04-02T10:54:18+09:00",
          "tree_id": "3d53f41c8d75673bdc3ce50f83d3c8d1ff46f026",
          "url": "https://github.com/eddmpython/dartlab/commit/89403feae359f49f022e5a4a746901477c3aba78"
        },
        "date": 1775094906296,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 575428.4471256908,
            "unit": "iter/sec",
            "range": "stddev: 2.5638298496177975e-7",
            "extra": "mean: 1.7378355293261512 usec\nrounds: 61932"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 662094.0117109555,
            "unit": "iter/sec",
            "range": "stddev: 5.157805610168956e-7",
            "extra": "mean: 1.5103595294810808 usec\nrounds: 137043"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 572764.8728261287,
            "unit": "iter/sec",
            "range": "stddev: 3.635215633178495e-7",
            "extra": "mean: 1.7459171248854937 usec\nrounds: 114208"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 728134.1329707479,
            "unit": "iter/sec",
            "range": "stddev: 2.9634598743255927e-7",
            "extra": "mean: 1.373373331531725 usec\nrounds: 170591"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 979287.1214192808,
            "unit": "iter/sec",
            "range": "stddev: 9.480770525401094e-8",
            "extra": "mean: 1.0211509761822457 usec\nrounds: 195199"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 294134.95339376456,
            "unit": "iter/sec",
            "range": "stddev: 4.1948331381988305e-7",
            "extra": "mean: 3.3997999505392995 usec\nrounds: 52582"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8542190.721097,
            "unit": "iter/sec",
            "range": "stddev: 8.425368522195255e-9",
            "extra": "mean: 117.06598841562491 nsec\nrounds: 85288"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9886327.98767758,
            "unit": "iter/sec",
            "range": "stddev: 8.21198273587902e-9",
            "extra": "mean: 101.14979001773058 nsec\nrounds: 87055"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1524341.29141156,
            "unit": "iter/sec",
            "range": "stddev: 1.58629157696993e-7",
            "extra": "mean: 656.0210666956262 nsec\nrounds: 169177"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "8154e7ac4de81c643c98224984b6fc1d54bcc4e3",
          "message": "docs: README 전면 정비 — credit/viz/extras/아키텍처/안정성 v0.8.2 반영",
          "timestamp": "2026-04-02T11:04:25+09:00",
          "tree_id": "916457fe3ca26ed754324978ff6e20abcbf7fa5b",
          "url": "https://github.com/eddmpython/dartlab/commit/8154e7ac4de81c643c98224984b6fc1d54bcc4e3"
        },
        "date": 1775095517203,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 521283.97393700865,
            "unit": "iter/sec",
            "range": "stddev: 5.485968934261198e-7",
            "extra": "mean: 1.9183401945919762 usec\nrounds: 46250"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 638367.4786045583,
            "unit": "iter/sec",
            "range": "stddev: 4.5667623255854647e-7",
            "extra": "mean: 1.5664958405869198 usec\nrounds: 131028"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 508666.4693245836,
            "unit": "iter/sec",
            "range": "stddev: 5.551564044317988e-7",
            "extra": "mean: 1.965924746971857 usec\nrounds: 127357"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 681224.2515494641,
            "unit": "iter/sec",
            "range": "stddev: 3.771873668390476e-7",
            "extra": "mean: 1.4679453905604085 usec\nrounds: 160540"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 891667.8459648024,
            "unit": "iter/sec",
            "range": "stddev: 1.5725320776639453e-7",
            "extra": "mean: 1.1214938438404494 usec\nrounds: 170707"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 248532.39344248732,
            "unit": "iter/sec",
            "range": "stddev: 6.282944268619512e-7",
            "extra": "mean: 4.023620366539499 usec\nrounds: 64881"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7085606.15586519,
            "unit": "iter/sec",
            "range": "stddev: 1.2823769592966368e-8",
            "extra": "mean: 141.131185956792 nsec\nrounds: 68957"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8085463.709846182,
            "unit": "iter/sec",
            "range": "stddev: 1.2408664802410088e-8",
            "extra": "mean: 123.67874445868041 nsec\nrounds: 80077"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1471773.9231950978,
            "unit": "iter/sec",
            "range": "stddev: 2.8166884226445966e-7",
            "extra": "mean: 679.4521796045168 nsec\nrounds: 164501"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "fed503f8c20b6109b2e099d96cd05a59521e2337",
          "message": "fix: credit reports 404 — glob 패턴에 @docs/credit/reports/*.md 추가",
          "timestamp": "2026-04-02T11:17:00+09:00",
          "tree_id": "5c2012dd7a00db46815e06463d86b7f2ef8a4224",
          "url": "https://github.com/eddmpython/dartlab/commit/fed503f8c20b6109b2e099d96cd05a59521e2337"
        },
        "date": 1775096269204,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 426180.61324756005,
            "unit": "iter/sec",
            "range": "stddev: 0.000005037473722956321",
            "extra": "mean: 2.346423016241519 usec\nrounds: 52615"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 661648.937936968,
            "unit": "iter/sec",
            "range": "stddev: 4.576902464781845e-7",
            "extra": "mean: 1.5113755084652836 usec\nrounds: 105955"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 531375.864493765,
            "unit": "iter/sec",
            "range": "stddev: 5.41952320721063e-7",
            "extra": "mean: 1.8819070771170368 usec\nrounds: 92679"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 665550.9623102566,
            "unit": "iter/sec",
            "range": "stddev: 3.865637586246399e-7",
            "extra": "mean: 1.5025145430318452 usec\nrounds: 166334"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 804623.9877554554,
            "unit": "iter/sec",
            "range": "stddev: 3.8651098197798837e-7",
            "extra": "mean: 1.242816539424281 usec\nrounds: 161239"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266429.43931248836,
            "unit": "iter/sec",
            "range": "stddev: 6.931515639430121e-7",
            "extra": "mean: 3.7533389800333787 usec\nrounds: 67532"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7331142.964480018,
            "unit": "iter/sec",
            "range": "stddev: 1.2332468867054417e-8",
            "extra": "mean: 136.4043785321172 nsec\nrounds: 72015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8865725.299396612,
            "unit": "iter/sec",
            "range": "stddev: 1.128742829755801e-8",
            "extra": "mean: 112.79393013316785 nsec\nrounds: 88254"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1462563.954008314,
            "unit": "iter/sec",
            "range": "stddev: 2.9750579101682525e-7",
            "extra": "mean: 683.7307847355272 nsec\nrounds: 161239"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "538602eb352702d7be2669d2fd484aff28494942",
          "message": "feat: credit 노트북 + 메모리 정리 + 랜딩 404 수정\n\n- notebooks/marimo/08_credit.py: credit 엔진 노트북 (등급/서사/시계열/비교)\n- docs/credit/reports: 파일명에 회사명 추가 (005930_삼성전자.md) → 404 해결\n- landing Header: Credit Reports 네비게이션 링크 추가\n- memory/behavior.md: 운영규칙 중복 제거 → MEMORY.md 참조로 통합",
          "timestamp": "2026-04-02T11:26:41+09:00",
          "tree_id": "6566eeb206d4932c5c41da0b6fb8c42146ac3abb",
          "url": "https://github.com/eddmpython/dartlab/commit/538602eb352702d7be2669d2fd484aff28494942"
        },
        "date": 1775096847140,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 540518.665755467,
            "unit": "iter/sec",
            "range": "stddev: 4.7352993587308615e-7",
            "extra": "mean: 1.8500748694817588 usec\nrounds: 55176"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 656276.81114856,
            "unit": "iter/sec",
            "range": "stddev: 5.000777463038595e-7",
            "extra": "mean: 1.5237472709875042 usec\nrounds: 111396"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520586.59742982633,
            "unit": "iter/sec",
            "range": "stddev: 5.393873859261708e-7",
            "extra": "mean: 1.9209099983308682 usec\nrounds: 118120"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 669287.2443520683,
            "unit": "iter/sec",
            "range": "stddev: 4.202010627372216e-7",
            "extra": "mean: 1.4941267870241457 usec\nrounds: 144865"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 802331.6819409635,
            "unit": "iter/sec",
            "range": "stddev: 4.135836651616144e-7",
            "extra": "mean: 1.2463673347422184 usec\nrounds: 172385"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268854.95811985957,
            "unit": "iter/sec",
            "range": "stddev: 6.630432493599125e-7",
            "extra": "mean: 3.71947762091925 usec\nrounds: 61084"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7345781.847947229,
            "unit": "iter/sec",
            "range": "stddev: 1.1911871352047789e-8",
            "extra": "mean: 136.13254799820237 nsec\nrounds: 73336"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9021629.859484233,
            "unit": "iter/sec",
            "range": "stddev: 1.1249725233427343e-8",
            "extra": "mean: 110.84471604082968 nsec\nrounds: 91316"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453651.6283384305,
            "unit": "iter/sec",
            "range": "stddev: 4.187504891261013e-7",
            "extra": "mean: 687.9227323145034 nsec\nrounds: 134157"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "b13ef766f76e69453358e86e60bcfdc9a04e3d42",
          "message": "fix: credit report mdsvex 빌드 오류 — < 이스케이프 (&lt;)",
          "timestamp": "2026-04-02T11:34:15+09:00",
          "tree_id": "3bead5db0c74d0217918f5a5f38d2abef593bee9",
          "url": "https://github.com/eddmpython/dartlab/commit/b13ef766f76e69453358e86e60bcfdc9a04e3d42"
        },
        "date": 1775097298555,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542308.8541456601,
            "unit": "iter/sec",
            "range": "stddev: 4.925885222802173e-7",
            "extra": "mean: 1.8439676806962249 usec\nrounds: 93721"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 649994.2599968453,
            "unit": "iter/sec",
            "range": "stddev: 5.207792632135424e-7",
            "extra": "mean: 1.538475124387796 usec\nrounds: 169463"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 534213.4469151938,
            "unit": "iter/sec",
            "range": "stddev: 5.615383156137965e-7",
            "extra": "mean: 1.8719109482819694 usec\nrounds: 133619"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 677912.6973207315,
            "unit": "iter/sec",
            "range": "stddev: 3.7715287125096427e-7",
            "extra": "mean: 1.4751161970445936 usec\nrounds: 118540"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 892452.0177042724,
            "unit": "iter/sec",
            "range": "stddev: 1.5854032635872373e-7",
            "extra": "mean: 1.1205084196821942 usec\nrounds: 108484"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270655.6045584033,
            "unit": "iter/sec",
            "range": "stddev: 6.468447951861219e-7",
            "extra": "mean: 3.694732283972399 usec\nrounds: 80238"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7306647.327706193,
            "unit": "iter/sec",
            "range": "stddev: 1.1988009379609536e-8",
            "extra": "mean: 136.8616761080125 nsec\nrounds: 73611"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8888192.322426844,
            "unit": "iter/sec",
            "range": "stddev: 1.2060195827964898e-8",
            "extra": "mean: 112.50881661018768 nsec\nrounds: 89438"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453812.7989554638,
            "unit": "iter/sec",
            "range": "stddev: 2.794178360427036e-7",
            "extra": "mean: 687.8464687602699 nsec\nrounds: 174186"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2c010fc59db0e21aacd3283a3435e2ba4685f7fd",
          "message": "refactor: quant를 analysis 축으로 통합 — dartlab.quant()/c.quant() 제거, 문서 일관화",
          "timestamp": "2026-04-02T12:27:33+09:00",
          "tree_id": "cff6aa595c48e97fc8e8562b53756640ae9e6e30",
          "url": "https://github.com/eddmpython/dartlab/commit/2c010fc59db0e21aacd3283a3435e2ba4685f7fd"
        },
        "date": 1775100503990,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 544431.6765927306,
            "unit": "iter/sec",
            "range": "stddev: 5.334891596908253e-7",
            "extra": "mean: 1.83677776843992 usec\nrounds: 47599"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 663438.5429542653,
            "unit": "iter/sec",
            "range": "stddev: 4.7537611890234146e-7",
            "extra": "mean: 1.5072986196235147 usec\nrounds: 128950"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 532187.8771233569,
            "unit": "iter/sec",
            "range": "stddev: 5.733674224381014e-7",
            "extra": "mean: 1.879035662002139 usec\nrounds: 125708"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 673268.6587886964,
            "unit": "iter/sec",
            "range": "stddev: 4.05548652517606e-7",
            "extra": "mean: 1.485291179005924 usec\nrounds: 124147"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 810461.0555202655,
            "unit": "iter/sec",
            "range": "stddev: 3.858535324381382e-7",
            "extra": "mean: 1.2338655795842803 usec\nrounds: 169751"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269230.5828176571,
            "unit": "iter/sec",
            "range": "stddev: 6.336613446433748e-7",
            "extra": "mean: 3.714288286027573 usec\nrounds: 67714"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7361448.292187433,
            "unit": "iter/sec",
            "range": "stddev: 1.1261329028012683e-8",
            "extra": "mean: 135.84283422343418 nsec\nrounds: 73611"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8997459.741721679,
            "unit": "iter/sec",
            "range": "stddev: 1.6463701675852507e-8",
            "extra": "mean: 111.14248117865414 nsec\nrounds: 89127"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1450421.8243874703,
            "unit": "iter/sec",
            "range": "stddev: 2.610860679115665e-7",
            "extra": "mean: 689.4546008519359 nsec\nrounds: 164177"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "74ae7689935526b4974225cb5f01f39efcd8ee10",
          "message": "refactor: quant/__init__.py에서 Quant 클래스 제거 — 내부 모듈만 유지",
          "timestamp": "2026-04-02T12:35:42+09:00",
          "tree_id": "10b03ac6cc2b0eabf52895b6397b914f0bd2e8be",
          "url": "https://github.com/eddmpython/dartlab/commit/74ae7689935526b4974225cb5f01f39efcd8ee10"
        },
        "date": 1775100988113,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 538622.6909115316,
            "unit": "iter/sec",
            "range": "stddev: 5.438152510139903e-7",
            "extra": "mean: 1.8565872119268911 usec\nrounds: 50641"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 646360.2543813278,
            "unit": "iter/sec",
            "range": "stddev: 5.297266939903e-7",
            "extra": "mean: 1.5471248320445743 usec\nrounds: 123534"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 532273.6929464699,
            "unit": "iter/sec",
            "range": "stddev: 5.866700555270341e-7",
            "extra": "mean: 1.8787327144882375 usec\nrounds: 116456"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 679473.4766704717,
            "unit": "iter/sec",
            "range": "stddev: 3.9439973402829463e-7",
            "extra": "mean: 1.4717277926728785 usec\nrounds: 121863"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 804156.1467833029,
            "unit": "iter/sec",
            "range": "stddev: 4.0266155631163566e-7",
            "extra": "mean: 1.2435395836991239 usec\nrounds: 162049"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269107.8607718388,
            "unit": "iter/sec",
            "range": "stddev: 7.777910192507252e-7",
            "extra": "mean: 3.715982123791779 usec\nrounds: 65450"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7291066.452248016,
            "unit": "iter/sec",
            "range": "stddev: 1.2506061837314286e-8",
            "extra": "mean: 137.1541470029635 nsec\nrounds: 61577"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8615794.243002728,
            "unit": "iter/sec",
            "range": "stddev: 1.361359985571058e-8",
            "extra": "mean: 116.06591009437636 nsec\nrounds: 86491"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1465384.9941892338,
            "unit": "iter/sec",
            "range": "stddev: 2.519940525448366e-7",
            "extra": "mean: 682.4145217573206 nsec\nrounds: 159719"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "af476e273fa01f970f481135517dcfc56eb9f25f",
          "message": "refactor: quant 독립 엔진 격상 — analysis 분산 제거, 전용 모듈로 통합\n\n- quant/extended.py: technicalAnalysis.py 로직 이동 (signals, beta, divergence, risk, flags)\n- analysis/quantCalcs.py, technicalAnalysis.py 삭제\n- analysis __init__에서 quant 그룹 제거\n- dartlab.quant(), c.quant() 독립 엔진 복원\n- c.quant(\"divergence\"), c.quant(\"flags\") 신규 metric\n- 시스템 프롬프트, ops/quant.md, ops/README.md, MEMORY.md 일관화",
          "timestamp": "2026-04-02T13:15:37+09:00",
          "tree_id": "18dd1e1a48cd0f11a466dd8c6a6a8b9e7b0b533d",
          "url": "https://github.com/eddmpython/dartlab/commit/af476e273fa01f970f481135517dcfc56eb9f25f"
        },
        "date": 1775103415138,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 541991.3813244617,
            "unit": "iter/sec",
            "range": "stddev: 5.071929544961826e-7",
            "extra": "mean: 1.8450477894248154 usec\nrounds: 55054"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 665811.5739701359,
            "unit": "iter/sec",
            "range": "stddev: 4.740478480582348e-7",
            "extra": "mean: 1.5019264294808634 usec\nrounds: 134157"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 528178.9598588214,
            "unit": "iter/sec",
            "range": "stddev: 4.951180426520192e-7",
            "extra": "mean: 1.8932976812769922 usec\nrounds: 135981"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 687472.3023418526,
            "unit": "iter/sec",
            "range": "stddev: 4.049805000721687e-7",
            "extra": "mean: 1.454604056910412 usec\nrounds: 163079"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 813937.4078328299,
            "unit": "iter/sec",
            "range": "stddev: 3.838321472197355e-7",
            "extra": "mean: 1.2285957008200126 usec\nrounds: 191571"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271714.0509118525,
            "unit": "iter/sec",
            "range": "stddev: 6.739267430208774e-7",
            "extra": "mean: 3.6803396682802125 usec\nrounds: 74823"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7275473.179343716,
            "unit": "iter/sec",
            "range": "stddev: 1.3286890567153366e-8",
            "extra": "mean: 137.44810479669792 nsec\nrounds: 70842"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8734012.817663703,
            "unit": "iter/sec",
            "range": "stddev: 2.0843773530584322e-8",
            "extra": "mean: 114.49490868362317 nsec\nrounds: 87936"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1459258.011587281,
            "unit": "iter/sec",
            "range": "stddev: 2.6202407511158836e-7",
            "extra": "mean: 685.2797737339598 nsec\nrounds: 158932"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "afeabc807e4723b04090b40d12cb52e44606b8a1",
          "message": "release: v0.8.3 + vscode v0.1.2 — quant 독립 엔진, credit healthScore, viz AI 연동",
          "timestamp": "2026-04-02T13:49:51+09:00",
          "tree_id": "b83cc031aa7d55b32d6114e7286263b91bc351d0",
          "url": "https://github.com/eddmpython/dartlab/commit/afeabc807e4723b04090b40d12cb52e44606b8a1"
        },
        "date": 1775105438810,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 544717.1560379239,
            "unit": "iter/sec",
            "range": "stddev: 4.837009087557949e-7",
            "extra": "mean: 1.8358151361958914 usec\nrounds: 61997"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 660689.222891407,
            "unit": "iter/sec",
            "range": "stddev: 4.3456919022659596e-7",
            "extra": "mean: 1.5135709276801133 usec\nrounds: 154298"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 530620.5448667133,
            "unit": "iter/sec",
            "range": "stddev: 5.316091082775445e-7",
            "extra": "mean: 1.8845859054537555 usec\nrounds: 135428"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 673113.2410445237,
            "unit": "iter/sec",
            "range": "stddev: 3.8750249472467125e-7",
            "extra": "mean: 1.4856341236850727 usec\nrounds: 170011"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 886693.352589695,
            "unit": "iter/sec",
            "range": "stddev: 1.7646949721090858e-7",
            "extra": "mean: 1.127785606015179 usec\nrounds: 199243"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270070.9247870803,
            "unit": "iter/sec",
            "range": "stddev: 6.52411304720437e-7",
            "extra": "mean: 3.7027310540310268 usec\nrounds: 78592"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7466209.484789999,
            "unit": "iter/sec",
            "range": "stddev: 1.1793657468232755e-8",
            "extra": "mean: 133.9367723390535 nsec\nrounds: 72015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8638774.517308302,
            "unit": "iter/sec",
            "range": "stddev: 1.0875912187732338e-8",
            "extra": "mean: 115.75715953651067 nsec\nrounds: 87704"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1447190.0392076022,
            "unit": "iter/sec",
            "range": "stddev: 2.694650760958475e-7",
            "extra": "mean: 690.9942529369138 nsec\nrounds: 172088"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "b72d31ae1a6430b36057a896bb4e9e3eff23d766",
          "message": "fix: lint/format/quality baseline 수정",
          "timestamp": "2026-04-02T13:59:19+09:00",
          "tree_id": "c30bd1042c75c7ba227ec40397271c59bd625c2f",
          "url": "https://github.com/eddmpython/dartlab/commit/b72d31ae1a6430b36057a896bb4e9e3eff23d766"
        },
        "date": 1775106007928,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542259.7371540341,
            "unit": "iter/sec",
            "range": "stddev: 4.949781641592179e-7",
            "extra": "mean: 1.8441347042440297 usec\nrounds: 57333"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 667192.1893274807,
            "unit": "iter/sec",
            "range": "stddev: 0.000008390149081315575",
            "extra": "mean: 1.4988185053664738 usec\nrounds: 127001"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 525715.4286007378,
            "unit": "iter/sec",
            "range": "stddev: 5.53959623972711e-7",
            "extra": "mean: 1.902169777785739 usec\nrounds: 104625"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 670617.3858847804,
            "unit": "iter/sec",
            "range": "stddev: 3.7935135283240543e-7",
            "extra": "mean: 1.4911632490419975 usec\nrounds: 133085"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 808852.502778201,
            "unit": "iter/sec",
            "range": "stddev: 3.7384438735566087e-7",
            "extra": "mean: 1.236319349405802 usec\nrounds: 122474"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268531.2607687521,
            "unit": "iter/sec",
            "range": "stddev: 7.388149662796614e-7",
            "extra": "mean: 3.7239612145610046 usec\nrounds: 65540"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7338550.451314273,
            "unit": "iter/sec",
            "range": "stddev: 1.3850595267989347e-8",
            "extra": "mean: 136.26669280728436 nsec\nrounds: 73449"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8684888.957882803,
            "unit": "iter/sec",
            "range": "stddev: 1.06555890241022e-8",
            "extra": "mean: 115.14251993888237 nsec\nrounds: 86641"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1459299.4628850976,
            "unit": "iter/sec",
            "range": "stddev: 2.88008372010968e-7",
            "extra": "mean: 685.2603084105556 nsec\nrounds: 142796"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "c99761e2435bae9b2156380bfde4bbacd999de60",
          "message": "style: screen format",
          "timestamp": "2026-04-02T14:08:38+09:00",
          "tree_id": "fa51e0ea7d003633d8859ecde791f87a847dc4e8",
          "url": "https://github.com/eddmpython/dartlab/commit/c99761e2435bae9b2156380bfde4bbacd999de60"
        },
        "date": 1775106563957,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 534223.5601814066,
            "unit": "iter/sec",
            "range": "stddev: 4.90421987990785e-7",
            "extra": "mean: 1.871875511556303 usec\nrounds: 52535"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 653678.9895145166,
            "unit": "iter/sec",
            "range": "stddev: 4.804263323931652e-7",
            "extra": "mean: 1.529802878845309 usec\nrounds: 124147"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520489.6247418966,
            "unit": "iter/sec",
            "range": "stddev: 5.610123677805433e-7",
            "extra": "mean: 1.921267884054146 usec\nrounds: 132031"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 642016.9022900941,
            "unit": "iter/sec",
            "range": "stddev: 6.215318570377689e-7",
            "extra": "mean: 1.557591391181399 usec\nrounds: 143411"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 799752.9319486816,
            "unit": "iter/sec",
            "range": "stddev: 3.82897034065612e-7",
            "extra": "mean: 1.250386163090888 usec\nrounds: 185186"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266557.8473626148,
            "unit": "iter/sec",
            "range": "stddev: 8.032466037000312e-7",
            "extra": "mean: 3.7515308961796925 usec\nrounds: 71449"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 5470845.660410711,
            "unit": "iter/sec",
            "range": "stddev: 1.6881926261973425e-8",
            "extra": "mean: 182.7870976577554 nsec\nrounds: 64982"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8903073.427420402,
            "unit": "iter/sec",
            "range": "stddev: 1.1425522407462942e-8",
            "extra": "mean: 112.32076295362448 nsec\nrounds: 87253"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1446669.1347625342,
            "unit": "iter/sec",
            "range": "stddev: 2.7773077295511174e-7",
            "extra": "mean: 691.2430603312392 nsec\nrounds: 161499"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "04a123e6c77d2dc9edf35bf676c5c6e0c8cafbae",
          "message": "fix: CI test에 --benchmark-disable 추가 (타임아웃 방지)",
          "timestamp": "2026-04-02T14:18:01+09:00",
          "tree_id": "f4396e7b709732f9327ec6c4edbbc1fea1c202c1",
          "url": "https://github.com/eddmpython/dartlab/commit/04a123e6c77d2dc9edf35bf676c5c6e0c8cafbae"
        },
        "date": 1775107123246,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 537101.9597592166,
            "unit": "iter/sec",
            "range": "stddev: 5.588731622366357e-7",
            "extra": "mean: 1.8618438861185704 usec\nrounds: 47081"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 660127.6768324699,
            "unit": "iter/sec",
            "range": "stddev: 4.97388403186725e-7",
            "extra": "mean: 1.5148584661657571 usec\nrounds: 116050"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 521024.82393322466,
            "unit": "iter/sec",
            "range": "stddev: 5.383621221480567e-7",
            "extra": "mean: 1.9192943484937708 usec\nrounds: 101441"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 674299.8007705206,
            "unit": "iter/sec",
            "range": "stddev: 4.1432202215675144e-7",
            "extra": "mean: 1.4830198657293132 usec\nrounds: 108378"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 809786.2305953412,
            "unit": "iter/sec",
            "range": "stddev: 3.9528988164831143e-7",
            "extra": "mean: 1.2348938055723877 usec\nrounds: 124611"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268093.0924101929,
            "unit": "iter/sec",
            "range": "stddev: 7.505560133351874e-7",
            "extra": "mean: 3.7300476152140507 usec\nrounds: 61346"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7423850.882855935,
            "unit": "iter/sec",
            "range": "stddev: 1.3628780625290404e-8",
            "extra": "mean: 134.7009814420333 nsec\nrounds: 73606"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8940037.531856354,
            "unit": "iter/sec",
            "range": "stddev: 1.1570119350161469e-8",
            "extra": "mean: 111.85635367152143 nsec\nrounds: 64772"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1472425.9666279366,
            "unit": "iter/sec",
            "range": "stddev: 2.822998470588522e-7",
            "extra": "mean: 679.1512936233672 nsec\nrounds: 153093"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "24d9ff0ae3bb561684d0fbe42f0c3f347df855a4",
          "message": "fix: coverage threshold 30→25% (신규 엔진 추가로 커버리지 희석)",
          "timestamp": "2026-04-02T14:27:05+09:00",
          "tree_id": "e5a89b56aeea5ea3a945d3cd249fcb2bbfdc56ec",
          "url": "https://github.com/eddmpython/dartlab/commit/24d9ff0ae3bb561684d0fbe42f0c3f347df855a4"
        },
        "date": 1775107672001,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 523878.9763287413,
            "unit": "iter/sec",
            "range": "stddev: 5.564370600480202e-7",
            "extra": "mean: 1.9088378140459794 usec\nrounds: 53377"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 660844.3375200533,
            "unit": "iter/sec",
            "range": "stddev: 5.12707253016108e-7",
            "extra": "mean: 1.513215659458768 usec\nrounds: 114078"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 529341.6480658447,
            "unit": "iter/sec",
            "range": "stddev: 5.469208276632406e-7",
            "extra": "mean: 1.889139091272883 usec\nrounds: 99503"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675828.3765058069,
            "unit": "iter/sec",
            "range": "stddev: 4.460131562902661e-7",
            "extra": "mean: 1.4796655996752273 usec\nrounds: 112778"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 809506.8856111428,
            "unit": "iter/sec",
            "range": "stddev: 3.977604316328533e-7",
            "extra": "mean: 1.2353199432578552 usec\nrounds: 128304"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270632.48034977313,
            "unit": "iter/sec",
            "range": "stddev: 7.53542530934093e-7",
            "extra": "mean: 3.6950479805955716 usec\nrounds: 72967"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7300241.856553154,
            "unit": "iter/sec",
            "range": "stddev: 1.245726438690052e-8",
            "extra": "mean: 136.98176302232196 nsec\nrounds: 73720"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8939456.8385042,
            "unit": "iter/sec",
            "range": "stddev: 1.0777346433145158e-8",
            "extra": "mean: 111.8636196880308 nsec\nrounds: 89679"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1468247.9215258525,
            "unit": "iter/sec",
            "range": "stddev: 3.002968858182301e-7",
            "extra": "mean: 681.083885997105 nsec\nrounds: 148523"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "f1ce80a45df1469a104ed494a7f0fba2618a0b47",
          "message": "refactor: 0.8 안정화 — 체계 문서 + scan 데이터 일관성\n\nPhase 1: ops/architecture.md 전체 청사진 (레이어, 엔진, 규칙, 데이터 출력, 체크리스트)\nPhase 2: ops/testing.md 테스트 체계 (마커, 커버리지 90% 목표, CI 규칙)\nPhase 3: scan 데이터 일관성 통일\n  - governance/workforce/capital/debt: 종목코드→stockCode, _enrichWithKorean 경유\n  - scanAccount: corpName 제거, _enrichWithKorean이 종목명 추가\n  - screen: stockCode 기반으로 통일\n  - 결과: 모든 scan 축이 종목코드|종목명 첫 2컬럼\nPhase 6: MEMORY.md에 architecture.md + testing.md 참조 추가",
          "timestamp": "2026-04-02T15:09:31+09:00",
          "tree_id": "81d01cfadeeb4a48649af900897ec38369fe8ebd",
          "url": "https://github.com/eddmpython/dartlab/commit/f1ce80a45df1469a104ed494a7f0fba2618a0b47"
        },
        "date": 1775110236875,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 523815.3595993766,
            "unit": "iter/sec",
            "range": "stddev: 5.581601595132071e-7",
            "extra": "mean: 1.9090696400441902 usec\nrounds: 52757"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 671837.3625443723,
            "unit": "iter/sec",
            "range": "stddev: 5.672329105687202e-7",
            "extra": "mean: 1.4884554741237002 usec\nrounds: 114338"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 530459.1054024097,
            "unit": "iter/sec",
            "range": "stddev: 5.512378067604448e-7",
            "extra": "mean: 1.8851594586945466 usec\nrounds: 97762"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 634456.6005518009,
            "unit": "iter/sec",
            "range": "stddev: 7.975858344680334e-7",
            "extra": "mean: 1.5761519371542165 usec\nrounds: 103115"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 792160.6060179445,
            "unit": "iter/sec",
            "range": "stddev: 4.059613305805812e-7",
            "extra": "mean: 1.2623702723956807 usec\nrounds: 113033"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270055.0481165468,
            "unit": "iter/sec",
            "range": "stddev: 7.304976107157757e-7",
            "extra": "mean: 3.7029487394304623 usec\nrounds: 59695"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7185180.094615977,
            "unit": "iter/sec",
            "range": "stddev: 1.3476097491915702e-8",
            "extra": "mean: 139.1753563350936 nsec\nrounds: 68980"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8844074.249824239,
            "unit": "iter/sec",
            "range": "stddev: 1.2004810533829738e-8",
            "extra": "mean: 113.07005931342937 nsec\nrounds: 88176"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1461121.056420634,
            "unit": "iter/sec",
            "range": "stddev: 2.8931645244738877e-7",
            "extra": "mean: 684.4059878582132 nsec\nrounds: 138046"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "01b2604fd7371d8235ba68c316d433cba2940386",
          "message": "test: credit/quant/scan 엔진 테스트 135개 추가 (978 passed)\n\n- test_credit_engine.py (75): scoreMetric, axisScore, mapTo20Grade, healthScore, outlook\n- test_quant_engine.py (39): SMA/EMA/RSI/MACD/BB/ATR, verdict, signals\n- test_scan_consistency.py (21): _enrichWithKorean, 컬럼명 매핑, 종목명 join\n- notebooks/02_scan.py: search() 호출 제거 (엔진 경계 수정)",
          "timestamp": "2026-04-02T15:23:39+09:00",
          "tree_id": "216a63b1db3c56cc06d285b3b1828d2f7bf896e7",
          "url": "https://github.com/eddmpython/dartlab/commit/01b2604fd7371d8235ba68c316d433cba2940386"
        },
        "date": 1775111064311,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 518441.9573033671,
            "unit": "iter/sec",
            "range": "stddev: 5.316497865514947e-7",
            "extra": "mean: 1.928856231469801 usec\nrounds: 52981"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 645438.3778567569,
            "unit": "iter/sec",
            "range": "stddev: 5.054832596923263e-7",
            "extra": "mean: 1.5493345829862186 usec\nrounds: 124301"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 502559.5318945342,
            "unit": "iter/sec",
            "range": "stddev: 8.475396787998422e-7",
            "extra": "mean: 1.9898140151281765 usec\nrounds: 123381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 678401.164865831,
            "unit": "iter/sec",
            "range": "stddev: 3.9827202254924905e-7",
            "extra": "mean: 1.4740540727075142 usec\nrounds: 173914"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 790632.0035888873,
            "unit": "iter/sec",
            "range": "stddev: 3.8851985088108804e-7",
            "extra": "mean: 1.2648109303199668 usec\nrounds: 177305"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 260193.03376490713,
            "unit": "iter/sec",
            "range": "stddev: 7.009735384538172e-7",
            "extra": "mean: 3.8433004355663596 usec\nrounds: 68414"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 6807845.692421235,
            "unit": "iter/sec",
            "range": "stddev: 1.3990707313925827e-8",
            "extra": "mean: 146.88934579014324 nsec\nrounds: 67486"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9114211.87093172,
            "unit": "iter/sec",
            "range": "stddev: 2.649706509569448e-8",
            "extra": "mean: 109.71875727284062 nsec\nrounds: 89199"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453191.1174548191,
            "unit": "iter/sec",
            "range": "stddev: 2.962586400670761e-7",
            "extra": "mean: 688.1407324808333 nsec\nrounds: 167758"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "69d4b4ece004c046c450e9432fe5b944949f8d56",
          "message": "test: viz/analysis/review 테스트 80개 추가 (1,058 passed)",
          "timestamp": "2026-04-02T15:30:06+09:00",
          "tree_id": "671f73be90816052f3977881a250272c5af0a47b",
          "url": "https://github.com/eddmpython/dartlab/commit/69d4b4ece004c046c450e9432fe5b944949f8d56"
        },
        "date": 1775111452658,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 539189.0575913944,
            "unit": "iter/sec",
            "range": "stddev: 4.94444232088419e-7",
            "extra": "mean: 1.8546370441327005 usec\nrounds: 52370"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 663499.8230619626,
            "unit": "iter/sec",
            "range": "stddev: 4.792028832751295e-7",
            "extra": "mean: 1.507159407194917 usec\nrounds: 116469"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 532612.8494434257,
            "unit": "iter/sec",
            "range": "stddev: 5.770037299075726e-7",
            "extra": "mean: 1.8775363775864373 usec\nrounds: 120555"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 692231.7194396754,
            "unit": "iter/sec",
            "range": "stddev: 4.662100668601688e-7",
            "extra": "mean: 1.4446029731336878 usec\nrounds: 168039"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 796636.187601235,
            "unit": "iter/sec",
            "range": "stddev: 3.810502016891872e-7",
            "extra": "mean: 1.2552781502571673 usec\nrounds: 181819"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266802.82820980466,
            "unit": "iter/sec",
            "range": "stddev: 7.205098273125146e-7",
            "extra": "mean: 3.7480862054941717 usec\nrounds: 62815"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7294668.291569183,
            "unit": "iter/sec",
            "range": "stddev: 1.2165760265663972e-8",
            "extra": "mean: 137.08642532186838 nsec\nrounds: 50108"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8774160.216092747,
            "unit": "iter/sec",
            "range": "stddev: 1.1005460442491267e-8",
            "extra": "mean: 113.97102119994267 nsec\nrounds: 76841"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1447280.0391035655,
            "unit": "iter/sec",
            "range": "stddev: 2.8402451628046256e-7",
            "extra": "mean: 690.9512830836751 nsec\nrounds: 159185"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "8d6f528fdba153cae4a565f60f26999e69392c8e",
          "message": "test: core/gather/guide 테스트 88개 추가 (1,146 passed)",
          "timestamp": "2026-04-02T15:38:11+09:00",
          "tree_id": "99476e0b31c1c35bafffaa010863a8d3ab75e3b2",
          "url": "https://github.com/eddmpython/dartlab/commit/8d6f528fdba153cae4a565f60f26999e69392c8e"
        },
        "date": 1775111942267,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 533720.9796242152,
            "unit": "iter/sec",
            "range": "stddev: 4.865171091733819e-7",
            "extra": "mean: 1.8736381708361638 usec\nrounds: 58956"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 668617.9993551573,
            "unit": "iter/sec",
            "range": "stddev: 4.698034799367858e-7",
            "extra": "mean: 1.4956223149308592 usec\nrounds: 167449"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 537164.2444965953,
            "unit": "iter/sec",
            "range": "stddev: 5.640194667606557e-7",
            "extra": "mean: 1.8616280034371093 usec\nrounds: 130141"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 686182.9789029846,
            "unit": "iter/sec",
            "range": "stddev: 3.8779235869412226e-7",
            "extra": "mean: 1.4573372274531224 usec\nrounds: 181127"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 909429.0260465092,
            "unit": "iter/sec",
            "range": "stddev: 1.5593810589668855e-7",
            "extra": "mean: 1.0995910305911645 usec\nrounds: 171204"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266413.81359885435,
            "unit": "iter/sec",
            "range": "stddev: 6.667664738433907e-7",
            "extra": "mean: 3.753559121021119 usec\nrounds: 78407"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7347216.479666599,
            "unit": "iter/sec",
            "range": "stddev: 1.2052526280832496e-8",
            "extra": "mean: 136.10596649322872 nsec\nrounds: 72701"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8998873.795715747,
            "unit": "iter/sec",
            "range": "stddev: 1.771207598090115e-8",
            "extra": "mean: 111.1250166077546 nsec\nrounds: 84296"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1463748.6913976672,
            "unit": "iter/sec",
            "range": "stddev: 2.5253533944836963e-7",
            "extra": "mean: 683.1773827549218 nsec\nrounds: 155934"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "715061fc2e58d49a84b34e3137d6463db899d05b",
          "message": "test: analysis calc + credit pipeline + server API 테스트 122개 추가 (1,268 passed)",
          "timestamp": "2026-04-02T15:54:34+09:00",
          "tree_id": "8ede103b6227d5f8f7aee9ad7745fcc6fd8caf18",
          "url": "https://github.com/eddmpython/dartlab/commit/715061fc2e58d49a84b34e3137d6463db899d05b"
        },
        "date": 1775112923939,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 540865.1986263858,
            "unit": "iter/sec",
            "range": "stddev: 4.957340733537627e-7",
            "extra": "mean: 1.848889524672064 usec\nrounds: 52953"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 656780.6293925047,
            "unit": "iter/sec",
            "range": "stddev: 4.862525676454621e-7",
            "extra": "mean: 1.5225784002262053 usec\nrounds: 129955"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 525663.9102094478,
            "unit": "iter/sec",
            "range": "stddev: 5.750903555310351e-7",
            "extra": "mean: 1.9023562024670013 usec\nrounds: 106417"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 685203.5296320933,
            "unit": "iter/sec",
            "range": "stddev: 3.9210835482224246e-7",
            "extra": "mean: 1.45942038643165 usec\nrounds: 144655"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 797553.0227759343,
            "unit": "iter/sec",
            "range": "stddev: 3.688373339823477e-7",
            "extra": "mean: 1.253835132514997 usec\nrounds: 186568"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268310.4686254574,
            "unit": "iter/sec",
            "range": "stddev: 6.950180311031382e-7",
            "extra": "mean: 3.727025654731087 usec\nrounds: 65407"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7380327.806119375,
            "unit": "iter/sec",
            "range": "stddev: 1.1569911994684434e-8",
            "extra": "mean: 135.49533655820184 nsec\nrounds: 73390"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8817350.035025384,
            "unit": "iter/sec",
            "range": "stddev: 1.0746647803324694e-8",
            "extra": "mean: 113.41275961912304 nsec\nrounds: 88418"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1470639.4585977995,
            "unit": "iter/sec",
            "range": "stddev: 2.653948270076637e-7",
            "extra": "mean: 679.9763151693639 nsec\nrounds: 178891"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "7325c2177d364b185247f44a3e3564c6a46b53b9",
          "message": "blog: scan 소개 글 추가 + easy-start uv 설명 보강\n\n- 신규: dartlab-news #02 \"2,700개 종목의 재무 데이터를 한 줄로 꺼낸다\"\n  - scan 19개 축, 프리빌드 parquet, XBRL 정규화, 실전 시나리오 4개\n  - SVG 5개 (hero-map, before-after, axes-overview, pipeline, checklist)\n- 보강: dartlab-news #01 uv 설명 확장\n  - Astral/Rust 배경, pip 4단계 vs uv 2단계, 속도 비교, uv run 상세\n- 운영문서: TOPIC_ROADMAP, WRITING_QUEUE 갱신",
          "timestamp": "2026-04-02T16:16:07+09:00",
          "tree_id": "52474bddb993ad5cd4aa7cac9a5904cb000e2531",
          "url": "https://github.com/eddmpython/dartlab/commit/7325c2177d364b185247f44a3e3564c6a46b53b9"
        },
        "date": 1775114223776,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 530010.9151628828,
            "unit": "iter/sec",
            "range": "stddev: 5.125244129581032e-7",
            "extra": "mean: 1.886753595806004 usec\nrounds: 53952"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 660471.0631169386,
            "unit": "iter/sec",
            "range": "stddev: 6.066756229204741e-7",
            "extra": "mean: 1.5140708743252642 usec\nrounds: 109927"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 524304.199622833,
            "unit": "iter/sec",
            "range": "stddev: 5.856526505256214e-7",
            "extra": "mean: 1.9072897007488527 usec\nrounds: 107435"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 674864.4307367409,
            "unit": "iter/sec",
            "range": "stddev: 3.992439920122046e-7",
            "extra": "mean: 1.4817790869616771 usec\nrounds: 112284"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 813467.9650249414,
            "unit": "iter/sec",
            "range": "stddev: 3.7610349914719355e-7",
            "extra": "mean: 1.2293047089682745 usec\nrounds: 136166"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269035.2827995184,
            "unit": "iter/sec",
            "range": "stddev: 6.657190334255304e-7",
            "extra": "mean: 3.7169845887655826 usec\nrounds: 57166"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7422726.065781833,
            "unit": "iter/sec",
            "range": "stddev: 1.2275452528881455e-8",
            "extra": "mean: 134.7213936143918 nsec\nrounds: 72538"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8921967.81280083,
            "unit": "iter/sec",
            "range": "stddev: 1.1052825886995234e-8",
            "extra": "mean: 112.08289706730906 nsec\nrounds: 84589"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1444244.8985457853,
            "unit": "iter/sec",
            "range": "stddev: 3.0882741590552315e-7",
            "extra": "mean: 692.4033458639204 nsec\nrounds: 155715"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "706281551531d72cf6d2eee25ca2d205d287561d",
          "message": "test: Company facade + CLI + review catalog + show + MCP 테스트 140개 추가",
          "timestamp": "2026-04-02T16:19:31+09:00",
          "tree_id": "ad51b64210def360817a98ee2d67bf3a2946bc43",
          "url": "https://github.com/eddmpython/dartlab/commit/706281551531d72cf6d2eee25ca2d205d287561d"
        },
        "date": 1775114418663,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 532275.295907181,
            "unit": "iter/sec",
            "range": "stddev: 4.875635228363301e-7",
            "extra": "mean: 1.878727056636462 usec\nrounds: 54275"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 654379.109025206,
            "unit": "iter/sec",
            "range": "stddev: 4.850067576955304e-7",
            "extra": "mean: 1.5281661443771444 usec\nrounds: 121581"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 526270.1562042814,
            "unit": "iter/sec",
            "range": "stddev: 5.63642666490802e-7",
            "extra": "mean: 1.9001647503869317 usec\nrounds: 82974"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 660348.7398583632,
            "unit": "iter/sec",
            "range": "stddev: 5.052183197219646e-7",
            "extra": "mean: 1.5143513414055851 usec\nrounds: 146564"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 763078.8040215829,
            "unit": "iter/sec",
            "range": "stddev: 3.7139976096839284e-7",
            "extra": "mean: 1.310480640701581 usec\nrounds: 159949"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269599.9423208963,
            "unit": "iter/sec",
            "range": "stddev: 6.555087328050389e-7",
            "extra": "mean: 3.7091996066146464 usec\nrounds: 73720"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7218450.613496982,
            "unit": "iter/sec",
            "range": "stddev: 1.2086542663547084e-8",
            "extra": "mean: 138.53388400693783 nsec\nrounds: 64521"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8016234.105733902,
            "unit": "iter/sec",
            "range": "stddev: 3.7073608297349466e-8",
            "extra": "mean: 124.74685579413328 nsec\nrounds: 37752"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1471801.6608849776,
            "unit": "iter/sec",
            "range": "stddev: 2.5636791723454414e-7",
            "extra": "mean: 679.4393745952912 nsec\nrounds: 155232"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "011e531091ce04a8065d5b1e756f93a155ddf144",
          "message": "test: analysis 잔여 calc + quant extended + narrative 150개 추가 (annualColsFromPeriods 버그 발견)",
          "timestamp": "2026-04-02T16:32:36+09:00",
          "tree_id": "fc747a2d268d455c8ec1ec3a53781198bf294e8e",
          "url": "https://github.com/eddmpython/dartlab/commit/011e531091ce04a8065d5b1e756f93a155ddf144"
        },
        "date": 1775115204167,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 522386.96191675507,
            "unit": "iter/sec",
            "range": "stddev: 5.173592110336883e-7",
            "extra": "mean: 1.9142897371151368 usec\nrounds: 52841"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 635555.5311389451,
            "unit": "iter/sec",
            "range": "stddev: 5.274698795423243e-7",
            "extra": "mean: 1.5734266338740746 usec\nrounds: 120846"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 511779.9265613617,
            "unit": "iter/sec",
            "range": "stddev: 7.537998412248239e-7",
            "extra": "mean: 1.9539648745486724 usec\nrounds: 104625"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 615185.9858284304,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011543037949034493",
            "extra": "mean: 1.6255246755229085 usec\nrounds: 136370"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 804835.1348201034,
            "unit": "iter/sec",
            "range": "stddev: 6.295578235201089e-7",
            "extra": "mean: 1.2424904887179407 usec\nrounds: 147667"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266862.3652046523,
            "unit": "iter/sec",
            "range": "stddev: 7.429158795491169e-7",
            "extra": "mean: 3.7472500074452864 usec\nrounds: 67218"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7077995.954146293,
            "unit": "iter/sec",
            "range": "stddev: 5.825135455270339e-8",
            "extra": "mean: 141.28292902091863 nsec\nrounds: 73557"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8943073.519954856,
            "unit": "iter/sec",
            "range": "stddev: 1.1784122025257904e-8",
            "extra": "mean: 111.81838075787705 nsec\nrounds: 74047"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1409555.8154604903,
            "unit": "iter/sec",
            "range": "stddev: 3.207268021028653e-7",
            "extra": "mean: 709.4433501899377 nsec\nrounds: 153328"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "255dd0f6c2340b819076859088f21cc2f5ef993e",
          "message": "fix: annualColsFromPeriods 인자 순서 버그 수정 (predictionSignals)",
          "timestamp": "2026-04-02T16:39:30+09:00",
          "tree_id": "e21a27402a139dc74ac1484e2868ab3e2447eb47",
          "url": "https://github.com/eddmpython/dartlab/commit/255dd0f6c2340b819076859088f21cc2f5ef993e"
        },
        "date": 1775115617609,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 573956.4935708387,
            "unit": "iter/sec",
            "range": "stddev: 3.0617987215883876e-7",
            "extra": "mean: 1.7422923360942482 usec\nrounds: 58573"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 683951.2515552326,
            "unit": "iter/sec",
            "range": "stddev: 3.195796700034584e-7",
            "extra": "mean: 1.4620925069237116 usec\nrounds: 126423"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 557333.0735390479,
            "unit": "iter/sec",
            "range": "stddev: 3.5650531163817007e-7",
            "extra": "mean: 1.7942592095782706 usec\nrounds: 104537"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 712829.288775761,
            "unit": "iter/sec",
            "range": "stddev: 2.965338424335707e-7",
            "extra": "mean: 1.4028604263966715 usec\nrounds: 149971"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 837626.0801680359,
            "unit": "iter/sec",
            "range": "stddev: 2.64231657293558e-7",
            "extra": "mean: 1.1938501243889041 usec\nrounds: 178955"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 288989.3398312408,
            "unit": "iter/sec",
            "range": "stddev: 3.9154569946896985e-7",
            "extra": "mean: 3.46033525175691 usec\nrounds: 70717"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8488701.968665687,
            "unit": "iter/sec",
            "range": "stddev: 1.202463708251185e-8",
            "extra": "mean: 117.80364108568024 nsec\nrounds: 85296"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9829568.830900993,
            "unit": "iter/sec",
            "range": "stddev: 8.877893058677323e-9",
            "extra": "mean: 101.7338621055608 nsec\nrounds: 96349"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1524073.3722683066,
            "unit": "iter/sec",
            "range": "stddev: 1.486351207143011e-7",
            "extra": "mean: 656.1363896225557 nsec\nrounds: 148699"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "40b180341dae518b92b253d30d71d76f2fdd660d",
          "message": "fix: scan 블로그 3초→1초 수정 + 축 갯수 숫자 포장 제거\n\n- 전체 \"3초\" → \"1초\" (본문 + SVG 4개)\n- \"19개 축\", \"10축\", \"6축\", \"3축\" 등 갯수 언급 전부 제거\n- H2/H3 제목에서 갯수 빼고 기능 직접 서술\n- BLOG_STRUCTURE.md에 \"축/단계/등급 갯수 강조 금지\" 규칙 추가",
          "timestamp": "2026-04-02T16:40:52+09:00",
          "tree_id": "16f997b700738dc4cbf68d0b34ecef8d0308c27f",
          "url": "https://github.com/eddmpython/dartlab/commit/40b180341dae518b92b253d30d71d76f2fdd660d"
        },
        "date": 1775115701702,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 471264.52040311135,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010063107484875264",
            "extra": "mean: 2.121950532462358 usec\nrounds: 56906"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 658829.0581634949,
            "unit": "iter/sec",
            "range": "stddev: 4.319068369476242e-7",
            "extra": "mean: 1.5178444053265183 usec\nrounds: 148302"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 523958.018046702,
            "unit": "iter/sec",
            "range": "stddev: 5.662465406923386e-7",
            "extra": "mean: 1.908549856204065 usec\nrounds: 139782"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 667844.7107404257,
            "unit": "iter/sec",
            "range": "stddev: 4.2915736239454977e-7",
            "extra": "mean: 1.4973540763560444 usec\nrounds: 137476"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 811043.0900106946,
            "unit": "iter/sec",
            "range": "stddev: 3.780195558718784e-7",
            "extra": "mean: 1.2329801120515236 usec\nrounds: 169751"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268503.5640868963,
            "unit": "iter/sec",
            "range": "stddev: 6.60159819838419e-7",
            "extra": "mean: 3.724345348638903 usec\nrounds: 71603"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7331512.598338573,
            "unit": "iter/sec",
            "range": "stddev: 1.2500376566380806e-8",
            "extra": "mean: 136.39750141418492 nsec\nrounds: 72485"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8973349.209171291,
            "unit": "iter/sec",
            "range": "stddev: 1.0975115054852108e-8",
            "extra": "mean: 111.44111041370606 nsec\nrounds: 84446"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1460736.826480972,
            "unit": "iter/sec",
            "range": "stddev: 2.8005428651371485e-7",
            "extra": "mean: 684.5860129432605 nsec\nrounds: 170329"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2596d104377816928e210b073eaf3cbf7df1bed9",
          "message": "fix: annualColsFromPeriods 인자 순서 버그 전수 수정 (8개 파일 23곳)\n\nasset.py, capitalAllocation.py, cashflow.py, earningsQuality.py,\npredictionSignals.py, profitability.py — _MAX_YEARS가 positional로 basePeriod에\n들어가던 버그. 전부 maxYears= 키워드로 변경.\n\nxfail 36개 → 0개 (전부 통과)",
          "timestamp": "2026-04-02T16:45:40+09:00",
          "tree_id": "88a1b7e2f511ae40217419aab2c488d60634da83",
          "url": "https://github.com/eddmpython/dartlab/commit/2596d104377816928e210b073eaf3cbf7df1bed9"
        },
        "date": 1775115997488,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 543559.3755967094,
            "unit": "iter/sec",
            "range": "stddev: 5.348056553695842e-7",
            "extra": "mean: 1.8397254189613022 usec\nrounds: 52866"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 658004.4220482511,
            "unit": "iter/sec",
            "range": "stddev: 5.800970474795093e-7",
            "extra": "mean: 1.5197466255426935 usec\nrounds: 112537"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 525860.6261972483,
            "unit": "iter/sec",
            "range": "stddev: 5.689432587080344e-7",
            "extra": "mean: 1.9016445616616746 usec\nrounds: 97097"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675992.5460038454,
            "unit": "iter/sec",
            "range": "stddev: 4.588497399852178e-7",
            "extra": "mean: 1.4793062525785772 usec\nrounds: 130634"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 805212.6453335108,
            "unit": "iter/sec",
            "range": "stddev: 4.208953101982671e-7",
            "extra": "mean: 1.241907967783852 usec\nrounds: 168039"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268377.2457336557,
            "unit": "iter/sec",
            "range": "stddev: 6.981778615069128e-7",
            "extra": "mean: 3.7260983034024613 usec\nrounds: 62419"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7283197.675092686,
            "unit": "iter/sec",
            "range": "stddev: 1.1990342106720899e-8",
            "extra": "mean: 137.30232853899219 nsec\nrounds: 73282"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8896699.78771718,
            "unit": "iter/sec",
            "range": "stddev: 2.086581161060366e-8",
            "extra": "mean: 112.40123010339227 nsec\nrounds: 78530"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1460905.7755248835,
            "unit": "iter/sec",
            "range": "stddev: 2.6210704293093127e-7",
            "extra": "mean: 684.506842777532 nsec\nrounds: 174490"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "1ff328249af7832c450a20834e54944ff01bc0e0",
          "message": "fix: numpy를 base 의존성에 추가 (quant 엔진 필수)",
          "timestamp": "2026-04-02T17:01:54+09:00",
          "tree_id": "7bec5b6221b3ee965325acbe8af397b35a9e144c",
          "url": "https://github.com/eddmpython/dartlab/commit/1ff328249af7832c450a20834e54944ff01bc0e0"
        },
        "date": 1775116965372,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 540895.0582480573,
            "unit": "iter/sec",
            "range": "stddev: 4.618410628497708e-7",
            "extra": "mean: 1.8487874584008397 usec\nrounds: 55575"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 668018.2846434517,
            "unit": "iter/sec",
            "range": "stddev: 4.998250408124603e-7",
            "extra": "mean: 1.4969650127671883 usec\nrounds: 140194"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 526408.1570968882,
            "unit": "iter/sec",
            "range": "stddev: 4.964104232915314e-7",
            "extra": "mean: 1.8996666113894296 usec\nrounds: 126663"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 683721.5424285795,
            "unit": "iter/sec",
            "range": "stddev: 3.918111272231455e-7",
            "extra": "mean: 1.462583724432609 usec\nrounds: 143823"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 805307.5427190262,
            "unit": "iter/sec",
            "range": "stddev: 3.7191944779873213e-7",
            "extra": "mean: 1.2417616214342382 usec\nrounds: 167729"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 272273.95747370936,
            "unit": "iter/sec",
            "range": "stddev: 6.916900647243791e-7",
            "extra": "mean: 3.6727713854034665 usec\nrounds: 74151"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7302662.912554569,
            "unit": "iter/sec",
            "range": "stddev: 1.6984540404718664e-8",
            "extra": "mean: 136.93634938028197 nsec\nrounds: 73015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8963358.451184003,
            "unit": "iter/sec",
            "range": "stddev: 1.0516799668607447e-8",
            "extra": "mean: 111.56532514527592 nsec\nrounds: 88176"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1430898.1212581506,
            "unit": "iter/sec",
            "range": "stddev: 4.48960695088778e-7",
            "extra": "mean: 698.861774394341 nsec\nrounds: 157431"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "623a7ef143d3894b3c7f18495784c8acc9532a45",
          "message": "fix: scan 글 마무리를 AI 질문 섹션으로 교체 + 다음글 예고 금지 규칙\n\n- \"다음 단계\" 섹션 제거 → \"AI에게 물어보면 된다\" 섹션으로 교체\n  - dartlab ask 예시 3개 (ROE+부채, 거버넌스+배당, 성장+현금흐름)\n  - 코드 vs 질문 양쪽 경로 안내\n- BLOG_STRUCTURE.md에 \"다음 글 예고/미래 글 링크 금지\" 규칙 추가",
          "timestamp": "2026-04-02T17:10:38+09:00",
          "tree_id": "c785569b8fbf56b017f24af45fb310716e18ab62",
          "url": "https://github.com/eddmpython/dartlab/commit/623a7ef143d3894b3c7f18495784c8acc9532a45"
        },
        "date": 1775117495573,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 543359.4223173187,
            "unit": "iter/sec",
            "range": "stddev: 4.89486000872325e-7",
            "extra": "mean: 1.8404024277985296 usec\nrounds: 56266"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 657513.1951605239,
            "unit": "iter/sec",
            "range": "stddev: 4.46949567604332e-7",
            "extra": "mean: 1.520882025425911 usec\nrounds: 133995"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 514325.0640054258,
            "unit": "iter/sec",
            "range": "stddev: 4.848910763564351e-7",
            "extra": "mean: 1.9442956798804787 usec\nrounds: 129116"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 683859.7370142422,
            "unit": "iter/sec",
            "range": "stddev: 3.84116996434371e-7",
            "extra": "mean: 1.4622881650644302 usec\nrounds: 177905"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 891964.5887075007,
            "unit": "iter/sec",
            "range": "stddev: 1.5184264111296488e-7",
            "extra": "mean: 1.1211207402852703 usec\nrounds: 174795"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 273844.5936175746,
            "unit": "iter/sec",
            "range": "stddev: 6.366090820208889e-7",
            "extra": "mean: 3.651706198722715 usec\nrounds: 74935"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7332153.967544597,
            "unit": "iter/sec",
            "range": "stddev: 1.1045143458302573e-8",
            "extra": "mean: 136.3855702466763 nsec\nrounds: 74047"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9049897.408368694,
            "unit": "iter/sec",
            "range": "stddev: 1.02019418531694e-8",
            "extra": "mean: 110.49849019009562 nsec\nrounds: 88488"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1450412.8917430108,
            "unit": "iter/sec",
            "range": "stddev: 2.8144791333319525e-7",
            "extra": "mean: 689.4588469896084 nsec\nrounds: 157704"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "6228ca3925c2565c225a885f5b212032906216bb",
          "message": "fix: AI 섹션에 scan 내부 호출 흐름 구체적으로 보여줌\n\n- \"AI에게 물어보면 된다\" → \"코드를 안 짜도 된다 — AI에게 물어보면 scan이 돌아간다\"\n- AI가 질문을 받으면 뒤에서 scan 축을 조합하는 과정을 단계별로 설명\n- 질문별로 어떤 scan 축이 호출되는지 매핑 (governance+dividendTrend 등)",
          "timestamp": "2026-04-02T17:12:56+09:00",
          "tree_id": "2e4c19c96dfaad830e1f727d1274dc4e9adc2f64",
          "url": "https://github.com/eddmpython/dartlab/commit/6228ca3925c2565c225a885f5b212032906216bb"
        },
        "date": 1775117628954,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 543161.0817077582,
            "unit": "iter/sec",
            "range": "stddev: 4.628014502053384e-7",
            "extra": "mean: 1.841074468840606 usec\nrounds: 56010"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 654077.6149333678,
            "unit": "iter/sec",
            "range": "stddev: 4.992531527309697e-7",
            "extra": "mean: 1.528870545587884 usec\nrounds: 132031"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 526343.651714835,
            "unit": "iter/sec",
            "range": "stddev: 5.931984254095464e-7",
            "extra": "mean: 1.8998994226338362 usec\nrounds: 109806"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 672700.2073619638,
            "unit": "iter/sec",
            "range": "stddev: 3.914564310638942e-7",
            "extra": "mean: 1.4865462936626153 usec\nrounds: 151241"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 810799.4161570768,
            "unit": "iter/sec",
            "range": "stddev: 3.6637187389032505e-7",
            "extra": "mean: 1.2333506661113198 usec\nrounds: 157928"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268061.3008787644,
            "unit": "iter/sec",
            "range": "stddev: 7.749895538569164e-7",
            "extra": "mean: 3.7304899913630876 usec\nrounds: 63695"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7270389.383301299,
            "unit": "iter/sec",
            "range": "stddev: 1.7351100459918915e-8",
            "extra": "mean: 137.5442149352839 nsec\nrounds: 61237"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8820896.09439358,
            "unit": "iter/sec",
            "range": "stddev: 1.2748273280693847e-8",
            "extra": "mean: 113.36716692939893 nsec\nrounds: 87474"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1455630.1217245234,
            "unit": "iter/sec",
            "range": "stddev: 2.6329008141995793e-7",
            "extra": "mean: 686.9877072997593 nsec\nrounds: 179212"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "22a582b3934bacae6abb315b19aca09e2d43248b",
          "message": "test: Round 1-6 대량 테스트 추가 — providers/analysis/review/ai/gather (373개)",
          "timestamp": "2026-04-02T17:45:15+09:00",
          "tree_id": "b88625317dfe26780f9deb32a234eebf03d60c60",
          "url": "https://github.com/eddmpython/dartlab/commit/22a582b3934bacae6abb315b19aca09e2d43248b"
        },
        "date": 1775119573324,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 511524.2599872879,
            "unit": "iter/sec",
            "range": "stddev: 4.983826241097375e-7",
            "extra": "mean: 1.9549414919731303 usec\nrounds: 54813"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 662599.0869790929,
            "unit": "iter/sec",
            "range": "stddev: 4.766523534778394e-7",
            "extra": "mean: 1.5092082371546538 usec\nrounds: 149858"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 530885.8770392657,
            "unit": "iter/sec",
            "range": "stddev: 5.741888992531445e-7",
            "extra": "mean: 1.8836440057079111 usec\nrounds: 126679"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 677138.2364366507,
            "unit": "iter/sec",
            "range": "stddev: 4.1957419434816915e-7",
            "extra": "mean: 1.4768033263966394 usec\nrounds: 186568"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 782602.3415079287,
            "unit": "iter/sec",
            "range": "stddev: 3.6835468113802733e-7",
            "extra": "mean: 1.2777881523753003 usec\nrounds: 199601"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266931.5180394498,
            "unit": "iter/sec",
            "range": "stddev: 6.927666969801339e-7",
            "extra": "mean: 3.7462792230185795 usec\nrounds: 72229"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7364837.487943031,
            "unit": "iter/sec",
            "range": "stddev: 1.2913131803950532e-8",
            "extra": "mean: 135.7803212409098 nsec\nrounds: 73932"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8736729.367931461,
            "unit": "iter/sec",
            "range": "stddev: 2.2309588237635e-8",
            "extra": "mean: 114.45930827050027 nsec\nrounds: 88098"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1461791.6234219575,
            "unit": "iter/sec",
            "range": "stddev: 4.170052346519754e-7",
            "extra": "mean: 684.0920306131363 nsec\nrounds: 193088"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "9dbd3e65eacf2c026d78832e95e6875591f4f591",
          "message": "blog: Company 소개 글 추가 — 종목코드 하나면 끝난다\n\n- 신규: dartlab-news #03 \"종목코드 하나면 끝난다 — dartlab.Company\"\n  - IS/BS/CF, ratios, show/select, diff, notes, trace, sections\n  - AI가 Company를 도구로 쓰는 흐름 (ask → Company 내부 호출)\n  - SVG 5개 (hero-map, financial-statements, show-select, source-priority, notes)\n- 운영문서: TOPIC_ROADMAP 46편, WRITING_QUEUE 130번 추가",
          "timestamp": "2026-04-02T17:53:07+09:00",
          "tree_id": "230424249ce62497421932d7b8e6945374a61cc1",
          "url": "https://github.com/eddmpython/dartlab/commit/9dbd3e65eacf2c026d78832e95e6875591f4f591"
        },
        "date": 1775120046389,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 528126.3045325284,
            "unit": "iter/sec",
            "range": "stddev: 5.376395225160564e-7",
            "extra": "mean: 1.893486447120166 usec\nrounds: 57036"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 633853.1856062581,
            "unit": "iter/sec",
            "range": "stddev: 4.5120982057354963e-7",
            "extra": "mean: 1.577652400758285 usec\nrounds: 130311"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 517068.62663986033,
            "unit": "iter/sec",
            "range": "stddev: 5.115535816001406e-7",
            "extra": "mean: 1.9339792601582508 usec\nrounds: 122325"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 656276.3338402782,
            "unit": "iter/sec",
            "range": "stddev: 4.6368002077328274e-7",
            "extra": "mean: 1.5237483792054214 usec\nrounds: 151470"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 781620.2957641403,
            "unit": "iter/sec",
            "range": "stddev: 3.4907565794170484e-7",
            "extra": "mean: 1.2793935948430863 usec\nrounds: 192345"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 259049.21599392206,
            "unit": "iter/sec",
            "range": "stddev: 6.360482560036009e-7",
            "extra": "mean: 3.8602703203064803 usec\nrounds: 70742"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 6794850.017135779,
            "unit": "iter/sec",
            "range": "stddev: 2.3254496112849105e-8",
            "extra": "mean: 147.17028300523523 nsec\nrounds: 198847"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8470133.613844886,
            "unit": "iter/sec",
            "range": "stddev: 1.0933392723721395e-8",
            "extra": "mean: 118.06189200669118 nsec\nrounds: 84524"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1419262.8603246822,
            "unit": "iter/sec",
            "range": "stddev: 2.6990053719911626e-7",
            "extra": "mean: 704.5911141303535 nsec\nrounds: 175132"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "c7b4cf990b96de73149572df794ceffb2b699ec4",
          "message": "refactor: c.insights 제거 — analysis(\"financial\", \"종합평가\")로 통합\n\n- dart/edgar company.py에서 insights property 제거\n- 노트북 5개 파일에서 c.insights → c.analysis(\"financial\", \"종합평가\") 교체\n- 시스템 프롬프트에서 c.insights 참조 제거\n- 엔진 체계: analysis 내부 기능을 Company에 직접 노출하지 않음",
          "timestamp": "2026-04-02T17:59:05+09:00",
          "tree_id": "e753e111c3aa9eb82951405bedb3e61003643489",
          "url": "https://github.com/eddmpython/dartlab/commit/c7b4cf990b96de73149572df794ceffb2b699ec4"
        },
        "date": 1775120401212,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 573705.5432245133,
            "unit": "iter/sec",
            "range": "stddev: 2.8633422698586093e-7",
            "extra": "mean: 1.7430544498132228 usec\nrounds: 63104"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 700249.8977098747,
            "unit": "iter/sec",
            "range": "stddev: 2.6106943516630154e-7",
            "extra": "mean: 1.4280616152468426 usec\nrounds: 132451"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 573123.7361595021,
            "unit": "iter/sec",
            "range": "stddev: 3.112406912548666e-7",
            "extra": "mean: 1.7448239130715344 usec\nrounds: 118822"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 740276.1300784528,
            "unit": "iter/sec",
            "range": "stddev: 2.0563178398889604e-7",
            "extra": "mean: 1.350847284369445 usec\nrounds: 176773"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 977412.529500465,
            "unit": "iter/sec",
            "range": "stddev: 8.761049659535516e-8",
            "extra": "mean: 1.0231094546241175 usec\nrounds: 181160"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 294527.42623251333,
            "unit": "iter/sec",
            "range": "stddev: 3.641094930532069e-7",
            "extra": "mean: 3.395269543456896 usec\nrounds: 69128"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8563441.812196884,
            "unit": "iter/sec",
            "range": "stddev: 7.977284783355944e-9",
            "extra": "mean: 116.77547672195342 nsec\nrounds: 76208"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9890044.359719502,
            "unit": "iter/sec",
            "range": "stddev: 7.1233016113357465e-9",
            "extra": "mean: 101.11178106266468 nsec\nrounds: 96201"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1526103.6491428702,
            "unit": "iter/sec",
            "range": "stddev: 1.5302038014524636e-7",
            "extra": "mean: 655.2634878775408 nsec\nrounds: 156789"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "5b2f3c74f70fe7d061783a6a48d902e10abd19e5",
          "message": "fix: test_skips_sparse_year Polars 타입 불일치 수정",
          "timestamp": "2026-04-02T18:00:31+09:00",
          "tree_id": "3fde573d1a71b13fe0f0c117a28a30635f4139fb",
          "url": "https://github.com/eddmpython/dartlab/commit/5b2f3c74f70fe7d061783a6a48d902e10abd19e5"
        },
        "date": 1775120489373,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 544987.4579154468,
            "unit": "iter/sec",
            "range": "stddev: 4.98831032945408e-7",
            "extra": "mean: 1.8349046119794319 usec\nrounds: 50824"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 638532.3162307725,
            "unit": "iter/sec",
            "range": "stddev: 4.509638607135487e-7",
            "extra": "mean: 1.5660914484374966 usec\nrounds: 148324"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520726.163591216,
            "unit": "iter/sec",
            "range": "stddev: 5.495253819457301e-7",
            "extra": "mean: 1.9203951518461184 usec\nrounds: 120541"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 667690.5797651798,
            "unit": "iter/sec",
            "range": "stddev: 3.979401335384063e-7",
            "extra": "mean: 1.4976997284456075 usec\nrounds: 146564"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 804896.1092877691,
            "unit": "iter/sec",
            "range": "stddev: 3.5803423152465854e-7",
            "extra": "mean: 1.2423963645256941 usec\nrounds: 197278"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 265264.07201699394,
            "unit": "iter/sec",
            "range": "stddev: 6.825914845895856e-7",
            "extra": "mean: 3.7698282786518322 usec\nrounds: 67627"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7274313.324649168,
            "unit": "iter/sec",
            "range": "stddev: 1.6498970701662428e-8",
            "extra": "mean: 137.47002024390102 nsec\nrounds: 25686"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8805583.854911055,
            "unit": "iter/sec",
            "range": "stddev: 1.2277058327582649e-8",
            "extra": "mean: 113.56430379596914 nsec\nrounds: 88724"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1463927.5373087437,
            "unit": "iter/sec",
            "range": "stddev: 2.6819551910907924e-7",
            "extra": "mean: 683.0939199616266 nsec\nrounds: 161265"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "597c13925dc0ddf94541852499faf69de9d73d4d",
          "message": "release: v0.8.4 — 테스트 1,991개 + scan 일관성 + insights 제거 + annualCols 버그 수정",
          "timestamp": "2026-04-02T18:06:50+09:00",
          "tree_id": "686134ceab0294047eb8f4a46df390453e333f6a",
          "url": "https://github.com/eddmpython/dartlab/commit/597c13925dc0ddf94541852499faf69de9d73d4d"
        },
        "date": 1775120871523,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 543182.804752602,
            "unit": "iter/sec",
            "range": "stddev: 5.268366663610135e-7",
            "extra": "mean: 1.8410008403256801 usec\nrounds: 49981"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 665308.0683049886,
            "unit": "iter/sec",
            "range": "stddev: 5.680393109027985e-7",
            "extra": "mean: 1.503063088574454 usec\nrounds: 112778"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 505097.4531188953,
            "unit": "iter/sec",
            "range": "stddev: 6.873606276006355e-7",
            "extra": "mean: 1.9798159619003446 usec\nrounds: 117981"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 684861.1899794689,
            "unit": "iter/sec",
            "range": "stddev: 5.192402704055112e-7",
            "extra": "mean: 1.4601499028291824 usec\nrounds: 163079"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 819530.8346893948,
            "unit": "iter/sec",
            "range": "stddev: 4.296565278425476e-7",
            "extra": "mean: 1.220210341907396 usec\nrounds: 146994"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269548.23005188484,
            "unit": "iter/sec",
            "range": "stddev: 6.829242073032404e-7",
            "extra": "mean: 3.709911208867934 usec\nrounds: 67304"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7335908.381349271,
            "unit": "iter/sec",
            "range": "stddev: 1.4414324279529351e-8",
            "extra": "mean: 136.31577004729073 nsec\nrounds: 73015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8796776.553517707,
            "unit": "iter/sec",
            "range": "stddev: 1.2410154743992194e-8",
            "extra": "mean: 113.67800397295689 nsec\nrounds: 87093"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1456416.4437845526,
            "unit": "iter/sec",
            "range": "stddev: 2.5852526183736114e-7",
            "extra": "mean: 686.6168013054443 nsec\nrounds: 162023"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2ebc061566933f62103a420de015215c0fdf4984",
          "message": "fix: CI 테스트 실패 — stdin 방지 autouse + 503 허용 + noqa 위치",
          "timestamp": "2026-04-02T18:24:00+09:00",
          "tree_id": "26e2151904f626826612415b1744772b108dd18f",
          "url": "https://github.com/eddmpython/dartlab/commit/2ebc061566933f62103a420de015215c0fdf4984"
        },
        "date": 1775121896503,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 520749.6316600443,
            "unit": "iter/sec",
            "range": "stddev: 4.824676054805853e-7",
            "extra": "mean: 1.9203086074438547 usec\nrounds: 55057"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 641068.3128543248,
            "unit": "iter/sec",
            "range": "stddev: 4.698483044924981e-7",
            "extra": "mean: 1.5598961607500916 usec\nrounds: 132031"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 524699.9150029242,
            "unit": "iter/sec",
            "range": "stddev: 5.80900319191876e-7",
            "extra": "mean: 1.9058512711869353 usec\nrounds: 130822"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 643157.9658879326,
            "unit": "iter/sec",
            "range": "stddev: 4.798054045013146e-7",
            "extra": "mean: 1.5548279785657597 usec\nrounds: 157928"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 780920.484648977,
            "unit": "iter/sec",
            "range": "stddev: 4.121913454966786e-7",
            "extra": "mean: 1.2805401057567327 usec\nrounds: 195695"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 258643.7142465681,
            "unit": "iter/sec",
            "range": "stddev: 0.000001045609515726048",
            "extra": "mean: 3.866322454087124 usec\nrounds: 59134"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7185678.865431447,
            "unit": "iter/sec",
            "range": "stddev: 1.6827300608343757e-8",
            "extra": "mean: 139.16569592481468 nsec\nrounds: 71969"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8603333.186897226,
            "unit": "iter/sec",
            "range": "stddev: 2.487296803340938e-8",
            "extra": "mean: 116.23401980095204 nsec\nrounds: 88176"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1450193.3070631253,
            "unit": "iter/sec",
            "range": "stddev: 2.733422601058512e-7",
            "extra": "mean: 689.5632431411236 nsec\nrounds: 160721"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "a752b8d991e598ba32d5cafda03ed9aeafadd788",
          "message": "test: integration 테스트 28개 + colab credit 노트북\n\n- test_analysis_integration.py: 24축 전체 실행 (9 tests)\n- test_review_integration.py: buildBlocks 전체 파이프라인 (9 tests)\n- test_credit_integration.py: evaluateCompany end-to-end (10 tests)\n- notebooks/colab/08_credit.ipynb: credit 노트북 신규",
          "timestamp": "2026-04-02T20:22:30+09:00",
          "tree_id": "ea97b1e87249a19f4a6f6e15d321c4509b9182bc",
          "url": "https://github.com/eddmpython/dartlab/commit/a752b8d991e598ba32d5cafda03ed9aeafadd788"
        },
        "date": 1775129008822,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 540093.7701276502,
            "unit": "iter/sec",
            "range": "stddev: 4.733781370430938e-7",
            "extra": "mean: 1.851530336599979 usec\nrounds: 55082"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 659894.0745121582,
            "unit": "iter/sec",
            "range": "stddev: 5.018190744385674e-7",
            "extra": "mean: 1.5153947256448288 usec\nrounds: 119977"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527759.4638028701,
            "unit": "iter/sec",
            "range": "stddev: 5.055242791050103e-7",
            "extra": "mean: 1.894802592064028 usec\nrounds: 123840"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 659139.6892495592,
            "unit": "iter/sec",
            "range": "stddev: 4.1971588550733886e-7",
            "extra": "mean: 1.5171290946514167 usec\nrounds: 138046"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 908630.813471878,
            "unit": "iter/sec",
            "range": "stddev: 1.6169096927230294e-7",
            "extra": "mean: 1.100556997598398 usec\nrounds: 173581"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267829.8988893482,
            "unit": "iter/sec",
            "range": "stddev: 6.991227932445038e-7",
            "extra": "mean: 3.733713092327836 usec\nrounds: 71706"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7342817.320327028,
            "unit": "iter/sec",
            "range": "stddev: 1.250196819435879e-8",
            "extra": "mean: 136.18750901397382 nsec\nrounds: 73497"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8973702.34341097,
            "unit": "iter/sec",
            "range": "stddev: 1.197282888529411e-8",
            "extra": "mean: 111.43672496940572 nsec\nrounds: 88332"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1458223.1571693586,
            "unit": "iter/sec",
            "range": "stddev: 2.8505709446458966e-7",
            "extra": "mean: 685.7660949104373 nsec\nrounds: 160206"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "1cf4dd1bb98299d5dec85635ac56b53e554bad1a",
          "message": "ci: coverage fail_under 25→30% (현재 35%)",
          "timestamp": "2026-04-02T20:46:17+09:00",
          "tree_id": "70bc4f5da1ad3435369ba32b288cd9aaced8b09c",
          "url": "https://github.com/eddmpython/dartlab/commit/1cf4dd1bb98299d5dec85635ac56b53e554bad1a"
        },
        "date": 1775130427683,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542853.0259637488,
            "unit": "iter/sec",
            "range": "stddev: 5.10437272895412e-7",
            "extra": "mean: 1.8421192333314524 usec\nrounds: 49097"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 663679.9426817072,
            "unit": "iter/sec",
            "range": "stddev: 4.778384248199962e-7",
            "extra": "mean: 1.5067503712095571 usec\nrounds: 106406"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 528327.5784564865,
            "unit": "iter/sec",
            "range": "stddev: 5.176458946537418e-7",
            "extra": "mean: 1.892765096460625 usec\nrounds: 109794"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 671298.4544176313,
            "unit": "iter/sec",
            "range": "stddev: 4.2421146931417865e-7",
            "extra": "mean: 1.4896503834014125 usec\nrounds: 133798"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 825193.7776913482,
            "unit": "iter/sec",
            "range": "stddev: 4.0282494003324025e-7",
            "extra": "mean: 1.2118365734624281 usec\nrounds: 179212"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269946.9101720912,
            "unit": "iter/sec",
            "range": "stddev: 6.698991788914837e-7",
            "extra": "mean: 3.7044321024548856 usec\nrounds: 67079"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7286919.028018573,
            "unit": "iter/sec",
            "range": "stddev: 1.2005912788822395e-8",
            "extra": "mean: 137.23220968353695 nsec\nrounds: 73282"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8909000.095084896,
            "unit": "iter/sec",
            "range": "stddev: 1.5611400168262352e-8",
            "extra": "mean: 112.24604212898157 nsec\nrounds: 87398"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1335630.3680540042,
            "unit": "iter/sec",
            "range": "stddev: 4.877922253344905e-7",
            "extra": "mean: 748.7101401093379 nsec\nrounds: 138046"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "45c6f0ce975892044b433c9cdbd83e7488ec91ac",
          "message": "feat: fixture integration 테스트 62개 + CI DARTLAB_DATA_DIR + 문서 동기화\n\nGoal 1: 커버리지\n- tests/fixtures/dart/ 구조 재배치 (DATA_RELEASES 레이아웃 매칭)\n- CI에 DARTLAB_DATA_DIR 설정 → fixture 데이터로 Company(\"005930\") 로드\n- test_fixture_company_full.py (21), test_fixture_analysis_real.py (24),\n  test_fixture_review_real.py (10), test_fixture_credit_real.py (8)\n- -m \"not requires_data and not heavy\" → -m \"not heavy\" 변경\n\nGoal 2: VSCode v0.1.3\n\nGoal 3: 문서\n- docs/api/export.md 생성 (nav 404 해결)\n- navigation.ts에 CLI 페이지 추가",
          "timestamp": "2026-04-02T21:55:04+09:00",
          "tree_id": "5f65c3f65fca24044c58142d971213b7ca288abf",
          "url": "https://github.com/eddmpython/dartlab/commit/45c6f0ce975892044b433c9cdbd83e7488ec91ac"
        },
        "date": 1775134566289,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542145.7446526007,
            "unit": "iter/sec",
            "range": "stddev: 5.277818259795437e-7",
            "extra": "mean: 1.8445224551947481 usec\nrounds: 53551"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 676810.5160817935,
            "unit": "iter/sec",
            "range": "stddev: 4.772218091762939e-7",
            "extra": "mean: 1.4775184135571982 usec\nrounds: 112906"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527339.9265769549,
            "unit": "iter/sec",
            "range": "stddev: 5.699371710052378e-7",
            "extra": "mean: 1.8963100451944817 usec\nrounds: 123840"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 672149.7868165747,
            "unit": "iter/sec",
            "range": "stddev: 5.209498231629619e-7",
            "extra": "mean: 1.487763619975518 usec\nrounds: 163106"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 911309.8888431011,
            "unit": "iter/sec",
            "range": "stddev: 1.823362536553932e-7",
            "extra": "mean: 1.0973215722145737 usec\nrounds: 179212"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 265293.54441209807,
            "unit": "iter/sec",
            "range": "stddev: 8.394282277933493e-7",
            "extra": "mean: 3.7694094751383536 usec\nrounds: 69804"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7206452.165941805,
            "unit": "iter/sec",
            "range": "stddev: 1.2726456322569091e-8",
            "extra": "mean: 138.7645372470617 nsec\nrounds: 72328"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9000967.726411028,
            "unit": "iter/sec",
            "range": "stddev: 2.4209915109706962e-8",
            "extra": "mean: 111.09916515595948 nsec\nrounds: 89358"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1457864.204959469,
            "unit": "iter/sec",
            "range": "stddev: 2.9910987553779626e-7",
            "extra": "mean: 685.9349427732205 nsec\nrounds: 185529"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "5f55982a59d38c66be9abbb216b91afea8e19ef3",
          "message": "fix: CI 마커를 원래대로 — requires_data 제외, fixture integration은 포함",
          "timestamp": "2026-04-02T22:33:58+09:00",
          "tree_id": "6bdcf5447ae5d289238e4c34550da54aded62bcd",
          "url": "https://github.com/eddmpython/dartlab/commit/5f55982a59d38c66be9abbb216b91afea8e19ef3"
        },
        "date": 1775136896232,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 537346.0460328404,
            "unit": "iter/sec",
            "range": "stddev: 7.160747720567538e-7",
            "extra": "mean: 1.8609981545093277 usec\nrounds: 52560"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 657801.5062337167,
            "unit": "iter/sec",
            "range": "stddev: 4.571266574177189e-7",
            "extra": "mean: 1.5202154305263937 usec\nrounds: 128784"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520445.32196968637,
            "unit": "iter/sec",
            "range": "stddev: 5.798371475346358e-7",
            "extra": "mean: 1.9214314314813756 usec\nrounds: 122775"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 649667.9049717289,
            "unit": "iter/sec",
            "range": "stddev: 4.591511472714332e-7",
            "extra": "mean: 1.539247963994029 usec\nrounds: 162576"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 867232.2537121773,
            "unit": "iter/sec",
            "range": "stddev: 3.7094781177688435e-7",
            "extra": "mean: 1.15309364442975 usec\nrounds: 173281"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269139.75435428735,
            "unit": "iter/sec",
            "range": "stddev: 6.021547340285061e-7",
            "extra": "mean: 3.7155417727090234 usec\nrounds: 64025"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7518854.136887548,
            "unit": "iter/sec",
            "range": "stddev: 1.1908675658734861e-8",
            "extra": "mean: 132.9989891802786 nsec\nrounds: 73020"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8770808.043235447,
            "unit": "iter/sec",
            "range": "stddev: 1.0917266573484259e-8",
            "extra": "mean: 114.01458053471568 nsec\nrounds: 88732"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1451661.0900410614,
            "unit": "iter/sec",
            "range": "stddev: 3.4578760512517164e-7",
            "extra": "mean: 688.8660217321897 nsec\nrounds: 161265"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "49238f051f07633536f67309a6d9cc42cd8fdb3b",
          "message": "fix: company.py 독스트링에서 c.insights 잔존 참조 제거",
          "timestamp": "2026-04-03T01:59:34+09:00",
          "tree_id": "f48425f9b5ece79a2caad608df1d1664a01ae7a3",
          "url": "https://github.com/eddmpython/dartlab/commit/49238f051f07633536f67309a6d9cc42cd8fdb3b"
        },
        "date": 1775149236992,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 540035.817081084,
            "unit": "iter/sec",
            "range": "stddev: 5.083056707249384e-7",
            "extra": "mean: 1.8517290305021648 usec\nrounds: 55390"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 650413.4018061666,
            "unit": "iter/sec",
            "range": "stddev: 4.6639156075213495e-7",
            "extra": "mean: 1.5374836945595654 usec\nrounds: 118120"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 523633.01106601214,
            "unit": "iter/sec",
            "range": "stddev: 5.674587723598781e-7",
            "extra": "mean: 1.9097344492552135 usec\nrounds: 119962"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 670312.8481587385,
            "unit": "iter/sec",
            "range": "stddev: 3.8843656254130247e-7",
            "extra": "mean: 1.4918407169829266 usec\nrounds: 167758"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 794518.8952266761,
            "unit": "iter/sec",
            "range": "stddev: 3.874153234937212e-7",
            "extra": "mean: 1.2586233077750781 usec\nrounds: 197668"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268488.49220353685,
            "unit": "iter/sec",
            "range": "stddev: 6.200935241023692e-7",
            "extra": "mean: 3.7245544186747335 usec\nrounds: 68414"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7447415.939027424,
            "unit": "iter/sec",
            "range": "stddev: 1.2229823126531205e-8",
            "extra": "mean: 134.27476163371 nsec\nrounds: 73878"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8974034.927172445,
            "unit": "iter/sec",
            "range": "stddev: 1.1076708841024274e-8",
            "extra": "mean: 111.43259504953608 nsec\nrounds: 88480"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1414294.5391010558,
            "unit": "iter/sec",
            "range": "stddev: 3.091345322022033e-7",
            "extra": "mean: 707.0662951407654 nsec\nrounds: 166890"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "ec5a3420f25ccbc5115fe8bb71e9c15c96c82602",
          "message": "feat(vscode): 프로바이더 연결 플로우 전면 개선 + 입력창 항상 활성\n\n- 웰컴 화면: 프로바이더 카드 (키 발급/연결 버튼)\n- 프로바이더 선택 시 API 키 입력 InputBox 자동 오픈\n- 키 없으면 needCredential 이벤트로 signupUrl 브라우저 + 키 입력\n- 헤더 드롭다운: 미설정 시에도 표시\n- 입력창 항상 활성화\n- 자동설치: PowerShell 5.x 호환\n- status API에 description/authKind/signupUrl 포함",
          "timestamp": "2026-04-03T02:06:37+09:00",
          "tree_id": "74801a75f8e8b1dc3061c4939e78b65612450985",
          "url": "https://github.com/eddmpython/dartlab/commit/ec5a3420f25ccbc5115fe8bb71e9c15c96c82602"
        },
        "date": 1775149659484,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 537711.458641293,
            "unit": "iter/sec",
            "range": "stddev: 5.22114465672444e-7",
            "extra": "mean: 1.8597334758809736 usec\nrounds: 50033"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 662493.9636392841,
            "unit": "iter/sec",
            "range": "stddev: 4.7321548514561823e-7",
            "extra": "mean: 1.5094477155787063 usec\nrounds: 120686"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 524670.8799359626,
            "unit": "iter/sec",
            "range": "stddev: 5.368464568316572e-7",
            "extra": "mean: 1.905956740198832 usec\nrounds: 110657"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 662041.9664224652,
            "unit": "iter/sec",
            "range": "stddev: 4.476200252220187e-7",
            "extra": "mean: 1.5104782637931378 usec\nrounds: 133441"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 814018.4430710827,
            "unit": "iter/sec",
            "range": "stddev: 3.693753898912215e-7",
            "extra": "mean: 1.2284733945673965 usec\nrounds: 174795"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267482.4987710657,
            "unit": "iter/sec",
            "range": "stddev: 7.976227082733584e-7",
            "extra": "mean: 3.738562353030376 usec\nrounds: 54873"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7394253.900895306,
            "unit": "iter/sec",
            "range": "stddev: 1.2940556618801884e-8",
            "extra": "mean: 135.2401490945447 nsec\nrounds: 74047"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8972939.087496828,
            "unit": "iter/sec",
            "range": "stddev: 1.2268996574251781e-8",
            "extra": "mean: 111.44620399724222 nsec\nrounds: 89207"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1497029.0892877034,
            "unit": "iter/sec",
            "range": "stddev: 3.3722914742172345e-7",
            "extra": "mean: 667.9896918207561 nsec\nrounds: 149881"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "69dc72cabd66420d7316d7d0aa1d0b0e2d413275",
          "message": "fix: 노트북 전수조사 — c.insights 제거 + corpName→종목명 + 독스트링 정비\n\n- 05_analysis.py/ipynb: c.insights → c.analysis(\"financial\", \"종합평가\")\n- 05_analysis.ipynb: dartlab.insights() → dartlab.analysis() 루트 호출\n- marketScan.py: corpName → 종목명 (scan 일관성 반영)\n- 05_analysis.py 독스트링: 2단계 호출 패턴으로 통일",
          "timestamp": "2026-04-03T02:07:36+09:00",
          "tree_id": "fa0079274856709617eba4bd73b042dd8b23572a",
          "url": "https://github.com/eddmpython/dartlab/commit/69dc72cabd66420d7316d7d0aa1d0b0e2d413275"
        },
        "date": 1775149711268,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 531701.962013206,
            "unit": "iter/sec",
            "range": "stddev: 4.794388558962309e-7",
            "extra": "mean: 1.880752886849725 usec\nrounds: 76900"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 659746.8854667832,
            "unit": "iter/sec",
            "range": "stddev: 4.5493642908722696e-7",
            "extra": "mean: 1.5157328090946296 usec\nrounds: 146371"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520476.6691066613,
            "unit": "iter/sec",
            "range": "stddev: 6.844466071409608e-7",
            "extra": "mean: 1.9213157079958758 usec\nrounds: 133085"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675490.1866353184,
            "unit": "iter/sec",
            "range": "stddev: 5.083952099296674e-7",
            "extra": "mean: 1.4804064067623188 usec\nrounds: 189394"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 893670.1899496666,
            "unit": "iter/sec",
            "range": "stddev: 1.5281278559282753e-7",
            "extra": "mean: 1.118981041603639 usec\nrounds: 179857"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266232.3972542607,
            "unit": "iter/sec",
            "range": "stddev: 7.937013557644989e-7",
            "extra": "mean: 3.7561168750058878 usec\nrounds: 76723"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7269651.83037303,
            "unit": "iter/sec",
            "range": "stddev: 1.5097101311652606e-8",
            "extra": "mean: 137.55816968041597 nsec\nrounds: 74823"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8684936.07760524,
            "unit": "iter/sec",
            "range": "stddev: 1.0461344314358109e-8",
            "extra": "mean: 115.14189523842035 nsec\nrounds: 87551"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1448620.5263062923,
            "unit": "iter/sec",
            "range": "stddev: 2.881003353820918e-7",
            "extra": "mean: 690.3119083572634 nsec\nrounds: 161525"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "b4b9fa32598ef930eeef3a48841b8ab5159e3245",
          "message": "fix: 노트북 잔존 insights/corpName 3건 추가 수정 (README, marketScan, STATUS)",
          "timestamp": "2026-04-03T02:11:59+09:00",
          "tree_id": "c161918750475210c7cdb54e57ffba26c44de3a4",
          "url": "https://github.com/eddmpython/dartlab/commit/b4b9fa32598ef930eeef3a48841b8ab5159e3245"
        },
        "date": 1775149976978,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 543960.7189055172,
            "unit": "iter/sec",
            "range": "stddev: 4.6242410012170315e-7",
            "extra": "mean: 1.8383680388026218 usec\nrounds: 87018"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 660136.0375240397,
            "unit": "iter/sec",
            "range": "stddev: 4.586844020329221e-7",
            "extra": "mean: 1.514839280325737 usec\nrounds: 175747"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 532733.0196519266,
            "unit": "iter/sec",
            "range": "stddev: 5.15888529097773e-7",
            "extra": "mean: 1.8771128559918682 usec\nrounds: 140985"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 663301.5443548114,
            "unit": "iter/sec",
            "range": "stddev: 4.302219030266849e-7",
            "extra": "mean: 1.5076099377586898 usec\nrounds: 187970"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 882489.936813258,
            "unit": "iter/sec",
            "range": "stddev: 1.6990840410682223e-7",
            "extra": "mean: 1.1331573973648699 usec\nrounds: 190115"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267876.02789663075,
            "unit": "iter/sec",
            "range": "stddev: 8.212958789576489e-7",
            "extra": "mean: 3.733070136406102 usec\nrounds: 78162"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7257934.677378977,
            "unit": "iter/sec",
            "range": "stddev: 1.5976558568477083e-8",
            "extra": "mean: 137.7802425139937 nsec\nrounds: 73068"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8703337.118664902,
            "unit": "iter/sec",
            "range": "stddev: 1.738866379408975e-8",
            "extra": "mean: 114.89845634675365 nsec\nrounds: 89191"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1461915.7663351921,
            "unit": "iter/sec",
            "range": "stddev: 3.011521653564712e-7",
            "extra": "mean: 684.0339389093893 nsec\nrounds: 195351"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "5caa941460d0541c73ddebe33510b0eaea4c7ce6",
          "message": "feat(vscode): OAuth 즉시 로그인 + 에러 메시지 CLI 안내 제거\n\n- OAuth provider 선택 시 바로 브라우저 로그인 시작 (callback 서버 + PKCE)\n- _sanitizeErrorForUi: dartlab.setup(...) 문구 제거, switchProvider 플래그\n- oauthStart/oauthResult 이벤트 체인 (stdio → stdioProxy → webview)\n- setProvider에서 auth_kind별 분기: api_key → InputBox, oauth → 브라우저",
          "timestamp": "2026-04-03T02:26:33+09:00",
          "tree_id": "24b8e5c13e1e789e9b62cd941a4142ced652ccd3",
          "url": "https://github.com/eddmpython/dartlab/commit/5caa941460d0541c73ddebe33510b0eaea4c7ce6"
        },
        "date": 1775150851759,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 541071.1596313517,
            "unit": "iter/sec",
            "range": "stddev: 4.836917202394619e-7",
            "extra": "mean: 1.8481857371243562 usec\nrounds: 55024"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 516480.81107490044,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010259915054230256",
            "extra": "mean: 1.9361803547334098 usec\nrounds: 118400"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 520025.38005997543,
            "unit": "iter/sec",
            "range": "stddev: 6.551057462662132e-7",
            "extra": "mean: 1.922983066489309 usec\nrounds: 97381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675770.543911553,
            "unit": "iter/sec",
            "range": "stddev: 3.822268664885459e-7",
            "extra": "mean: 1.4797922297881088 usec\nrounds: 138812"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 899204.9230119506,
            "unit": "iter/sec",
            "range": "stddev: 1.526919837974885e-7",
            "extra": "mean: 1.1120935555495284 usec\nrounds: 177905"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266493.3029830237,
            "unit": "iter/sec",
            "range": "stddev: 7.079681922079018e-7",
            "extra": "mean: 3.752439512762175 usec\nrounds: 62228"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7322487.446153167,
            "unit": "iter/sec",
            "range": "stddev: 1.3286239922772321e-8",
            "extra": "mean: 136.565614806939 nsec\nrounds: 73828"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8757037.355042059,
            "unit": "iter/sec",
            "range": "stddev: 1.0468943927050096e-8",
            "extra": "mean: 114.1938716778715 nsec\nrounds: 88574"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1460695.3125185738,
            "unit": "iter/sec",
            "range": "stddev: 2.483418439386114e-7",
            "extra": "mean: 684.6054693471772 nsec\nrounds: 179180"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "00e0224b6c8e0466e17a890fbf611ef412096015",
          "message": "fix(vscode): 무료 표현 제거 + 연결 완료 안내 메시지\n\n- provider 목록에서 (무료) 표현 전부 제거\n- OAuth/API키 연결 완료 시 \"연결 완료\" 메시지 표시\n- freeTier → description 표시로 변경",
          "timestamp": "2026-04-03T02:33:16+09:00",
          "tree_id": "a7cf661e560da4fbcf60e815f5795ecee991b78e",
          "url": "https://github.com/eddmpython/dartlab/commit/00e0224b6c8e0466e17a890fbf611ef412096015"
        },
        "date": 1775151249005,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 546952.2659181923,
            "unit": "iter/sec",
            "range": "stddev: 4.6394606418982473e-7",
            "extra": "mean: 1.82831311306711 usec\nrounds: 39235"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 657821.1302438137,
            "unit": "iter/sec",
            "range": "stddev: 4.878085061580365e-7",
            "extra": "mean: 1.5201700797135562 usec\nrounds: 95420"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 526155.4103020101,
            "unit": "iter/sec",
            "range": "stddev: 5.803782202218434e-7",
            "extra": "mean: 1.9005791452871421 usec\nrounds: 96247"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 671698.5492583462,
            "unit": "iter/sec",
            "range": "stddev: 3.8004603597992943e-7",
            "extra": "mean: 1.4887630784734414 usec\nrounds: 132909"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 788853.4232376267,
            "unit": "iter/sec",
            "range": "stddev: 4.083669091051323e-7",
            "extra": "mean: 1.2676626234260118 usec\nrounds: 175101"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267027.25887198676,
            "unit": "iter/sec",
            "range": "stddev: 6.800436853981223e-7",
            "extra": "mean: 3.7449360197319828 usec\nrounds: 57627"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7028419.972868128,
            "unit": "iter/sec",
            "range": "stddev: 2.3145503285484998e-8",
            "extra": "mean: 142.27948868455624 nsec\nrounds: 199641"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8644234.171383763,
            "unit": "iter/sec",
            "range": "stddev: 1.1578963123603019e-8",
            "extra": "mean: 115.684047906805 nsec\nrounds: 50641"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1478698.1341788648,
            "unit": "iter/sec",
            "range": "stddev: 3.033554363844952e-7",
            "extra": "mean: 676.2705496719312 nsec\nrounds: 135428"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "16b2e142d948456640d5a4eae1dd150f9fb14163",
          "message": "feat: credit 보고서를 블로그 카테고리로 이관 + 렌더링 버그 수정\n\n- publisher.py: 출력 경로 docs/credit/reports/ → blog/04-credit-reports/\n- 블로그 frontmatter 자동 생성, _registry.json으로 번호/slug 관리\n- HTML 엔티티 버그 수정 (차입금 < 현금 → 현금이 차입금 초과)\n- None 점수 표현 개선 (-점/100 → 평가 불가)\n- posts.ts에 credit-reports 카테고리 추가\n- 네비게이션/헤더/sitemap 링크를 블로그 카테고리로 변경\n- governance _scanView 컬럼명 호환 수정 (종목코드/stockCode)\n- 4개 보고서(삼성전자/SK하이닉스/NAVER/LG) 블로그 포스트로 재생성",
          "timestamp": "2026-04-03T02:40:35+09:00",
          "tree_id": "970ddcb692a97f04549c821fb488d7c5edad1b93",
          "url": "https://github.com/eddmpython/dartlab/commit/16b2e142d948456640d5a4eae1dd150f9fb14163"
        },
        "date": 1775151700856,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 538256.5176311804,
            "unit": "iter/sec",
            "range": "stddev: 5.359130707846552e-7",
            "extra": "mean: 1.8578502391404605 usec\nrounds: 52477"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 663147.545965414,
            "unit": "iter/sec",
            "range": "stddev: 4.6111300414767974e-7",
            "extra": "mean: 1.507960040090617 usec\nrounds: 142593"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527307.7128056132,
            "unit": "iter/sec",
            "range": "stddev: 5.078531284344251e-7",
            "extra": "mean: 1.896425892728484 usec\nrounds: 119833"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 679657.7745963396,
            "unit": "iter/sec",
            "range": "stddev: 4.398030328182947e-7",
            "extra": "mean: 1.4713287147990284 usec\nrounds: 148965"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 819214.1550384243,
            "unit": "iter/sec",
            "range": "stddev: 3.899341405626314e-7",
            "extra": "mean: 1.2206820327135293 usec\nrounds: 194932"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269939.73882303206,
            "unit": "iter/sec",
            "range": "stddev: 6.542007260205341e-7",
            "extra": "mean: 3.704530516181551 usec\nrounds: 72224"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7349731.4670312265,
            "unit": "iter/sec",
            "range": "stddev: 1.2317200877409674e-8",
            "extra": "mean: 136.0593927119258 nsec\nrounds: 73606"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8915330.284544565,
            "unit": "iter/sec",
            "range": "stddev: 1.1210519029689047e-8",
            "extra": "mean: 112.16634359958373 nsec\nrounds: 88021"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1460636.0442934134,
            "unit": "iter/sec",
            "range": "stddev: 2.729707851491765e-7",
            "extra": "mean: 684.6332485816155 nsec\nrounds: 159694"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "eb3636b319235b3fd0fe05e598ce4f8a6aa92d88",
          "message": "fix(vscode): provider 인증 에러 무시 방지 + 에러 표시\n\n- except Exception: pass → ImportError만 무시, 나머지는 에러 emit\n- provider 확인 실패 시 사용자에게 에러 메시지 표시",
          "timestamp": "2026-04-03T02:44:32+09:00",
          "tree_id": "e8c262a5c8cad62e884a0cc16ce2b0a557493b0a",
          "url": "https://github.com/eddmpython/dartlab/commit/eb3636b319235b3fd0fe05e598ce4f8a6aa92d88"
        },
        "date": 1775151932576,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 538613.64309865,
            "unit": "iter/sec",
            "range": "stddev: 5.468045165067019e-7",
            "extra": "mean: 1.8566183995024512 usec\nrounds: 53121"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 653457.5168703751,
            "unit": "iter/sec",
            "range": "stddev: 0.000001792872975928843",
            "extra": "mean: 1.5303213662447894 usec\nrounds: 141583"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 521970.23337071546,
            "unit": "iter/sec",
            "range": "stddev: 5.057560421929693e-7",
            "extra": "mean: 1.915818060241333 usec\nrounds: 117440"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 686965.9601782188,
            "unit": "iter/sec",
            "range": "stddev: 4.0357759200305696e-7",
            "extra": "mean: 1.4556762022685537 usec\nrounds: 155208"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 807320.248074634,
            "unit": "iter/sec",
            "range": "stddev: 3.706612272793135e-7",
            "extra": "mean: 1.2386658236119867 usec\nrounds: 189394"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271902.37469864276,
            "unit": "iter/sec",
            "range": "stddev: 6.7491249722769e-7",
            "extra": "mean: 3.6777906081487104 usec\nrounds: 64396"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7446781.954981742,
            "unit": "iter/sec",
            "range": "stddev: 1.2702266418668183e-8",
            "extra": "mean: 134.28619315636342 nsec\nrounds: 73557"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8996826.563531155,
            "unit": "iter/sec",
            "range": "stddev: 1.1993445464912029e-8",
            "extra": "mean: 111.15030315839623 nsec\nrounds: 77979"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1456339.3719414824,
            "unit": "iter/sec",
            "range": "stddev: 2.808902215732851e-7",
            "extra": "mean: 686.6531381808863 nsec\nrounds: 153799"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "4106fc064800f91b809fabc9f346d9a8251fc620",
          "message": "feat: 데이터 품질 감사 — 마진 괴리 플래그 + 프롬프트 #31\n\n엔진:\n- profitabilityFlags에 마진 괴리 감지 추가 (순이익률 > 2× 영업이익률 → 비영업이익 경고)\n- 영업이익률 > 100% 이상치 감지\n\n프롬프트 #31:\n- 데이터 품질 점검 섹션 추가 (분석 전 필수)\n- analysis 결과 구조 안내 (marginTrend vs returnTrend vs ROIC 분리)\n- \"marginTrend에서 ROE를 찾지 마라 — returnTrend를 써라\"\n\n검증: 삼성전자 2022Q4 순이익률 33.8% vs 영업이익률 6.1% → 플래그 정상 작동\n데이터 확인: 연간 합산 302조/55.6조 → 공시와 일치, Q4 비영업이익 19.5조는 실제 현상",
          "timestamp": "2026-04-03T02:46:04+09:00",
          "tree_id": "1c0709259a72c7fc6dace7d4151d55635f253afe",
          "url": "https://github.com/eddmpython/dartlab/commit/4106fc064800f91b809fabc9f346d9a8251fc620"
        },
        "date": 1775152035596,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 529108.9099770932,
            "unit": "iter/sec",
            "range": "stddev: 4.886168862063219e-7",
            "extra": "mean: 1.889970063145021 usec\nrounds: 51241"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 663353.4284717871,
            "unit": "iter/sec",
            "range": "stddev: 4.805046510780596e-7",
            "extra": "mean: 1.5074920202097528 usec\nrounds: 112284"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 524109.8383054983,
            "unit": "iter/sec",
            "range": "stddev: 5.545298608984484e-7",
            "extra": "mean: 1.9079970016077243 usec\nrounds: 116064"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 676331.4530709723,
            "unit": "iter/sec",
            "range": "stddev: 4.2330723711878555e-7",
            "extra": "mean: 1.4785649779547705 usec\nrounds: 174490"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 901375.6633275838,
            "unit": "iter/sec",
            "range": "stddev: 1.712107053214916e-7",
            "extra": "mean: 1.1094153533148734 usec\nrounds: 174490"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270398.21020700736,
            "unit": "iter/sec",
            "range": "stddev: 6.898163455606884e-7",
            "extra": "mean: 3.6982493309938524 usec\nrounds: 66899"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7245923.904518515,
            "unit": "iter/sec",
            "range": "stddev: 1.2103441290217247e-8",
            "extra": "mean: 138.0086257014659 nsec\nrounds: 72015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8806375.039660566,
            "unit": "iter/sec",
            "range": "stddev: 1.122824713339856e-8",
            "extra": "mean: 113.55410092079659 nsec\nrounds: 89119"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1462250.3738798413,
            "unit": "iter/sec",
            "range": "stddev: 2.554247135261325e-7",
            "extra": "mean: 683.8774110528446 nsec\nrounds: 157184"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "5fc8adb3c8de3ce722fdba554f65f2852a4b4d72",
          "message": "fix: 전체에서 무료 표현 제거\n\n- providers.py label/description/freeTierHint에서 무료 제거\n- setup.py CLI 안내에서 무료 제거\n- stdio.py status API에서 freeTier 필드 제거\n- extension.ts 시작 메시지에서 무료 제거\n- vscode README에서 무료 제거\n- ChatHeader에서 freeTier → description",
          "timestamp": "2026-04-03T02:50:55+09:00",
          "tree_id": "e5eca88980fffe7578c0531b6d6a46cb3229f894",
          "url": "https://github.com/eddmpython/dartlab/commit/5fc8adb3c8de3ce722fdba554f65f2852a4b4d72"
        },
        "date": 1775152333220,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 527214.6471414393,
            "unit": "iter/sec",
            "range": "stddev: 5.306658814038476e-7",
            "extra": "mean: 1.8967606560667567 usec\nrounds: 55485"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 656609.540841318,
            "unit": "iter/sec",
            "range": "stddev: 4.841870339893371e-7",
            "extra": "mean: 1.5229751287480435 usec\nrounds: 120541"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 525192.7821594536,
            "unit": "iter/sec",
            "range": "stddev: 5.767308980188392e-7",
            "extra": "mean: 1.9040627250973727 usec\nrounds: 105508"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 673848.5191340799,
            "unit": "iter/sec",
            "range": "stddev: 5.714100868688262e-7",
            "extra": "mean: 1.484013055760717 usec\nrounds: 143001"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 805039.7964333991,
            "unit": "iter/sec",
            "range": "stddev: 3.6415847847575753e-7",
            "extra": "mean: 1.2421746160007754 usec\nrounds: 184502"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267964.89787848265,
            "unit": "iter/sec",
            "range": "stddev: 6.756914832085457e-7",
            "extra": "mean: 3.731832071727105 usec\nrounds: 68696"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7519857.92451786,
            "unit": "iter/sec",
            "range": "stddev: 1.2871933697227315e-8",
            "extra": "mean: 132.98123582090358 nsec\nrounds: 73878"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8600599.197044859,
            "unit": "iter/sec",
            "range": "stddev: 2.6455221414333566e-8",
            "extra": "mean: 116.27096869525059 nsec\nrounds: 88645"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1403481.531401327,
            "unit": "iter/sec",
            "range": "stddev: 3.8065210838226e-7",
            "extra": "mean: 712.5138290929523 nsec\nrounds: 169751"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "0b9158ebf072d307ab3094ea510aacc9088f9af8",
          "message": "fix(vscode): setProvider 테스트 수정 + CHANGELOG 0.1.8 작성\n\n- setProvider 테스트: needCredential 응답도 허용\n- CHANGELOG: v0.1.0 이후 전체 변경사항 기록",
          "timestamp": "2026-04-03T02:55:08+09:00",
          "tree_id": "549e10253034e5f65130ddcb0c3b6d8ecd4167cd",
          "url": "https://github.com/eddmpython/dartlab/commit/0b9158ebf072d307ab3094ea510aacc9088f9af8"
        },
        "date": 1775152599137,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 536008.9175138279,
            "unit": "iter/sec",
            "range": "stddev: 4.838962418151484e-7",
            "extra": "mean: 1.865640602843519 usec\nrounds: 50031"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 653299.0365982256,
            "unit": "iter/sec",
            "range": "stddev: 4.4995267509576363e-7",
            "extra": "mean: 1.5306925986100806 usec\nrounds: 127976"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 529418.0868699994,
            "unit": "iter/sec",
            "range": "stddev: 5.618813576137729e-7",
            "extra": "mean: 1.8888663323010983 usec\nrounds: 122625"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 666870.8984815081,
            "unit": "iter/sec",
            "range": "stddev: 3.9381035434093014e-7",
            "extra": "mean: 1.4995406191468847 usec\nrounds: 180506"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 801647.1157932375,
            "unit": "iter/sec",
            "range": "stddev: 3.5690972863885613e-7",
            "extra": "mean: 1.2474316694952372 usec\nrounds: 194591"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 265009.09912248555,
            "unit": "iter/sec",
            "range": "stddev: 6.471267363857422e-7",
            "extra": "mean: 3.773455339123304 usec\nrounds: 25772"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7268423.407879475,
            "unit": "iter/sec",
            "range": "stddev: 1.5505473022627493e-8",
            "extra": "mean: 137.58141812651292 nsec\nrounds: 74267"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8180757.329472631,
            "unit": "iter/sec",
            "range": "stddev: 3.5185698699245164e-8",
            "extra": "mean: 122.23807157771597 nsec\nrounds: 197239"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1463104.5390811902,
            "unit": "iter/sec",
            "range": "stddev: 2.93658826449632e-7",
            "extra": "mean: 683.4781611900311 nsec\nrounds: 165783"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "57fb910cede49a311feae22fec80710ab52764ec",
          "message": "release: v0.8.5 — VSCode 프로바이더 연결 플로우 + OAuth 로그인\n\n- provider 선택 시 바로 연결 (API키 InputBox, OAuth 브라우저 로그인)\n- stdio needCredential/oauthStart 프로토콜\n- 에러 메시지 CLI 안내 제거, 무료 표현 제거\n- fixture integration 테스트 62개",
          "timestamp": "2026-04-03T03:07:01+09:00",
          "tree_id": "8205c4ccc6b814575c8cf1d53fd0c8d393224a0e",
          "url": "https://github.com/eddmpython/dartlab/commit/57fb910cede49a311feae22fec80710ab52764ec"
        },
        "date": 1775153276101,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 583585.7531445358,
            "unit": "iter/sec",
            "range": "stddev: 3.0998969731313347e-7",
            "extra": "mean: 1.7135442299811106 usec\nrounds: 55381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 711889.4599132551,
            "unit": "iter/sec",
            "range": "stddev: 3.093706131621979e-7",
            "extra": "mean: 1.4047124677500515 usec\nrounds: 127617"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 581694.8839186901,
            "unit": "iter/sec",
            "range": "stddev: 3.899937765064758e-7",
            "extra": "mean: 1.7191143117218493 usec\nrounds: 119804"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 776650.5355709648,
            "unit": "iter/sec",
            "range": "stddev: 2.429567367358911e-7",
            "extra": "mean: 1.2875803906641703 usec\nrounds: 151081"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 907931.7393927574,
            "unit": "iter/sec",
            "range": "stddev: 2.392731103812327e-7",
            "extra": "mean: 1.1014043860486908 usec\nrounds: 181621"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 300759.13636093814,
            "unit": "iter/sec",
            "range": "stddev: 4.083579295163995e-7",
            "extra": "mean: 3.324919775005304 usec\nrounds: 69517"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8509733.298633171,
            "unit": "iter/sec",
            "range": "stddev: 1.1701830459323355e-8",
            "extra": "mean: 117.51249597453536 nsec\nrounds: 83230"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9887689.580622643,
            "unit": "iter/sec",
            "range": "stddev: 8.214744272380074e-9",
            "extra": "mean: 101.13586109739383 nsec\nrounds: 97248"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1516232.9551368442,
            "unit": "iter/sec",
            "range": "stddev: 1.6975745008610592e-7",
            "extra": "mean: 659.5292607327265 nsec\nrounds: 167477"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "e3d03ce49dc783bf1572e411601606b6059f7a77",
          "message": "style: ruff format",
          "timestamp": "2026-04-03T03:16:38+09:00",
          "tree_id": "0cbad7cc12cbacb5407953449cdbc41638e4b502",
          "url": "https://github.com/eddmpython/dartlab/commit/e3d03ce49dc783bf1572e411601606b6059f7a77"
        },
        "date": 1775153854484,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 539149.5699364336,
            "unit": "iter/sec",
            "range": "stddev: 5.569398689520487e-7",
            "extra": "mean: 1.8547728789209668 usec\nrounds: 48833"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 647238.6095457472,
            "unit": "iter/sec",
            "range": "stddev: 6.696179769722283e-7",
            "extra": "mean: 1.5450252584619946 usec\nrounds: 112398"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 532777.4309724559,
            "unit": "iter/sec",
            "range": "stddev: 5.52156794668735e-7",
            "extra": "mean: 1.8769563834090022 usec\nrounds: 109087"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 672829.8523234829,
            "unit": "iter/sec",
            "range": "stddev: 4.5178793837559567e-7",
            "extra": "mean: 1.4862598568519227 usec\nrounds: 154512"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 807696.1433720879,
            "unit": "iter/sec",
            "range": "stddev: 4.50940997877726e-7",
            "extra": "mean: 1.2380893584870345 usec\nrounds: 168322"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268343.5255751392,
            "unit": "iter/sec",
            "range": "stddev: 8.333326843468269e-7",
            "extra": "mean: 3.7265665264578507 usec\nrounds: 62306"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7416215.704793104,
            "unit": "iter/sec",
            "range": "stddev: 1.2831304566597086e-8",
            "extra": "mean: 134.8396594443308 nsec\nrounds: 73938"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8767858.744084287,
            "unit": "iter/sec",
            "range": "stddev: 1.1922947366763964e-8",
            "extra": "mean: 114.05293232794203 nsec\nrounds: 76782"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453855.3008088376,
            "unit": "iter/sec",
            "range": "stddev: 2.835835797314925e-7",
            "extra": "mean: 687.8263603287481 nsec\nrounds: 161265"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "a8e240928cfb20bc827e91d0a62b1e69a28fefc5",
          "message": "feat: 신용분석 보고서 명칭 변경 + AI 분석 보강 + 천단위 콤마\n\n- \"신용등급/신용평가 보고서\" → \"신용분석 보고서\" 전체 변경 (법적 안전)\n- publisher.py에 _generateAIAnalysis() 추가 — 등급 근거 섹션에 AI 종합 해석 삽입\n- AI provider 미설정 시 기존 기계적 서사로 graceful fallback\n- AI 출력에서 코드블록/print문 자동 제거 (mdsvex 호환)\n- narrative.py _fmtTril 천단위 콤마 추가 (1598억→1,598억)\n- 4개 보고서 재생성 (삼성전자/SK하이닉스/NAVER/LG)",
          "timestamp": "2026-04-03T03:35:00+09:00",
          "tree_id": "6b3369b145ab2f2f57600f8e34d5b17e58f0d1ee",
          "url": "https://github.com/eddmpython/dartlab/commit/a8e240928cfb20bc827e91d0a62b1e69a28fefc5"
        },
        "date": 1775154958146,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 493216.0246812771,
            "unit": "iter/sec",
            "range": "stddev: 9.823354379388822e-7",
            "extra": "mean: 2.027509143982525 usec\nrounds: 53150"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 668257.7491039244,
            "unit": "iter/sec",
            "range": "stddev: 5.560345197065678e-7",
            "extra": "mean: 1.4964285881322186 usec\nrounds: 119546"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 522657.16338393255,
            "unit": "iter/sec",
            "range": "stddev: 5.825591128596216e-7",
            "extra": "mean: 1.913300094320953 usec\nrounds: 103864"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 672524.158333778,
            "unit": "iter/sec",
            "range": "stddev: 4.505276507123756e-7",
            "extra": "mean: 1.4869354321450168 usec\nrounds: 138428"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 814533.9644360289,
            "unit": "iter/sec",
            "range": "stddev: 3.5469608771414154e-7",
            "extra": "mean: 1.2276958895046015 usec\nrounds: 147864"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266943.5385198307,
            "unit": "iter/sec",
            "range": "stddev: 6.893929904356383e-7",
            "extra": "mean: 3.7461105278849525 usec\nrounds: 55823"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7334034.926420462,
            "unit": "iter/sec",
            "range": "stddev: 1.2089529791587214e-8",
            "extra": "mean: 136.35059145921903 nsec\nrounds: 73175"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8647746.17797216,
            "unit": "iter/sec",
            "range": "stddev: 1.1342305263076467e-8",
            "extra": "mean: 115.63706651650284 nsec\nrounds: 86791"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1496866.7544196157,
            "unit": "iter/sec",
            "range": "stddev: 2.838641836972577e-7",
            "extra": "mean: 668.0621351549308 nsec\nrounds: 175408"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "b19dddce98f2fcda0c13c21a837ec98a3f65f945",
          "message": "feat: OAuth 수동 토큰 입력 (방화벽 환경용)\n\n- stdio oauthPasteToken 프로토콜: 토큰 JSON 받아서 저장\n- VSCode: OAuth 카드에 \"토큰 입력\" 버튼, InputBox로 토큰 붙여넣기\n- 다른 PC에서 발급한 토큰으로 방화벽 환경에서도 ChatGPT 사용 가능",
          "timestamp": "2026-04-03T08:20:41+09:00",
          "tree_id": "ee107e26904bd38b8f947939bc1019e34d6de0f9",
          "url": "https://github.com/eddmpython/dartlab/commit/b19dddce98f2fcda0c13c21a837ec98a3f65f945"
        },
        "date": 1775172098362,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 530341.3817569272,
            "unit": "iter/sec",
            "range": "stddev: 5.104266543822321e-7",
            "extra": "mean: 1.8855779209368442 usec\nrounds: 50455"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 621848.2318685653,
            "unit": "iter/sec",
            "range": "stddev: 6.421704637547027e-7",
            "extra": "mean: 1.608109420839137 usec\nrounds: 114247"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 508048.5335850049,
            "unit": "iter/sec",
            "range": "stddev: 6.473003401253765e-7",
            "extra": "mean: 1.968315886955874 usec\nrounds: 136036"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 668761.1117794553,
            "unit": "iter/sec",
            "range": "stddev: 3.9766713175757786e-7",
            "extra": "mean: 1.495302257242764 usec\nrounds: 149032"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 830272.6071488656,
            "unit": "iter/sec",
            "range": "stddev: 3.5481207282311807e-7",
            "extra": "mean: 1.2044236933625618 usec\nrounds: 196156"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 256370.60098224756,
            "unit": "iter/sec",
            "range": "stddev: 0.000001184595763590817",
            "extra": "mean: 3.9006032523567136 usec\nrounds: 72255"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 6819209.962169257,
            "unit": "iter/sec",
            "range": "stddev: 4.6950146749933465e-8",
            "extra": "mean: 146.64455348166024 nsec\nrounds: 197707"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8143516.244375473,
            "unit": "iter/sec",
            "range": "stddev: 1.3004440347500349e-8",
            "extra": "mean: 122.7970780669438 nsec\nrounds: 78010"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1481075.4086791393,
            "unit": "iter/sec",
            "range": "stddev: 2.4718932449261437e-7",
            "extra": "mean: 675.1850676474504 nsec\nrounds: 149032"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "db397fca98a36a83448e8ca45f3e402a26ab127d",
          "message": "docs: ops/vscode.md 신규 — VSCode 확장 운영문서 집약",
          "timestamp": "2026-04-03T09:08:10+09:00",
          "tree_id": "75038a9f0211246ea25dd383e8c1f6d0e8803b6f",
          "url": "https://github.com/eddmpython/dartlab/commit/db397fca98a36a83448e8ca45f3e402a26ab127d"
        },
        "date": 1775174952047,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 534697.1009403017,
            "unit": "iter/sec",
            "range": "stddev: 6.490879142620504e-7",
            "extra": "mean: 1.8702177330706136 usec\nrounds: 56234"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 649942.0703054202,
            "unit": "iter/sec",
            "range": "stddev: 4.709742254846129e-7",
            "extra": "mean: 1.5385986623855277 usec\nrounds: 129786"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 514860.27709507884,
            "unit": "iter/sec",
            "range": "stddev: 5.383077730036728e-7",
            "extra": "mean: 1.9422745247354376 usec\nrounds: 114456"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 661542.0428645252,
            "unit": "iter/sec",
            "range": "stddev: 4.2898257579432303e-7",
            "extra": "mean: 1.511619723623199 usec\nrounds: 172088"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 786342.3102411993,
            "unit": "iter/sec",
            "range": "stddev: 3.9024863054142806e-7",
            "extra": "mean: 1.2717107892786084 usec\nrounds: 147211"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267234.3062597206,
            "unit": "iter/sec",
            "range": "stddev: 8.193564068148218e-7",
            "extra": "mean: 3.7420345239211787 usec\nrounds: 69459"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7478780.312449675,
            "unit": "iter/sec",
            "range": "stddev: 1.1885335765056512e-8",
            "extra": "mean: 133.71164257029096 nsec\nrounds: 71449"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9175776.379113264,
            "unit": "iter/sec",
            "range": "stddev: 1.3800668960088242e-8",
            "extra": "mean: 108.98260361665861 nsec\nrounds: 89199"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1378622.1192117152,
            "unit": "iter/sec",
            "range": "stddev: 2.5657678863715987e-7",
            "extra": "mean: 725.361929178818 nsec\nrounds: 162576"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "c95d4e69332e2acb517626c28385641a7fbdd486",
          "message": "fix: Daily Data Sync 타임아웃 근본 해결 — job 분할 + docs 직접 수집\n\n근본 원인: syncRecent.py가 88개 종목의 docs를 수집할 때\nbatchCollect._collectDocs가 종목마다 2016년부터 전체 공시를\n재조회한 후 새 것만 필터. 이미 발견한 rcept_no를 버리고\n재발견하는 구조 → 90분 타임아웃 초과.\n\n변경:\n- dataSyncDaily.yml: 단일 job → 병렬 2 job (sync-data 45분, sync-docs 150분)\n- concurrency group 추가 (중복 실행 방지)\n- syncRecent.py: SYNC_CATEGORIES 환경변수로 카테고리 분리 실행\n- docs 전용 모드: _collectDocsDirect() — listing API 재조회 없이\n  이미 발견한 rcept_no의 ZIP만 직접 다운로드\n- 건당 120초 타임아웃으로 한 종목이 전체를 블록하지 않음\n- dataSync.yml에도 concurrency 추가\n\nCloses #12",
          "timestamp": "2026-04-03T09:52:24+09:00",
          "tree_id": "3d6a8d64dd551ede8ec67f59dfd03ed5ba466c9c",
          "url": "https://github.com/eddmpython/dartlab/commit/c95d4e69332e2acb517626c28385641a7fbdd486"
        },
        "date": 1775177634797,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 527329.9909194638,
            "unit": "iter/sec",
            "range": "stddev: 4.957407912122807e-7",
            "extra": "mean: 1.8963457744104004 usec\nrounds: 47638"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 635225.2332718166,
            "unit": "iter/sec",
            "range": "stddev: 4.441755282602219e-7",
            "extra": "mean: 1.5742447680318994 usec\nrounds: 109614"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 516581.2071042187,
            "unit": "iter/sec",
            "range": "stddev: 5.006157289498949e-7",
            "extra": "mean: 1.9358040638095706 usec\nrounds: 125597"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 654106.3919415904,
            "unit": "iter/sec",
            "range": "stddev: 3.860627513440467e-7",
            "extra": "mean: 1.52880328386899 usec\nrounds: 158228"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 796591.6717645577,
            "unit": "iter/sec",
            "range": "stddev: 3.400415297380952e-7",
            "extra": "mean: 1.255348298815208 usec\nrounds: 186986"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 250545.7804766831,
            "unit": "iter/sec",
            "range": "stddev: 6.353538589702605e-7",
            "extra": "mean: 3.991286534929549 usec\nrounds: 68065"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7219157.458590785,
            "unit": "iter/sec",
            "range": "stddev: 1.3428380606202323e-8",
            "extra": "mean: 138.52031982070176 nsec\nrounds: 69195"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8714733.769408392,
            "unit": "iter/sec",
            "range": "stddev: 1.6505488155270312e-8",
            "extra": "mean: 114.74819844873885 nsec\nrounds: 80464"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1467775.6722829584,
            "unit": "iter/sec",
            "range": "stddev: 2.635643763920657e-7",
            "extra": "mean: 681.303021220275 nsec\nrounds: 170097"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "e5afa97d45b93168234d791a3c29d761a32a105d",
          "message": "feat: OAuth 코드 수동 입력 + auth URL 화면 표시\n\n- 방화벽 환경: 로그인 후 브라우저 주소창 URL 복사 → 붙여넣기로 인증\n- oauthStart에 verifier/state/authUrl 포함, extension host가 보관\n- oauthPasteCode 프로토콜: code + verifier로 토큰 교환\n- 채팅에 auth URL 링크 표시 (브라우저 미오픈 시 직접 클릭)",
          "timestamp": "2026-04-03T09:54:01+09:00",
          "tree_id": "595f1f2d90c624e7fc17cf9e64f7e71cf4deb50a",
          "url": "https://github.com/eddmpython/dartlab/commit/e5afa97d45b93168234d791a3c29d761a32a105d"
        },
        "date": 1775177700032,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 581374.7514217285,
            "unit": "iter/sec",
            "range": "stddev: 3.399133208555893e-7",
            "extra": "mean: 1.720060937552827 usec\nrounds: 49641"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 707371.3265907703,
            "unit": "iter/sec",
            "range": "stddev: 3.0481252176637786e-7",
            "extra": "mean: 1.4136846694360312 usec\nrounds: 130073"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 575490.5197779965,
            "unit": "iter/sec",
            "range": "stddev: 7.33475594420881e-7",
            "extra": "mean: 1.737648085646596 usec\nrounds: 102596"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 756461.4435328955,
            "unit": "iter/sec",
            "range": "stddev: 2.3242308071136563e-7",
            "extra": "mean: 1.3219444408557142 usec\nrounds: 139257"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 987198.2119237095,
            "unit": "iter/sec",
            "range": "stddev: 1.179188131321973e-7",
            "extra": "mean: 1.0129677990920833 usec\nrounds: 191535"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 277415.63240254985,
            "unit": "iter/sec",
            "range": "stddev: 8.941418915686093e-7",
            "extra": "mean: 3.604699530951193 usec\nrounds: 72480"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8508723.725596141,
            "unit": "iter/sec",
            "range": "stddev: 1.1498710053079422e-8",
            "extra": "mean: 117.52643901126753 nsec\nrounds: 81834"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9869337.183494234,
            "unit": "iter/sec",
            "range": "stddev: 7.795472088025487e-9",
            "extra": "mean: 101.32392696770243 nsec\nrounds: 83935"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1539583.8591078522,
            "unit": "iter/sec",
            "range": "stddev: 1.423030295197867e-7",
            "extra": "mean: 649.5261651934136 nsec\nrounds: 154155"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "88ca7ae7c8acdb178fb29117a7cf7e50d7d5151b",
          "message": "fix: API 한도 초과 시 키 로테이션 + graceful exit\n\n- _discoverNewFilings: 여러 키 순서대로 시도, 전부 020이면 빈 결과 반환\n- 한도 초과 시 crash 대신 \"수집 불가, 다음 실행까지 대기\" 출력 후 정상 종료\n- changed_*.txt 빈 파일 생성 → 후속 upload step 안전 skip",
          "timestamp": "2026-04-03T09:56:05+09:00",
          "tree_id": "64d21d718b86ebe9130ca103779baad9b0b6d989",
          "url": "https://github.com/eddmpython/dartlab/commit/88ca7ae7c8acdb178fb29117a7cf7e50d7d5151b"
        },
        "date": 1775177826204,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 529660.6907306269,
            "unit": "iter/sec",
            "range": "stddev: 4.951005376688972e-7",
            "extra": "mean: 1.8880011628210045 usec\nrounds: 53320"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 643101.2652215032,
            "unit": "iter/sec",
            "range": "stddev: 4.4561140344001804e-7",
            "extra": "mean: 1.5549650639476977 usec\nrounds: 127633"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 523932.61149639933,
            "unit": "iter/sec",
            "range": "stddev: 5.229802291789697e-7",
            "extra": "mean: 1.9086424056405054 usec\nrounds: 114065"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 676005.8542875608,
            "unit": "iter/sec",
            "range": "stddev: 3.8198798655202873e-7",
            "extra": "mean: 1.4792771300093177 usec\nrounds: 139025"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 800641.6029784369,
            "unit": "iter/sec",
            "range": "stddev: 4.0855968114934505e-7",
            "extra": "mean: 1.2489982987143529 usec\nrounds: 160463"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267860.99715738994,
            "unit": "iter/sec",
            "range": "stddev: 6.466929194714988e-7",
            "extra": "mean: 3.7332796137259927 usec\nrounds: 69267"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7409305.4733662605,
            "unit": "iter/sec",
            "range": "stddev: 1.1266194170315216e-8",
            "extra": "mean: 134.96541660951 nsec\nrounds: 73234"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8987243.220392257,
            "unit": "iter/sec",
            "range": "stddev: 1.0234313346854825e-8",
            "extra": "mean: 111.26882576527778 nsec\nrounds: 88645"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1443548.341442392,
            "unit": "iter/sec",
            "range": "stddev: 2.590216238164405e-7",
            "extra": "mean: 692.7374520764585 nsec\nrounds: 175408"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "97847d1c07d44ccccfb6c7ae80487659c64f79ce",
          "message": "feat: HF→로컬 자동 동기화 개선 + 문서 현행화\n\nTTL 체계 단축:\n- DART ETag TTL 72h → 24h (CI가 매일 HF 업데이트하므로)\n- L2 폴백 TTL 90일 → 30일\n- collect 수집 데이터도 7일 후 HF 최신본 확인 (etag 없는 파일)\n- 네트워크 오류 시 etag touch로 재시도 쓰로틀링\n\n파이프라인 안정화:\n- syncRecent.py 세마포어 6→4 (API 한도 소진 속도 조절)\n\n문서 동기화:\n- ops/data.md: dataSyncDaily 2 병렬 job, concurrency, 키 로테이션,\n  3-Layer Freshness TTL 값 갱신, refresh 파라미터 문서화\n- quickstart.md: Data freshness 섹션 추가 (자동 갱신, 오프라인 모드)",
          "timestamp": "2026-04-03T10:31:14+09:00",
          "tree_id": "d413e2b1e5a903c1f5b6e7a5b9e17bb54ab0166d",
          "url": "https://github.com/eddmpython/dartlab/commit/97847d1c07d44ccccfb6c7ae80487659c64f79ce"
        },
        "date": 1775179935237,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 520300.8028503234,
            "unit": "iter/sec",
            "range": "stddev: 8.713332233095846e-7",
            "extra": "mean: 1.9219651296361218 usec\nrounds: 47777"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 611368.000009798,
            "unit": "iter/sec",
            "range": "stddev: 8.165788807840527e-7",
            "extra": "mean: 1.6356760576019251 usec\nrounds: 110816"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 513853.6942900302,
            "unit": "iter/sec",
            "range": "stddev: 5.422743471034817e-7",
            "extra": "mean: 1.9460792266593654 usec\nrounds: 111932"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 684340.5991074722,
            "unit": "iter/sec",
            "range": "stddev: 4.1733822662497826e-7",
            "extra": "mean: 1.461260666551445 usec\nrounds: 156986"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 914832.0704446186,
            "unit": "iter/sec",
            "range": "stddev: 1.569566942008083e-7",
            "extra": "mean: 1.093096790445911 usec\nrounds: 170678"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 251941.3733765341,
            "unit": "iter/sec",
            "range": "stddev: 6.622334576817035e-7",
            "extra": "mean: 3.969177378839915 usec\nrounds: 68909"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7119852.135525084,
            "unit": "iter/sec",
            "range": "stddev: 1.2780057752142631e-8",
            "extra": "mean: 140.45235504406313 nsec\nrounds: 68814"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8056533.160568688,
            "unit": "iter/sec",
            "range": "stddev: 3.954767485459147e-8",
            "extra": "mean: 124.12286774841658 nsec\nrounds: 78933"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1476099.5395730417,
            "unit": "iter/sec",
            "range": "stddev: 3.071841384797568e-7",
            "extra": "mean: 677.4610879488843 nsec\nrounds: 179276"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "bb7aed737bb6aa807d850c85c9259bc21fc864ea",
          "message": "feat: YouTube 임베딩 컴포넌트 + uv 안내 Shorts 블로그 삽입",
          "timestamp": "2026-04-03T15:32:23+09:00",
          "tree_id": "e2eface19ffc6a2d4ab00c864122fa4e58b0f113",
          "url": "https://github.com/eddmpython/dartlab/commit/bb7aed737bb6aa807d850c85c9259bc21fc864ea"
        },
        "date": 1775198015630,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 536525.6410647371,
            "unit": "iter/sec",
            "range": "stddev: 5.107889691681958e-7",
            "extra": "mean: 1.8638438193102875 usec\nrounds: 55916"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 656573.6487336836,
            "unit": "iter/sec",
            "range": "stddev: 4.697903049658568e-7",
            "extra": "mean: 1.5230583833644158 usec\nrounds: 156226"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 530003.5717002309,
            "unit": "iter/sec",
            "range": "stddev: 5.321255203451076e-7",
            "extra": "mean: 1.8867797377139153 usec\nrounds: 132206"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 683099.4292496305,
            "unit": "iter/sec",
            "range": "stddev: 3.890187352312824e-7",
            "extra": "mean: 1.4639157305379065 usec\nrounds: 151241"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 912366.6851182373,
            "unit": "iter/sec",
            "range": "stddev: 1.5837594804785078e-7",
            "extra": "mean: 1.096050542299674 usec\nrounds: 172414"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267625.80022632197,
            "unit": "iter/sec",
            "range": "stddev: 8.386174820727304e-7",
            "extra": "mean: 3.7365605227684866 usec\nrounds: 69701"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7458946.950606201,
            "unit": "iter/sec",
            "range": "stddev: 1.2615284978760203e-8",
            "extra": "mean: 134.06718222050478 nsec\nrounds: 72802"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8972634.388459472,
            "unit": "iter/sec",
            "range": "stddev: 1.5554484056517145e-8",
            "extra": "mean: 111.44998856592126 nsec\nrounds: 88332"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1449313.3098570732,
            "unit": "iter/sec",
            "range": "stddev: 2.9022905260181355e-7",
            "extra": "mean: 689.9819336500931 nsec\nrounds: 156202"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "d365417d62c4473b09c5f604c03d5eae88a56261",
          "message": "feat: macro 엔진 + credit v3 60% + analysis TTM + 문서 현행화\n\nmacro: 5축(사이클/금리/자산/심리/유동성) 시장 레벨 분석 엔진.\ncredit v3: Notch Adjustment Layer로 53→60% (18/30). 50개사 확대 64%.\nanalysis: 14축 TTM 환산. KB ROE 0.09→8.41%.\n프롬프트 69% 압축. company-reports 블로그 카테고리.\n\nNote: 대용량 fixture(034730/055550 docs >50MB) gitignore 처리.",
          "timestamp": "2026-04-03T22:27:59+09:00",
          "tree_id": "02bd81e2e0d328c4ea70be3a0852f1168ade6f31",
          "url": "https://github.com/eddmpython/dartlab/commit/d365417d62c4473b09c5f604c03d5eae88a56261"
        },
        "date": 1775222956664,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 537260.6309985344,
            "unit": "iter/sec",
            "range": "stddev: 4.632087695943408e-7",
            "extra": "mean: 1.8612940206347037 usec\nrounds: 55792"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 654724.5503101139,
            "unit": "iter/sec",
            "range": "stddev: 4.5441650573829053e-7",
            "extra": "mean: 1.5273598638180659 usec\nrounds: 120993"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527576.9163351842,
            "unit": "iter/sec",
            "range": "stddev: 5.235087904003489e-7",
            "extra": "mean: 1.8954582147879122 usec\nrounds: 113174"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 669584.8100543277,
            "unit": "iter/sec",
            "range": "stddev: 4.1817228658732447e-7",
            "extra": "mean: 1.493462792142587 usec\nrounds: 148302"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 798098.3597772301,
            "unit": "iter/sec",
            "range": "stddev: 3.8824304710541746e-7",
            "extra": "mean: 1.2529783926371256 usec\nrounds: 164990"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267375.31127218064,
            "unit": "iter/sec",
            "range": "stddev: 6.915577872229049e-7",
            "extra": "mean: 3.740061097047318 usec\nrounds: 73015"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7272041.176271894,
            "unit": "iter/sec",
            "range": "stddev: 1.1772587793994578e-8",
            "extra": "mean: 137.51297273493478 nsec\nrounds: 73720"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8597734.274253927,
            "unit": "iter/sec",
            "range": "stddev: 1.0643176175077223e-8",
            "extra": "mean: 116.30971231508263 nsec\nrounds: 85823"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1423021.1049744608,
            "unit": "iter/sec",
            "range": "stddev: 3.566155075957426e-7",
            "extra": "mean: 702.7302662654095 nsec\nrounds: 164718"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "1522b95031e2af0045cd6db0fd4ff6fe23c012b3",
          "message": "fix: CHS 보정 강도 축소 — 30%/±6→15%/±3 (주가 급락 과보정 방지)",
          "timestamp": "2026-04-03T22:41:47+09:00",
          "tree_id": "ffed58cc3acb2687feb9512af940ed70e1d97d3a",
          "url": "https://github.com/eddmpython/dartlab/commit/1522b95031e2af0045cd6db0fd4ff6fe23c012b3"
        },
        "date": 1775223771323,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 536126.2898376249,
            "unit": "iter/sec",
            "range": "stddev: 5.55198522133759e-7",
            "extra": "mean: 1.8652321644269063 usec\nrounds: 57007"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 653445.3107643005,
            "unit": "iter/sec",
            "range": "stddev: 4.808556967428726e-7",
            "extra": "mean: 1.5303499520569714 usec\nrounds: 132381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 533408.9432545202,
            "unit": "iter/sec",
            "range": "stddev: 5.500062316820888e-7",
            "extra": "mean: 1.8747342215498668 usec\nrounds: 123840"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 665557.581462788,
            "unit": "iter/sec",
            "range": "stddev: 4.139837345531802e-7",
            "extra": "mean: 1.5024996001129785 usec\nrounds: 153799"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 897432.1798657915,
            "unit": "iter/sec",
            "range": "stddev: 1.610405172605182e-7",
            "extra": "mean: 1.1142903301612688 usec\nrounds: 173581"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 260281.16995987293,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014742534506377003",
            "extra": "mean: 3.841999020344684 usec\nrounds: 69411"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7263433.442254369,
            "unit": "iter/sec",
            "range": "stddev: 1.6245342613882414e-8",
            "extra": "mean: 137.6759363116884 nsec\nrounds: 72855"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8899757.444984278,
            "unit": "iter/sec",
            "range": "stddev: 3.412901729144695e-8",
            "extra": "mean: 112.36261282194603 nsec\nrounds: 88724"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1442584.146795619,
            "unit": "iter/sec",
            "range": "stddev: 2.9791967703503985e-7",
            "extra": "mean: 693.2004640570037 nsec\nrounds: 175408"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "ade32d5e79a9a13f9a1fe08b62b4ecb4f5caf63a",
          "message": "release: v0.8.8 — credit v3 + macro + analysis TTM + AI 멀티턴",
          "timestamp": "2026-04-04T06:13:27+09:00",
          "tree_id": "3fdc452df4cad0de4f6390ca233c3bdd3586c9ca",
          "url": "https://github.com/eddmpython/dartlab/commit/ade32d5e79a9a13f9a1fe08b62b4ecb4f5caf63a"
        },
        "date": 1775250877057,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 536377.6174236755,
            "unit": "iter/sec",
            "range": "stddev: 4.784438566935542e-7",
            "extra": "mean: 1.8643581825863498 usec\nrounds: 96247"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 657320.3293261304,
            "unit": "iter/sec",
            "range": "stddev: 4.409333409402738e-7",
            "extra": "mean: 1.5213282708374114 usec\nrounds: 166058"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 518087.98481432674,
            "unit": "iter/sec",
            "range": "stddev: 6.433832421720761e-7",
            "extra": "mean: 1.9301740810653651 usec\nrounds: 129635"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 690498.8168893186,
            "unit": "iter/sec",
            "range": "stddev: 4.6851543229663837e-7",
            "extra": "mean: 1.4482284046553144 usec\nrounds: 175408"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 911505.5363688336,
            "unit": "iter/sec",
            "range": "stddev: 1.9943969876242649e-7",
            "extra": "mean: 1.0970860407318006 usec\nrounds: 26717"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269791.37433973287,
            "unit": "iter/sec",
            "range": "stddev: 6.842922636073369e-7",
            "extra": "mean: 3.706567722735113 usec\nrounds: 70892"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7351466.506600474,
            "unit": "iter/sec",
            "range": "stddev: 3.301099283285552e-8",
            "extra": "mean: 136.02728096525442 nsec\nrounds: 74600"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8851326.115615508,
            "unit": "iter/sec",
            "range": "stddev: 1.103552985905526e-8",
            "extra": "mean: 112.97742134207441 nsec\nrounds: 89438"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453245.9277010534,
            "unit": "iter/sec",
            "range": "stddev: 2.8054851649209255e-7",
            "extra": "mean: 688.1147787435668 nsec\nrounds: 158958"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "7ffb46128ea53c3d9dd81b411712f2afa587196f",
          "message": "style: ruff lint+format 수정 (unused import, formatting)",
          "timestamp": "2026-04-04T06:19:50+09:00",
          "tree_id": "540124c3408df793b377ba5f878bac4d8eaab4f9",
          "url": "https://github.com/eddmpython/dartlab/commit/7ffb46128ea53c3d9dd81b411712f2afa587196f"
        },
        "date": 1775251260499,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 464560.7564863425,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011194227631762546",
            "extra": "mean: 2.152570973845051 usec\nrounds: 53724"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 664618.0601473232,
            "unit": "iter/sec",
            "range": "stddev: 4.658547059650712e-7",
            "extra": "mean: 1.5046235724896402 usec\nrounds: 123381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 540303.2027856286,
            "unit": "iter/sec",
            "range": "stddev: 5.916858356710264e-7",
            "extra": "mean: 1.850812645278287 usec\nrounds: 111409"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 686836.9945464579,
            "unit": "iter/sec",
            "range": "stddev: 4.259893206748571e-7",
            "extra": "mean: 1.455949530878625 usec\nrounds: 151241"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 820317.0586957211,
            "unit": "iter/sec",
            "range": "stddev: 3.913393923876621e-7",
            "extra": "mean: 1.2190408445119614 usec\nrounds: 170329"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267081.1251919313,
            "unit": "iter/sec",
            "range": "stddev: 8.275172105319744e-7",
            "extra": "mean: 3.7441807214245277 usec\nrounds: 65067"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7294968.389141228,
            "unit": "iter/sec",
            "range": "stddev: 1.2306940569656206e-8",
            "extra": "mean: 137.08078591382647 nsec\nrounds: 73774"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8714425.13984829,
            "unit": "iter/sec",
            "range": "stddev: 1.2227178571263059e-8",
            "extra": "mean: 114.75226236407937 nsec\nrounds: 87329"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1447476.022913974,
            "unit": "iter/sec",
            "range": "stddev: 3.005239170791357e-7",
            "extra": "mean: 690.8577304008522 nsec\nrounds: 151241"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "1e934e9189bdb4327617e100a99f1542b421ea01",
          "message": "feat: credit v4 — notch 문턱10 + CHS PD비대칭 + OFS동적 + 축1압축\n\nPhase 1: Notch 문턱 15→10, A범위 sub-cap 2.\nPhase 2: CHS PD<0.001 -5점, PD<0.01 상향만, PD>0.1 하향만.\nPhase 3: OFS 별도가 10점+ 양호하면 35:65.\nPhase 4: captive/holding/cyclical 축1 20초과 40% 압축.",
          "timestamp": "2026-04-04T07:04:08+09:00",
          "tree_id": "b8ee825777170a53ad70b1409aea9c3d61251fa8",
          "url": "https://github.com/eddmpython/dartlab/commit/1e934e9189bdb4327617e100a99f1542b421ea01"
        },
        "date": 1775254281304,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 541650.4207965188,
            "unit": "iter/sec",
            "range": "stddev: 4.576864801291731e-7",
            "extra": "mean: 1.8462092183542655 usec\nrounds: 58991"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 650168.6467149155,
            "unit": "iter/sec",
            "range": "stddev: 5.777304435635166e-7",
            "extra": "mean: 1.5380624781780314 usec\nrounds: 157431"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 515038.7737692007,
            "unit": "iter/sec",
            "range": "stddev: 5.142147901169372e-7",
            "extra": "mean: 1.941601391836414 usec\nrounds: 134355"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 719556.696033644,
            "unit": "iter/sec",
            "range": "stddev: 3.2032681518931387e-7",
            "extra": "mean: 1.3897445545461833 usec\nrounds: 178222"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 895439.8156661675,
            "unit": "iter/sec",
            "range": "stddev: 1.5881788417162086e-7",
            "extra": "mean: 1.116769639348731 usec\nrounds: 174186"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 265926.405782523,
            "unit": "iter/sec",
            "range": "stddev: 6.584082408006705e-7",
            "extra": "mean: 3.7604388968345215 usec\nrounds: 74767"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7299573.587053359,
            "unit": "iter/sec",
            "range": "stddev: 1.2752706339015179e-8",
            "extra": "mean: 136.9943035814607 nsec\nrounds: 73878"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8724079.580839438,
            "unit": "iter/sec",
            "range": "stddev: 1.0857270090002678e-8",
            "extra": "mean: 114.625272584203 nsec\nrounds: 87551"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1443942.665506349,
            "unit": "iter/sec",
            "range": "stddev: 2.7806687771361483e-7",
            "extra": "mean: 692.5482734796323 nsec\nrounds: 103649"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2b57af29bd3fec715a0e71afe1ba4a638caf7bc1",
          "message": "feat: 정성 대리 신호 3개 — 시가총액 시장지위 + 연속 흑자 + notch cap 5→7\n\n시가총액 30조+ (+2), 10조+ (+1): 시장이 인정한 지위/암묵적 지원.\n연속 5기 영업흑자 (+1): 경영 역량 대리.\n총 notch cap 5→7. A범위 sub-cap 2→3 (POSCO 악화 방지).",
          "timestamp": "2026-04-04T09:47:27+09:00",
          "tree_id": "42c324620b856f4d5e855c9368f4f120c5c53418",
          "url": "https://github.com/eddmpython/dartlab/commit/2b57af29bd3fec715a0e71afe1ba4a638caf7bc1"
        },
        "date": 1775264146109,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 577440.1724562531,
            "unit": "iter/sec",
            "range": "stddev: 2.963036566113102e-7",
            "extra": "mean: 1.7317811397608642 usec\nrounds: 56447"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 695330.9170658508,
            "unit": "iter/sec",
            "range": "stddev: 3.11015163626761e-7",
            "extra": "mean: 1.438164153867612 usec\nrounds: 137761"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 567767.9453080017,
            "unit": "iter/sec",
            "range": "stddev: 3.369970838014683e-7",
            "extra": "mean: 1.7612829471334839 usec\nrounds: 110632"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 720319.3477260382,
            "unit": "iter/sec",
            "range": "stddev: 3.2135026815261217e-7",
            "extra": "mean: 1.3882731362927847 usec\nrounds: 160257"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 980570.4661330692,
            "unit": "iter/sec",
            "range": "stddev: 9.430191540694395e-8",
            "extra": "mean: 1.0198145207692744 usec\nrounds: 184095"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 299301.3652526446,
            "unit": "iter/sec",
            "range": "stddev: 3.5949103434284833e-7",
            "extra": "mean: 3.3411140612602472 usec\nrounds: 72391"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8485970.031598851,
            "unit": "iter/sec",
            "range": "stddev: 1.3414128833435107e-8",
            "extra": "mean: 117.84156628839627 nsec\nrounds: 82488"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9885332.906585885,
            "unit": "iter/sec",
            "range": "stddev: 7.009042531921105e-9",
            "extra": "mean: 101.1599719958619 nsec\nrounds: 86768"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1556520.7014652023,
            "unit": "iter/sec",
            "range": "stddev: 1.4061742093542386e-7",
            "extra": "mean: 642.4585288577713 nsec\nrounds: 150671"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "ca04b718570e818eb8ec5a50b3a62da0108fe001",
          "message": "feat: 금융 유동0% + 매출/시총 notch 강화 + A범위 cap 3→4\n\nTrack B 유동성 가중치 5→0% (은행 현금/자산 무의미).\n매출 50조+ notch 2→3, 시총 30조+ notch 2→3.\nA범위 sub-cap 3→4 (대기업 추가 1 notch 확보).",
          "timestamp": "2026-04-04T10:06:52+09:00",
          "tree_id": "f85eb8bd530475aeb2e595456b429a065221064f",
          "url": "https://github.com/eddmpython/dartlab/commit/ca04b718570e818eb8ec5a50b3a62da0108fe001"
        },
        "date": 1775264869715,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 533591.3359194624,
            "unit": "iter/sec",
            "range": "stddev: 5.190203343833278e-7",
            "extra": "mean: 1.8740933982311418 usec\nrounds: 68042"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 666075.8889599664,
            "unit": "iter/sec",
            "range": "stddev: 5.282503391893207e-7",
            "extra": "mean: 1.5013304288216078 usec\nrounds: 163079"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 459552.5541273089,
            "unit": "iter/sec",
            "range": "stddev: 9.418694078131082e-7",
            "extra": "mean: 2.1760296858734725 usec\nrounds: 142593"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 614813.4884490323,
            "unit": "iter/sec",
            "range": "stddev: 8.231246468147171e-7",
            "extra": "mean: 1.6265095330336097 usec\nrounds: 130651"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 767183.3235497389,
            "unit": "iter/sec",
            "range": "stddev: 6.85074599894918e-7",
            "extra": "mean: 1.3034694176784551 usec\nrounds: 156937"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 263558.96876543754,
            "unit": "iter/sec",
            "range": "stddev: 0.000001115040997100971",
            "extra": "mean: 3.794217304325473 usec\nrounds: 67486"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7335870.136679389,
            "unit": "iter/sec",
            "range": "stddev: 1.2487943460019713e-8",
            "extra": "mean: 136.316480713037 nsec\nrounds: 74427"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8774807.55025009,
            "unit": "iter/sec",
            "range": "stddev: 1.0848166261488212e-8",
            "extra": "mean: 113.96261334204407 nsec\nrounds: 84589"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453941.0519500233,
            "unit": "iter/sec",
            "range": "stddev: 2.796218375235372e-7",
            "extra": "mean: 687.7857934190672 nsec\nrounds: 172385"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "280b03bca608678e35526eaa75672ffe2e2210a0",
          "message": "fix: Track B 자산건전성 fallback 규모 기반 — 대형 금융지주 12점, 중형 20점\n\n금융지주 자산건전성 데이터 없을 때 자산규모로 추정:\n100조+ → 12점(양호), 10조+ → 20점, 소형 → 25점(중립).",
          "timestamp": "2026-04-04T10:17:12+09:00",
          "tree_id": "20ab981b14b941ce345c47b9572173a2b452ac28",
          "url": "https://github.com/eddmpython/dartlab/commit/280b03bca608678e35526eaa75672ffe2e2210a0"
        },
        "date": 1775265589426,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 582119.2284254202,
            "unit": "iter/sec",
            "range": "stddev: 3.0354012255499007e-7",
            "extra": "mean: 1.7178611376657482 usec\nrounds: 58576"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 717308.5653113885,
            "unit": "iter/sec",
            "range": "stddev: 3.1356995730990545e-7",
            "extra": "mean: 1.3941001799774877 usec\nrounds: 122250"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 584020.2724264538,
            "unit": "iter/sec",
            "range": "stddev: 2.998941195970424e-7",
            "extra": "mean: 1.712269329017052 usec\nrounds: 126455"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 763219.4642554712,
            "unit": "iter/sec",
            "range": "stddev: 2.320693726825884e-7",
            "extra": "mean: 1.3102391210312105 usec\nrounds: 150083"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 898481.8236953836,
            "unit": "iter/sec",
            "range": "stddev: 2.544567166934938e-7",
            "extra": "mean: 1.1129885698600783 usec\nrounds: 190549"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 296256.2565322525,
            "unit": "iter/sec",
            "range": "stddev: 3.879919078117553e-7",
            "extra": "mean: 3.3754561395773703 usec\nrounds: 69402"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8376171.787053662,
            "unit": "iter/sec",
            "range": "stddev: 2.2606018171128746e-8",
            "extra": "mean: 119.3862811583706 nsec\nrounds: 75701"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9735626.46772143,
            "unit": "iter/sec",
            "range": "stddev: 1.611754850746848e-8",
            "extra": "mean: 102.7155266603038 nsec\nrounds: 84020"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1519486.3443255045,
            "unit": "iter/sec",
            "range": "stddev: 1.547423654505424e-7",
            "extra": "mean: 658.117135263823 nsec\nrounds: 172177"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "39ab106f92cbe371be126fff59ecbc08fb5332ae",
          "message": "feat: 괴리 설명 자동 생성 + CHS 우량기업 하향 보호 + Track B 자산건전 규모 기반\n\n_explainDivergence: 축별 병목/FCF음수/CHS하향/D/EBITDA/정량한계 자동 설명.\nCHS: baseScore<10(AA이상)이면 하향 max +1점 (SKT 주가 급락 보호).\nTrack B: 자산건전성 fallback 규모 기반 (100조+ → 12점).",
          "timestamp": "2026-04-04T10:52:32+09:00",
          "tree_id": "ffac2ab325cc258a98252c865ec9538bf1135dd8",
          "url": "https://github.com/eddmpython/dartlab/commit/39ab106f92cbe371be126fff59ecbc08fb5332ae"
        },
        "date": 1775267614995,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 510837.77376166213,
            "unit": "iter/sec",
            "range": "stddev: 7.405948311792699e-7",
            "extra": "mean: 1.957568628169934 usec\nrounds: 53462"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 673669.5336950638,
            "unit": "iter/sec",
            "range": "stddev: 4.95022731920772e-7",
            "extra": "mean: 1.4844073391816017 usec\nrounds: 140588"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 534992.9606344969,
            "unit": "iter/sec",
            "range": "stddev: 5.639470677005444e-7",
            "extra": "mean: 1.869183472646087 usec\nrounds: 125392"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 683052.5293387492,
            "unit": "iter/sec",
            "range": "stddev: 3.991441816912549e-7",
            "extra": "mean: 1.4640162462586617 usec\nrounds: 168039"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 909378.2082689047,
            "unit": "iter/sec",
            "range": "stddev: 1.6649187504338966e-7",
            "extra": "mean: 1.0996524778217451 usec\nrounds: 173883"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269864.8969654418,
            "unit": "iter/sec",
            "range": "stddev: 7.110020747514544e-7",
            "extra": "mean: 3.7055578967280702 usec\nrounds: 74322"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7229638.307439052,
            "unit": "iter/sec",
            "range": "stddev: 1.1954733579840561e-8",
            "extra": "mean: 138.31950610461854 nsec\nrounds: 67079"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8876258.901098853,
            "unit": "iter/sec",
            "range": "stddev: 1.0929258386932e-8",
            "extra": "mean: 112.66007573035111 nsec\nrounds: 78040"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1456989.523692775,
            "unit": "iter/sec",
            "range": "stddev: 2.775324834112835e-7",
            "extra": "mean: 686.3467332733292 nsec\nrounds: 194553"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "882393d38122a0b4c0f2f647a97879982d9627d5",
          "message": "fix: EDGAR 데이터 싱크 근본 원인 6건 수정\n\n1. vertical_relaxed → 스키마 정합 concat (증분 업데이트 시 컬럼 불일치로 데이터 오염)\n2. batch.py ticker-level asyncio Lock (동시 쓰기 경합으로 데이터 유실)\n3. freshness.py 컬럼 존재 검증 (filing_date 없는 parquet에서 silent fail → 반복 재수집)\n4. asyncClient 이벤트 루프별 세마포어 (루프 간 공유로 교착 상태)\n5. batch.py 예외 logging 추가 (silent failure로 원인 추적 불가)\n6. deploy.py 카테고리 사전 검증 (DATA_RELEASES 매핑 미스매치)",
          "timestamp": "2026-04-04T11:03:35+09:00",
          "tree_id": "a4a3514f72841739ed676a324ec1006b8cb30922",
          "url": "https://github.com/eddmpython/dartlab/commit/882393d38122a0b4c0f2f647a97879982d9627d5"
        },
        "date": 1775268283110,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 491121.26570511167,
            "unit": "iter/sec",
            "range": "stddev: 5.368760092598912e-7",
            "extra": "mean: 2.0361569938623654 usec\nrounds: 57429"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 601930.3611194476,
            "unit": "iter/sec",
            "range": "stddev: 4.874116728274703e-7",
            "extra": "mean: 1.6613217484830594 usec\nrounds: 122459"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 510348.063724583,
            "unit": "iter/sec",
            "range": "stddev: 5.550994668999403e-7",
            "extra": "mean: 1.959447034445231 usec\nrounds: 107551"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 588209.7300621204,
            "unit": "iter/sec",
            "range": "stddev: 4.315265443223412e-7",
            "extra": "mean: 1.7000738833313602 usec\nrounds: 148545"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 735857.8947312891,
            "unit": "iter/sec",
            "range": "stddev: 3.738892547935528e-7",
            "extra": "mean: 1.3589580368165606 usec\nrounds: 162023"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 257094.5282768964,
            "unit": "iter/sec",
            "range": "stddev: 7.180228908580126e-7",
            "extra": "mean: 3.889619925800125 usec\nrounds: 68976"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7362190.947373957,
            "unit": "iter/sec",
            "range": "stddev: 1.3393658378904826e-8",
            "extra": "mean: 135.82913118501676 nsec\nrounds: 73606"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8552745.972368507,
            "unit": "iter/sec",
            "range": "stddev: 1.1144827415600409e-8",
            "extra": "mean: 116.92151307085653 nsec\nrounds: 86949"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453126.3577988255,
            "unit": "iter/sec",
            "range": "stddev: 2.737424264317009e-7",
            "extra": "mean: 688.1713999839528 nsec\nrounds: 156937"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "edf635e7198eebdbd88cc8e2d4cd0c25053f06ca",
          "message": "fix: Track B에 Notch+divergence 추가 + CHS 현금및예치금 fallback\n\nTrack B 금융업에 Notch Adjustment 누락 수정.\nCHS BS select에 현금및예치금 fallback (금융지주).\nKB금융 CHS None→동작(PD 0.86%).",
          "timestamp": "2026-04-04T11:05:40+09:00",
          "tree_id": "3751c344ef98881539ac7f0a9862d07ddb1e9902",
          "url": "https://github.com/eddmpython/dartlab/commit/edf635e7198eebdbd88cc8e2d4cd0c25053f06ca"
        },
        "date": 1775268408388,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 534008.1919334071,
            "unit": "iter/sec",
            "range": "stddev: 4.862815697695599e-7",
            "extra": "mean: 1.8726304485694178 usec\nrounds: 50564"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 651875.0955042711,
            "unit": "iter/sec",
            "range": "stddev: 4.6867082133394834e-7",
            "extra": "mean: 1.5340362086182013 usec\nrounds: 121877"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 523158.30937918526,
            "unit": "iter/sec",
            "range": "stddev: 5.738473891178633e-7",
            "extra": "mean: 1.9114672978943357 usec\nrounds: 119977"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 650790.1789807567,
            "unit": "iter/sec",
            "range": "stddev: 4.5133676875597234e-7",
            "extra": "mean: 1.536593563176019 usec\nrounds: 127796"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 798917.9062591866,
            "unit": "iter/sec",
            "range": "stddev: 4.1877066476528406e-7",
            "extra": "mean: 1.2516930615341322 usec\nrounds: 159185"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267054.4673230943,
            "unit": "iter/sec",
            "range": "stddev: 7.364599035901946e-7",
            "extra": "mean: 3.7445544724408437 usec\nrounds: 58167"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7338822.073407057,
            "unit": "iter/sec",
            "range": "stddev: 1.3163418568277492e-8",
            "extra": "mean: 136.26164934882374 nsec\nrounds: 73720"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8823020.786324712,
            "unit": "iter/sec",
            "range": "stddev: 1.1772263996383044e-8",
            "extra": "mean: 113.33986672115239 nsec\nrounds: 78107"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1455063.899739045,
            "unit": "iter/sec",
            "range": "stddev: 3.1047327213728356e-7",
            "extra": "mean: 687.2550409499835 nsec\nrounds: 156716"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "0febbc615e44795723462b17d704137294971047",
          "message": "feat: credit v5 WS-A+B — notch 규모별 cap + 보고서 12섹션\n\nWS-A: 매출 기반 notch cap (대형7/중형4/소형2). 과대평가 수정.\nWS-B: 보고서 섹션 9~11 추가 (괴리분석/notch상세/별도재무비교).\nengine.py: separateMetrics를 result에 포함.",
          "timestamp": "2026-04-04T11:53:55+09:00",
          "tree_id": "8d82418639f73f041a408c4ccfdee94b2def8836",
          "url": "https://github.com/eddmpython/dartlab/commit/0febbc615e44795723462b17d704137294971047"
        },
        "date": 1775271292645,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 532034.1729533382,
            "unit": "iter/sec",
            "range": "stddev: 4.873160423612389e-7",
            "extra": "mean: 1.8795785136299965 usec\nrounds: 53634"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 648699.9731116028,
            "unit": "iter/sec",
            "range": "stddev: 4.7243339799594387e-7",
            "extra": "mean: 1.5415446916134823 usec\nrounds: 145497"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 519257.36140286055,
            "unit": "iter/sec",
            "range": "stddev: 5.736610777574474e-7",
            "extra": "mean: 1.9258272955405635 usec\nrounds: 117565"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 671987.670027836,
            "unit": "iter/sec",
            "range": "stddev: 4.162214825981967e-7",
            "extra": "mean: 1.4881225424248878 usec\nrounds: 163372"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 889221.2629718522,
            "unit": "iter/sec",
            "range": "stddev: 1.6573389538854233e-7",
            "extra": "mean: 1.124579496286353 usec\nrounds: 163346"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 258299.824787295,
            "unit": "iter/sec",
            "range": "stddev: 7.139377631331197e-7",
            "extra": "mean: 3.871469912236607 usec\nrounds: 68134"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 6919581.755557025,
            "unit": "iter/sec",
            "range": "stddev: 3.444194870784791e-8",
            "extra": "mean: 144.51740514474207 nsec\nrounds: 69896"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8357617.584346261,
            "unit": "iter/sec",
            "range": "stddev: 1.8594849504921363e-8",
            "extra": "mean: 119.65132286897054 nsec\nrounds: 82631"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1435907.3877053785,
            "unit": "iter/sec",
            "range": "stddev: 3.022158806578985e-7",
            "extra": "mean: 696.4237447082356 nsec\nrounds: 173883"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "06ae0bfca33854712a13d20fe617b731e839548b",
          "message": "docs: credit 방법론 문서 v5 — 3-Track/Notch/CHS/OFS/검증/12섹션 반영\n\nops/credit.md: Layer 3에 3-Track+OFS+축1압축+CHS 추가.\nLayer 4에 Notch Adjustment 7규칙 상세. 보고서 12섹션.\n방법론 기반(S&P/Moody's/KIS/Campbell 참조). dartlab 고유 접근 4개.\n검증 결과: 대기업 87%, 79개사 70%.",
          "timestamp": "2026-04-04T11:56:52+09:00",
          "tree_id": "48c3754aba103d0ba108660cbff662b754847756",
          "url": "https://github.com/eddmpython/dartlab/commit/06ae0bfca33854712a13d20fe617b731e839548b"
        },
        "date": 1775271473559,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 539680.5416597157,
            "unit": "iter/sec",
            "range": "stddev: 5.19190247650442e-7",
            "extra": "mean: 1.8529480364895738 usec\nrounds: 56809"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 657302.4891037334,
            "unit": "iter/sec",
            "range": "stddev: 4.6869363530704357e-7",
            "extra": "mean: 1.521369562077199 usec\nrounds: 132381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527081.3880865815,
            "unit": "iter/sec",
            "range": "stddev: 5.253716915707974e-7",
            "extra": "mean: 1.897240203510533 usec\nrounds: 119532"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 667612.032495522,
            "unit": "iter/sec",
            "range": "stddev: 3.921906048631105e-7",
            "extra": "mean: 1.4978759389072387 usec\nrounds: 186916"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 843852.7539583162,
            "unit": "iter/sec",
            "range": "stddev: 1.6658252434394937e-7",
            "extra": "mean: 1.1850408679822797 usec\nrounds: 166639"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266862.0977319042,
            "unit": "iter/sec",
            "range": "stddev: 6.606516816262024e-7",
            "extra": "mean: 3.747253763269983 usec\nrounds: 67760"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7220978.214634719,
            "unit": "iter/sec",
            "range": "stddev: 2.2721368005971682e-8",
            "extra": "mean: 138.48539218319553 nsec\nrounds: 73180"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8914727.954968818,
            "unit": "iter/sec",
            "range": "stddev: 1.149797943283885e-8",
            "extra": "mean: 112.17392219384868 nsec\nrounds: 87474"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1454608.593206585,
            "unit": "iter/sec",
            "range": "stddev: 2.462270549021371e-7",
            "extra": "mean: 687.4701584125587 nsec\nrounds: 169177"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "fc71155a460dd3be637d0bb7e6bedd14076d20d2",
          "message": "publish: 신용분석 보고서 4개사 v4.0 재발간\n\n삼성전자 dCR-AA+(?확일치!), SK하이닉스 dCR-AA+, NAVER dCR-AA(정확일치), LG dCR-AA.\n12섹션 구조 + 괴리분석(섹션9) + notch상세(섹션10) + 별도재무(섹션11).\n방법론 v1.0→v4.0 업데이트.",
          "timestamp": "2026-04-04T12:03:45+09:00",
          "tree_id": "56dc088b195cd0a0c1ca90ff434e15d7dc96f664",
          "url": "https://github.com/eddmpython/dartlab/commit/fc71155a460dd3be637d0bb7e6bedd14076d20d2"
        },
        "date": 1775271889550,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 545944.9066273555,
            "unit": "iter/sec",
            "range": "stddev: 4.80670781643949e-7",
            "extra": "mean: 1.8316866553030557 usec\nrounds: 52013"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 661912.8380553451,
            "unit": "iter/sec",
            "range": "stddev: 4.657283991862933e-7",
            "extra": "mean: 1.5107729333939677 usec\nrounds: 144865"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 530251.2009641981,
            "unit": "iter/sec",
            "range": "stddev: 5.718266203787971e-7",
            "extra": "mean: 1.8858986046266755 usec\nrounds: 120686"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 686664.2948597915,
            "unit": "iter/sec",
            "range": "stddev: 3.9389266742942604e-7",
            "extra": "mean: 1.4563157098538055 usec\nrounds: 181160"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 922613.2067381116,
            "unit": "iter/sec",
            "range": "stddev: 1.6037600191146027e-7",
            "extra": "mean: 1.0838778295137228 usec\nrounds: 176992"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270225.82366919756,
            "unit": "iter/sec",
            "range": "stddev: 7.986027094239882e-7",
            "extra": "mean: 3.7006085740501633 usec\nrounds: 77256"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7335782.17075253,
            "unit": "iter/sec",
            "range": "stddev: 1.1602553399080976e-8",
            "extra": "mean: 136.31811533158114 nsec\nrounds: 73180"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8873923.136003535,
            "unit": "iter/sec",
            "range": "stddev: 1.2117168162217949e-8",
            "extra": "mean: 112.689729747914 nsec\nrounds: 88732"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1453906.6504725819,
            "unit": "iter/sec",
            "range": "stddev: 2.6717258136492643e-7",
            "extra": "mean: 687.8020673988644 nsec\nrounds: 170649"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "b31682b87868f64200afdbd5c3afd4e76d9d364a",
          "message": "feat: credit 보고서 전문화 — 13섹션 구조 + Executive Summary + 건전도 바\n\npublisher.py 전면 재작성: 9섹션→13섹션.\nNEW: Executive Summary (인과 요약), 사업 분석 3.1~3.3, 건전도 ASCII 바.\nNEW: 부문별 매출 테이블, HHI 집중도, 피어 비교 (graceful).\n8개 헬퍼 함수. audit.py sectionNum 파라미터.\n삼성전자 재발간: dCR-AA+(정확일치), 건전도 96/100.",
          "timestamp": "2026-04-04T12:46:22+09:00",
          "tree_id": "f8c492fe876b9778b80e7f57096ebefca028e126",
          "url": "https://github.com/eddmpython/dartlab/commit/b31682b87868f64200afdbd5c3afd4e76d9d364a"
        },
        "date": 1775274468669,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 601259.7629067982,
            "unit": "iter/sec",
            "range": "stddev: 3.6587143842176e-7",
            "extra": "mean: 1.6631746570990995 usec\nrounds: 51478"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 706285.3296788882,
            "unit": "iter/sec",
            "range": "stddev: 3.058771969463214e-7",
            "extra": "mean: 1.415858376181548 usec\nrounds: 112008"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 594471.4214382919,
            "unit": "iter/sec",
            "range": "stddev: 3.6076312781190784e-7",
            "extra": "mean: 1.682166650804766 usec\nrounds: 94581"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 728259.3634705488,
            "unit": "iter/sec",
            "range": "stddev: 3.4000093391148434e-7",
            "extra": "mean: 1.373137168102392 usec\nrounds: 111870"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 889182.5175907597,
            "unit": "iter/sec",
            "range": "stddev: 2.346800809101818e-7",
            "extra": "mean: 1.1246284988930062 usec\nrounds: 159873"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 295128.4581452981,
            "unit": "iter/sec",
            "range": "stddev: 3.9967295024109807e-7",
            "extra": "mean: 3.3883550447299746 usec\nrounds: 67169"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8526627.05386078,
            "unit": "iter/sec",
            "range": "stddev: 8.178660215560431e-9",
            "extra": "mean: 117.27966916850303 nsec\nrounds: 84998"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9849342.126668315,
            "unit": "iter/sec",
            "range": "stddev: 8.287655207443172e-9",
            "extra": "mean: 101.52962371896656 nsec\nrounds: 95248"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1526695.6014397691,
            "unit": "iter/sec",
            "range": "stddev: 2.7511691701278086e-7",
            "extra": "mean: 655.0094197277687 nsec\nrounds: 141724"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "8ac3f0654277372e466438d9fab5f58ca9cf5c6e",
          "message": "fix: 부문별 매출 테이블 완성 — segments 파싱 수정 + 중복 제거\n\nmetrics.py: segments DataFrame 연도 컬럼 구조 인식 (기존: '매출' 키워드 검색 실패).\npublisher.py: 중복 부문명 제거 + 비중만 표시 (금액 단위 불일치 우회).\n삼성전자: DX 34.6%, IM 21.3%, DS 18.4% 등 7개 부문.",
          "timestamp": "2026-04-04T12:52:18+09:00",
          "tree_id": "e7fa9345800bfe3c6b4f3ff0ed0559d3313eed0c",
          "url": "https://github.com/eddmpython/dartlab/commit/8ac3f0654277372e466438d9fab5f58ca9cf5c6e"
        },
        "date": 1775274801400,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 534189.833575145,
            "unit": "iter/sec",
            "range": "stddev: 5.049749287885463e-7",
            "extra": "mean: 1.8719936942778397 usec\nrounds: 56139"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 646831.0010312265,
            "unit": "iter/sec",
            "range": "stddev: 6.702641632059852e-7",
            "extra": "mean: 1.5459988751400677 usec\nrounds: 124456"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 533577.4723407782,
            "unit": "iter/sec",
            "range": "stddev: 5.425542201865735e-7",
            "extra": "mean: 1.8741420915186862 usec\nrounds: 126503"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 399506.9100977379,
            "unit": "iter/sec",
            "range": "stddev: 5.282251293870217e-7",
            "extra": "mean: 2.5030856156038794 usec\nrounds: 141563"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 884154.6296513606,
            "unit": "iter/sec",
            "range": "stddev: 1.6864181767261394e-7",
            "extra": "mean: 1.131023880284741 usec\nrounds: 173281"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269132.495709021,
            "unit": "iter/sec",
            "range": "stddev: 6.565741781310245e-7",
            "extra": "mean: 3.7156419828290588 usec\nrounds: 68790"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7289092.775053163,
            "unit": "iter/sec",
            "range": "stddev: 1.6921545330746684e-8",
            "extra": "mean: 137.19128441093363 nsec\nrounds: 73341"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8853866.545451501,
            "unit": "iter/sec",
            "range": "stddev: 1.575206148632615e-8",
            "extra": "mean: 112.94500485934365 nsec\nrounds: 88488"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1455686.9580565267,
            "unit": "iter/sec",
            "range": "stddev: 3.0090194131112547e-7",
            "extra": "mean: 686.9608843202733 nsec\nrounds: 164691"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2bcd127bc5f5e2ddabc6e5085908bd2bb653c14e",
          "message": "publish: 4개사 보고서 전문화 재발간 — 13섹션 + 부문테이블 + Executive Summary\n\n삼성전자 dCR-AA+(96/100), SK하이닉스 dCR-AA+(95/100),\nNAVER dCR-AA(94/100), LG dCR-AA(94/100).\n부문별 매출 비중, 건전도 바, 인과 요약, AI 해석.",
          "timestamp": "2026-04-04T12:54:51+09:00",
          "tree_id": "68fb4a0d92f9f5f303e442ca095caf86ab2f03e1",
          "url": "https://github.com/eddmpython/dartlab/commit/2bcd127bc5f5e2ddabc6e5085908bd2bb653c14e"
        },
        "date": 1775274952565,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542179.1399710685,
            "unit": "iter/sec",
            "range": "stddev: 4.940628165276547e-7",
            "extra": "mean: 1.8444088425337823 usec\nrounds: 55640"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 670036.4109607941,
            "unit": "iter/sec",
            "range": "stddev: 4.6046417777904754e-7",
            "extra": "mean: 1.4924562063217683 usec\nrounds: 125235"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 527311.2111328654,
            "unit": "iter/sec",
            "range": "stddev: 5.278815187264292e-7",
            "extra": "mean: 1.896413311318792 usec\nrounds: 113302"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 690238.1536301014,
            "unit": "iter/sec",
            "range": "stddev: 3.884055799127017e-7",
            "extra": "mean: 1.448775317244923 usec\nrounds: 195351"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 811842.0336735578,
            "unit": "iter/sec",
            "range": "stddev: 3.7383050453151284e-7",
            "extra": "mean: 1.2317667212610732 usec\nrounds: 164177"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 254765.9985552516,
            "unit": "iter/sec",
            "range": "stddev: 0.000001299323124599312",
            "extra": "mean: 3.9251705709195255 usec\nrounds: 63821"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7425140.27155183,
            "unit": "iter/sec",
            "range": "stddev: 2.1545823873065714e-8",
            "extra": "mean: 134.67759037917855 nsec\nrounds: 73883"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8822335.95985469,
            "unit": "iter/sec",
            "range": "stddev: 1.2051706928950162e-8",
            "extra": "mean: 113.34866463376788 nsec\nrounds: 89526"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1460075.521199614,
            "unit": "iter/sec",
            "range": "stddev: 2.920188275158247e-7",
            "extra": "mean: 684.8960793332039 nsec\nrounds: 156937"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "26d22e0b007b1feb549bba0010c3d733df663feb",
          "message": "refactor: UI 구조 재편 + macro 엔진 확장 + EDGAR 강화\n\n- vscode/webview → ui/vscode, ui/ → ui/web, ui/shared 공유 코드 분리\n- CI 워크플로우/문서 경로 일괄 업데이트 (.github/workflows/vscode.yml, ops/)\n- .gitignore에 ui/web/build, ui/vscode/node_modules 추가\n- macro 엔진: 사이클/유동성/심리/자산신호 + 위기감지/재고/교역 확장\n- EDGAR: report 14 apiType, notes 파서 강화, scan 프리빌드 개선\n- credit: 보고서 13섹션 구조화 + 이력 데이터 업데이트\n- analysis: memoize/revenue/capital 개선, search 인덱스 업데이트\n- v0.8.9 / vsce-0.2.2",
          "timestamp": "2026-04-04T13:13:45+09:00",
          "tree_id": "9f55e9946f3b3cc6e2345cc2d1e0b0cbf075be22",
          "url": "https://github.com/eddmpython/dartlab/commit/26d22e0b007b1feb549bba0010c3d733df663feb"
        },
        "date": 1775276109111,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 537731.5652374721,
            "unit": "iter/sec",
            "range": "stddev: 5.248961576240669e-7",
            "extra": "mean: 1.8596639376347228 usec\nrounds: 53377"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 663809.9180559322,
            "unit": "iter/sec",
            "range": "stddev: 4.705696816425367e-7",
            "extra": "mean: 1.5064553463266281 usec\nrounds: 127470"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 525870.0285876582,
            "unit": "iter/sec",
            "range": "stddev: 5.888713098368411e-7",
            "extra": "mean: 1.901610560856119 usec\nrounds: 102586"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 675334.9656736281,
            "unit": "iter/sec",
            "range": "stddev: 4.929666752692968e-7",
            "extra": "mean: 1.4807466676962702 usec\nrounds: 126040"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 808673.0961473365,
            "unit": "iter/sec",
            "range": "stddev: 4.092309838193978e-7",
            "extra": "mean: 1.2365936306823846 usec\nrounds: 148744"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271708.5930429675,
            "unit": "iter/sec",
            "range": "stddev: 7.593692066693473e-7",
            "extra": "mean: 3.6804135960538495 usec\nrounds: 59841"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7224135.573347682,
            "unit": "iter/sec",
            "range": "stddev: 1.2328367785698553e-8",
            "extra": "mean: 138.4248661790545 nsec\nrounds: 70542"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8556080.776134912,
            "unit": "iter/sec",
            "range": "stddev: 1.1962352341663985e-8",
            "extra": "mean: 116.87594193702036 nsec\nrounds: 83599"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1463095.152044148,
            "unit": "iter/sec",
            "range": "stddev: 2.877197451761476e-7",
            "extra": "mean: 683.4825463011484 nsec\nrounds: 165810"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "cca6371d89ebab056556bce4b6a253e9df0284d9",
          "message": "fix: CI 테스트 수정 — widget skip + FRED 그룹 수 14개 반영\n\n- test_embed.py: ui/widget 미구현 상태에서 skip 처리\n- test_fred.py: FRED catalog 7→14 그룹 확장 반영",
          "timestamp": "2026-04-04T14:20:15+09:00",
          "tree_id": "dc443172e055567665be9b2e327f5e7738528650",
          "url": "https://github.com/eddmpython/dartlab/commit/cca6371d89ebab056556bce4b6a253e9df0284d9"
        },
        "date": 1775280084794,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 525616.0228263675,
            "unit": "iter/sec",
            "range": "stddev: 4.707209817957906e-7",
            "extra": "mean: 1.9025295207378805 usec\nrounds: 55605"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 654642.3070226081,
            "unit": "iter/sec",
            "range": "stddev: 4.7089448101389246e-7",
            "extra": "mean: 1.5275517473780762 usec\nrounds: 119977"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 518055.8071606594,
            "unit": "iter/sec",
            "range": "stddev: 5.022999473810521e-7",
            "extra": "mean: 1.9302939686763907 usec\nrounds: 122775"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 668065.6121169955,
            "unit": "iter/sec",
            "range": "stddev: 3.8939502029778356e-7",
            "extra": "mean: 1.49685896394391 usec\nrounds: 132732"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 889204.6430527109,
            "unit": "iter/sec",
            "range": "stddev: 1.5320285323358728e-7",
            "extra": "mean: 1.1246005155426537 usec\nrounds: 174186"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 261657.20763709708,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014515182446766354",
            "extra": "mean: 3.821794205596432 usec\nrounds: 67169"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7451810.489974386,
            "unit": "iter/sec",
            "range": "stddev: 1.492255008619537e-8",
            "extra": "mean: 134.19557587319122 nsec\nrounds: 74157"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8953222.048724689,
            "unit": "iter/sec",
            "range": "stddev: 1.061309668494349e-8",
            "extra": "mean: 111.69163397912617 nsec\nrounds: 88410"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1460345.327063674,
            "unit": "iter/sec",
            "range": "stddev: 3.1316801662544076e-7",
            "extra": "mean: 684.7695414691444 nsec\nrounds: 163908"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "67d65263e14417e0d7f2c2a75b5edfab06cdde06",
          "message": "chore: uv.lock 동기화 (v0.8.9)",
          "timestamp": "2026-04-04T14:21:32+09:00",
          "tree_id": "cf2764643f4b32d119154fed74000e375a0c134a",
          "url": "https://github.com/eddmpython/dartlab/commit/67d65263e14417e0d7f2c2a75b5edfab06cdde06"
        },
        "date": 1775280155444,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542093.292901491,
            "unit": "iter/sec",
            "range": "stddev: 4.881386670162066e-7",
            "extra": "mean: 1.8447009271183135 usec\nrounds: 58133"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 663114.5761934384,
            "unit": "iter/sec",
            "range": "stddev: 4.704936941872622e-7",
            "extra": "mean: 1.5080350152162667 usec\nrounds: 131857"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 529674.9536694825,
            "unit": "iter/sec",
            "range": "stddev: 5.614216891061813e-7",
            "extra": "mean: 1.887950323254289 usec\nrounds: 126679"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 674616.4954432391,
            "unit": "iter/sec",
            "range": "stddev: 4.1492643131937107e-7",
            "extra": "mean: 1.4823236709368872 usec\nrounds: 188324"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 807587.2810346351,
            "unit": "iter/sec",
            "range": "stddev: 4.0020573349002147e-7",
            "extra": "mean: 1.2382562522763565 usec\nrounds: 198847"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271604.1650606773,
            "unit": "iter/sec",
            "range": "stddev: 7.284505600616285e-7",
            "extra": "mean: 3.6818286633292114 usec\nrounds: 73020"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7205395.622933932,
            "unit": "iter/sec",
            "range": "stddev: 3.3536610978279166e-8",
            "extra": "mean: 138.78488459635957 nsec\nrounds: 73828"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8754239.992067464,
            "unit": "iter/sec",
            "range": "stddev: 1.3202025625602495e-8",
            "extra": "mean: 114.23036161975642 nsec\nrounds: 88795"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1459755.8065113395,
            "unit": "iter/sec",
            "range": "stddev: 3.028328855207095e-7",
            "extra": "mean: 685.0460847899576 nsec\nrounds: 162049"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "f0ba430d9c8aefe1589b124ce44205e69dff424a",
          "message": "chore: 품질 게이트 baseline 업데이트 (macro 확장 반영)",
          "timestamp": "2026-04-04T14:51:15+09:00",
          "tree_id": "0c9fa2328d52b858eadf9fe356ea2342b6125dfa",
          "url": "https://github.com/eddmpython/dartlab/commit/f0ba430d9c8aefe1589b124ce44205e69dff424a"
        },
        "date": 1775281935134,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 541373.5017693219,
            "unit": "iter/sec",
            "range": "stddev: 5.209770779537803e-7",
            "extra": "mean: 1.84715357647131 usec\nrounds: 57333"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 664148.1200787204,
            "unit": "iter/sec",
            "range": "stddev: 5.021164985978826e-7",
            "extra": "mean: 1.505688218889292 usec\nrounds: 163881"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 530547.533027113,
            "unit": "iter/sec",
            "range": "stddev: 5.487321104069231e-7",
            "extra": "mean: 1.8848452546642909 usec\nrounds: 124301"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 677199.3284027871,
            "unit": "iter/sec",
            "range": "stddev: 4.1604303066925025e-7",
            "extra": "mean: 1.4766701000111098 usec\nrounds: 173883"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 817881.7603964002,
            "unit": "iter/sec",
            "range": "stddev: 3.7169594614827236e-7",
            "extra": "mean: 1.2226706211364013 usec\nrounds: 198847"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270817.662800621,
            "unit": "iter/sec",
            "range": "stddev: 6.746825397376116e-7",
            "extra": "mean: 3.6925213431747665 usec\nrounds: 80822"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7368397.438958621,
            "unit": "iter/sec",
            "range": "stddev: 1.3781115524971077e-8",
            "extra": "mean: 135.7147206409825 nsec\nrounds: 72380"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8551497.918035693,
            "unit": "iter/sec",
            "range": "stddev: 2.2235511814299165e-8",
            "extra": "mean: 116.93857726269589 nsec\nrounds: 87177"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1489849.2925267476,
            "unit": "iter/sec",
            "range": "stddev: 2.4993172499261877e-7",
            "extra": "mean: 671.2088296555316 nsec\nrounds: 185874"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "2477ec0f2af67d78324192206dfba122e0934309",
          "message": "style: ruff format 적용 (32개 파일)",
          "timestamp": "2026-04-04T15:18:53+09:00",
          "tree_id": "bf89d0e55beea9c96ee7ac9ebb451a2b197c1dfc",
          "url": "https://github.com/eddmpython/dartlab/commit/2477ec0f2af67d78324192206dfba122e0934309"
        },
        "date": 1775283594016,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 599376.4219277474,
            "unit": "iter/sec",
            "range": "stddev: 3.186551619332621e-7",
            "extra": "mean: 1.668400630081085 usec\nrounds: 58720"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 714460.2627205304,
            "unit": "iter/sec",
            "range": "stddev: 2.992874108015493e-7",
            "extra": "mean: 1.399657968649212 usec\nrounds: 112209"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 583246.0979644655,
            "unit": "iter/sec",
            "range": "stddev: 3.2046017543743254e-7",
            "extra": "mean: 1.7145421177955749 usec\nrounds: 102712"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 776109.3203910227,
            "unit": "iter/sec",
            "range": "stddev: 2.6246807696198273e-7",
            "extra": "mean: 1.2884782771274745 usec\nrounds: 138909"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 807170.1893652844,
            "unit": "iter/sec",
            "range": "stddev: 5.319858508595795e-7",
            "extra": "mean: 1.2388961004448722 usec\nrounds: 161839"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 299929.4873467556,
            "unit": "iter/sec",
            "range": "stddev: 3.8489949428479464e-7",
            "extra": "mean: 3.334116991450982 usec\nrounds: 67834"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 8522046.496605419,
            "unit": "iter/sec",
            "range": "stddev: 8.851000605751988e-9",
            "extra": "mean: 117.3427064025442 nsec\nrounds: 84289"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 9848372.26319868,
            "unit": "iter/sec",
            "range": "stddev: 8.053439985507072e-9",
            "extra": "mean: 101.53962231269345 nsec\nrounds: 84382"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1530830.0136404657,
            "unit": "iter/sec",
            "range": "stddev: 2.514759599210287e-7",
            "extra": "mean: 653.240393178535 nsec\nrounds: 133369"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "e11be6f45c8a2f5e20648994cdb9b5b68df0a8b0",
          "message": "refactor: 루트 vscode/ → ui/vscode/ 통합 (확장 본체 + webview)\n\n- vscode/ 전체를 ui/vscode/로 이동\n- webview 소스는 ui/vscode/webview/에 위치\n- CI vscode.yml, ops/vscode.md, .gitignore 경로 일괄 업데이트\n- vite.config.ts 빌드 출력: ../dist/webview (같은 패키지 내)\n- 빌드 검증 완료 (extension + webview)",
          "timestamp": "2026-04-04T15:34:00+09:00",
          "tree_id": "1ac1f4d624455ae03dc5acdd71ea29b0687f59bd",
          "url": "https://github.com/eddmpython/dartlab/commit/e11be6f45c8a2f5e20648994cdb9b5b68df0a8b0"
        },
        "date": 1775284510674,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 532992.8089858505,
            "unit": "iter/sec",
            "range": "stddev: 4.860304254529766e-7",
            "extra": "mean: 1.8761979207613422 usec\nrounds: 53577"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 642824.2619258877,
            "unit": "iter/sec",
            "range": "stddev: 4.5021656984794315e-7",
            "extra": "mean: 1.5556351233601882 usec\nrounds: 139998"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 512424.9948878357,
            "unit": "iter/sec",
            "range": "stddev: 5.090108734009136e-7",
            "extra": "mean: 1.9515051177760936 usec\nrounds: 132381"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 681601.3978154814,
            "unit": "iter/sec",
            "range": "stddev: 3.9111943408516623e-7",
            "extra": "mean: 1.4671331414591866 usec\nrounds: 178254"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 889323.6194257328,
            "unit": "iter/sec",
            "range": "stddev: 1.7429802112804665e-7",
            "extra": "mean: 1.1244500631229548 usec\nrounds: 172682"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 271789.4976570668,
            "unit": "iter/sec",
            "range": "stddev: 6.65252568074854e-7",
            "extra": "mean: 3.6793180333324 usec\nrounds: 73769"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7296828.020617588,
            "unit": "iter/sec",
            "range": "stddev: 1.2102830586937399e-8",
            "extra": "mean: 137.0458502207322 nsec\nrounds: 51369"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8882457.988854872,
            "unit": "iter/sec",
            "range": "stddev: 1.7287602816963497e-8",
            "extra": "mean: 112.58145000570052 nsec\nrounds: 89510"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1465558.2853690227,
            "unit": "iter/sec",
            "range": "stddev: 2.956801746174329e-7",
            "extra": "mean: 682.333831402825 nsec\nrounds: 159949"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "d841e3d9377d362b918ce1b194d5e2bd66f8704b",
          "message": "fix: UI 경로 잔여 참조 수정 + CHANGELOG v0.8.9 / vsce-0.2.2 작성\n\n- ops/ui.md: 디렉토리 구조/빌드 명령 ui/web, ui/vscode로 갱신\n- server/web.py: ui/build → ui/web/build\n- server/embed.py: ui/build → ui/web/build\n- CHANGELOG.md, docs/changelog.md: v0.8.9 항목 추가\n- ui/vscode/CHANGELOG.md: v0.2.2 항목 추가\n- credit: segments 중복 방지 + Executive Summary 개선",
          "timestamp": "2026-04-04T16:04:44+09:00",
          "tree_id": "7b9c477c5408744534c7b1a3b75be84318e21ba7",
          "url": "https://github.com/eddmpython/dartlab/commit/d841e3d9377d362b918ce1b194d5e2bd66f8704b"
        },
        "date": 1775286348193,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 533214.8415641739,
            "unit": "iter/sec",
            "range": "stddev: 4.868047739470664e-7",
            "extra": "mean: 1.8754166651973194 usec\nrounds: 57101"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 684563.4923303263,
            "unit": "iter/sec",
            "range": "stddev: 5.284540827616614e-7",
            "extra": "mean: 1.4607848814664284 usec\nrounds: 154036"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 533036.1859126615,
            "unit": "iter/sec",
            "range": "stddev: 5.249522182605552e-7",
            "extra": "mean: 1.876045241258444 usec\nrounds: 132556"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 694774.4724196213,
            "unit": "iter/sec",
            "range": "stddev: 4.029746103919002e-7",
            "extra": "mean: 1.439315979064977 usec\nrounds: 181819"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 821708.9623348471,
            "unit": "iter/sec",
            "range": "stddev: 3.852417040083477e-7",
            "extra": "mean: 1.216975895161892 usec\nrounds: 196890"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 266329.88756639964,
            "unit": "iter/sec",
            "range": "stddev: 6.74928392132725e-7",
            "extra": "mean: 3.754741944802145 usec\nrounds: 76255"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7186210.943175339,
            "unit": "iter/sec",
            "range": "stddev: 1.1693035210431367e-8",
            "extra": "mean: 139.15539188975362 nsec\nrounds: 72967"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8596523.60139941,
            "unit": "iter/sec",
            "range": "stddev: 1.106506226885401e-8",
            "extra": "mean: 116.32609254247986 nsec\nrounds: 85237"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1465558.921387785,
            "unit": "iter/sec",
            "range": "stddev: 2.775782288280473e-7",
            "extra": "mean: 682.3335352856832 nsec\nrounds: 178254"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "79f7a4b37e71e0105276af83fed7c565b97599b5",
          "message": "fix: credit metrics/publisher CRLF 정규화",
          "timestamp": "2026-04-04T16:05:23+09:00",
          "tree_id": "2cec245af3b978bbbbc0fd89d2a73a236b3f47ff",
          "url": "https://github.com/eddmpython/dartlab/commit/79f7a4b37e71e0105276af83fed7c565b97599b5"
        },
        "date": 1775286393919,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 542290.9942126151,
            "unit": "iter/sec",
            "range": "stddev: 4.813349561487964e-7",
            "extra": "mean: 1.844028410340762 usec\nrounds: 59239"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 669432.8332179816,
            "unit": "iter/sec",
            "range": "stddev: 4.745467383994251e-7",
            "extra": "mean: 1.4938018429615607 usec\nrounds: 133263"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 524059.16349006695,
            "unit": "iter/sec",
            "range": "stddev: 6.580780161507405e-7",
            "extra": "mean: 1.908181498707739 usec\nrounds: 106987"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 678737.9265283995,
            "unit": "iter/sec",
            "range": "stddev: 4.4149072434041274e-7",
            "extra": "mean: 1.4733227080955795 usec\nrounds: 140985"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 818683.1410587747,
            "unit": "iter/sec",
            "range": "stddev: 3.7651189757562557e-7",
            "extra": "mean: 1.2214737910771372 usec\nrounds: 174826"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 269142.718459436,
            "unit": "iter/sec",
            "range": "stddev: 6.854118787272942e-7",
            "extra": "mean: 3.7155008529451097 usec\nrounds: 65067"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7067881.593445993,
            "unit": "iter/sec",
            "range": "stddev: 2.72350568192082e-8",
            "extra": "mean: 141.48510933280127 nsec\nrounds: 73720"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8835294.405199107,
            "unit": "iter/sec",
            "range": "stddev: 1.1762572352328018e-8",
            "extra": "mean: 113.18241975180278 nsec\nrounds: 88881"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1465745.0400708972,
            "unit": "iter/sec",
            "range": "stddev: 2.695754284096504e-7",
            "extra": "mean: 682.2468933284813 nsec\nrounds: 178891"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "04a9f94fbed6b1aa17a54c82523120320577ebe1",
          "message": "fix: 보고서 5결함 수정 — 매출333.6조 + 부문DX/DS/SDC/Harman + 조사처리 + 번호연속 + 괴리강화\n\n매출: segComp→IS metricsHistory 실제 매출. '13억'→'333.6조'.\n부문: 최신 연도 자동 선택(2개+ 유효 데이터). DX 53%, DS 34%, SDC 9%, Harman 4%.\n조사: 종성 판별 '은/는' 자동. '삼성전자은(는)'→'삼성전자는'.\n번호: _sec() 카운터로 1~N 연속. 빈 섹션 자동 스킵.\n괴리: 0 notch 시 '일치' 이유 + 강점 3개 표시.",
          "timestamp": "2026-04-04T16:06:28+09:00",
          "tree_id": "0e89f74881842e5eab183ae0c6585f4d5c153d53",
          "url": "https://github.com/eddmpython/dartlab/commit/04a9f94fbed6b1aa17a54c82523120320577ebe1"
        },
        "date": 1775286449833,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 533034.7647442853,
            "unit": "iter/sec",
            "range": "stddev: 5.482269052298638e-7",
            "extra": "mean: 1.8760502431388948 usec\nrounds: 55729"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 656322.3640914243,
            "unit": "iter/sec",
            "range": "stddev: 4.766027309465888e-7",
            "extra": "mean: 1.523641513243791 usec\nrounds: 123840"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 521387.76553250384,
            "unit": "iter/sec",
            "range": "stddev: 5.695329627515206e-7",
            "extra": "mean: 1.9179583145352095 usec\nrounds: 126519"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 667380.1041878319,
            "unit": "iter/sec",
            "range": "stddev: 4.4320492747886524e-7",
            "extra": "mean: 1.498396481592675 usec\nrounds: 188324"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 802810.3742226132,
            "unit": "iter/sec",
            "range": "stddev: 3.6237479804503576e-7",
            "extra": "mean: 1.2456241624534707 usec\nrounds: 193424"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 267732.29175929574,
            "unit": "iter/sec",
            "range": "stddev: 6.428910276229014e-7",
            "extra": "mean: 3.7350742916698607 usec\nrounds: 68083"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7297549.210417098,
            "unit": "iter/sec",
            "range": "stddev: 1.2194948980649783e-8",
            "extra": "mean: 137.03230648619962 nsec\nrounds: 73341"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8725944.485586934,
            "unit": "iter/sec",
            "range": "stddev: 1.2459060979573867e-8",
            "extra": "mean: 114.6007749249091 nsec\nrounds: 87944"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1432035.1082553586,
            "unit": "iter/sec",
            "range": "stddev: 3.259501885220816e-7",
            "extra": "mean: 698.3069019992779 nsec\nrounds: 157679"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "f4f4870d87ac6b403be2f6a5ab2b9173dde57074",
          "message": "publish: 4개사 보고서 최종 퀄리티 — hook+부문+조사+번호+괴리 완성\n\n삼성전자: DX 53%/DS 34%/SDC 9%/Harman 4%. 매출 333.6조.\nSK하이닉스: 매출 97.1조. 단일 사업 구조.\nNAVER: 핀테크 45%/클라우드 31%/콘텐츠 24%. 매출 12.0조.\nLG: 지주사. 매출 6,154억. 건전도 94/100.",
          "timestamp": "2026-04-04T16:09:30+09:00",
          "tree_id": "c004a0ce0f159c3a68f4b462478d5e889200dabb",
          "url": "https://github.com/eddmpython/dartlab/commit/f4f4870d87ac6b403be2f6a5ab2b9173dde57074"
        },
        "date": 1775286647370,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 465918.4294132004,
            "unit": "iter/sec",
            "range": "stddev: 5.531596963515229e-7",
            "extra": "mean: 2.1462984438272747 usec\nrounds: 52757"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 662665.2750895283,
            "unit": "iter/sec",
            "range": "stddev: 5.209951716058162e-7",
            "extra": "mean: 1.5090574949244122 usec\nrounds: 109314"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 523015.37496054015,
            "unit": "iter/sec",
            "range": "stddev: 5.520484459554914e-7",
            "extra": "mean: 1.9119896811359451 usec\nrounds: 117842"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 663902.8156227306,
            "unit": "iter/sec",
            "range": "stddev: 4.23022128663578e-7",
            "extra": "mean: 1.5062445533718896 usec\nrounds: 144447"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 812896.9120028806,
            "unit": "iter/sec",
            "range": "stddev: 3.7810826008778107e-7",
            "extra": "mean: 1.2301682848519129 usec\nrounds: 186220"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 268244.46522314963,
            "unit": "iter/sec",
            "range": "stddev: 6.481053809459049e-7",
            "extra": "mean: 3.7279427151203697 usec\nrounds: 65794"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7446014.953259169,
            "unit": "iter/sec",
            "range": "stddev: 2.7912199101221932e-8",
            "extra": "mean: 134.30002575569546 nsec\nrounds: 73769"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8687445.189955963,
            "unit": "iter/sec",
            "range": "stddev: 1.4404087717908666e-8",
            "extra": "mean: 115.10863989751043 nsec\nrounds: 86942"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1462962.2125844723,
            "unit": "iter/sec",
            "range": "stddev: 3.028135847160082e-7",
            "extra": "mean: 683.5446543991028 nsec\nrounds: 123840"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "committer": {
            "email": "206024502+eddmpython@users.noreply.github.com",
            "name": "eddmpython",
            "username": "eddmpython"
          },
          "distinct": true,
          "id": "ad79ea50ec48327afcb7852642ead857b95716e7",
          "message": "feat: 보고서 발행 수준 달성 — 재무하이라이트+인과서사+mermaid+AI선택\n\n1. 재무 하이라이트 박스: 매출/영업이익/EBITDA/OCF/순차입금/D/EBITDA + YoY.\n2. Executive Summary 인과: '매출→이익률→OCF→순현금→등급' 자동 서술.\n3. 부문 테이블: 금액(IS매출×비중) + 비중 3열.\n4. Mermaid 인과도: graph LR 매출→이익률→OCF→부채→등급.\n5. AI 선택적: useAI=False 기본 (재현 가능한 기계 서사).",
          "timestamp": "2026-04-04T16:37:24+09:00",
          "tree_id": "ea4e214c6df957891b882538626b60e967ce8041",
          "url": "https://github.com/eddmpython/dartlab/commit/ad79ea50ec48327afcb7852642ead857b95716e7"
        },
        "date": 1775288308661,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_20q",
            "value": 533987.4772343,
            "unit": "iter/sec",
            "range": "stddev: 4.984566766641714e-7",
            "extra": "mean: 1.8727030925506623 usec\nrounds: 56297"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_sparse",
            "value": 664484.6464825387,
            "unit": "iter/sec",
            "range": "stddev: 4.6623086727371974e-7",
            "extra": "mean: 1.504925667272401 usec\nrounds: 134880"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getTTM_annualize",
            "value": 529906.3784969071,
            "unit": "iter/sec",
            "range": "stddev: 5.253290109164593e-7",
            "extra": "mean: 1.8871258029324456 usec\nrounds: 112398"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_20q",
            "value": 670033.0316555985,
            "unit": "iter/sec",
            "range": "stddev: 4.1756396857294403e-7",
            "extra": "mean: 1.49246373351039 usec\nrounds: 168351"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_getLatest_sparse",
            "value": 813698.1770455213,
            "unit": "iter/sec",
            "range": "stddev: 3.767104887994727e-7",
            "extra": "mean: 1.2289569132757887 usec\nrounds: 158680"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_revenueGrowth3Y",
            "value": 270424.3575322169,
            "unit": "iter/sec",
            "range": "stddev: 7.237774772346408e-7",
            "extra": "mean: 3.6978917473470023 usec\nrounds: 62271"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_normal",
            "value": 7326623.618118825,
            "unit": "iter/sec",
            "range": "stddev: 1.2446314221098536e-8",
            "extra": "mean: 136.48851805721102 nsec\nrounds: 73073"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safeDiv_zeroDenom",
            "value": 8796981.381806664,
            "unit": "iter/sec",
            "range": "stddev: 1.149136755544007e-8",
            "extra": "mean: 113.67535710239584 nsec\nrounds: 88098"
          },
          {
            "name": "tests/benchmarks/bench_core.py::test_safePct_normal",
            "value": 1448256.8529550042,
            "unit": "iter/sec",
            "range": "stddev: 2.774547575207991e-7",
            "extra": "mean: 690.4852533303144 nsec\nrounds: 158680"
          }
        ]
      }
    ]
  }
}