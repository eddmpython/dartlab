window.BENCHMARK_DATA = {
  "lastUpdate": 1775029725047,
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
      }
    ]
  }
}