window.BENCHMARK_DATA = {
  "lastUpdate": 1775096847583,
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
      }
    ]
  }
}