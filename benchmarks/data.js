window.BENCHMARK_DATA = {
  "lastUpdate": 1775054012312,
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
      }
    ]
  }
}