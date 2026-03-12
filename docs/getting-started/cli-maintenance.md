# CLI Maintenance

DartLab CLI is maintained as a package under `src/dartlab/cli/`, not as a single file.

## Rules

- Add new commands in `src/dartlab/cli/commands/<name>.py`.
- Each command module must separate parser registration from execution.
- Use `configure_parser(subparsers)` to define arguments and `run(args)` to execute.
- Keep shared constants and provider lists in `src/dartlab/cli/context.py`.
- Keep shared output and environment logic in `src/dartlab/cli/services/`.
- Raise `CLIError` for user-facing failures instead of printing ad-hoc errors in commands.
- Keep stdout for successful data output and stderr for warnings/errors/deprecations.
- Preserve stable exit codes: `0` success, `1` runtime failure, `2` usage error, `130` interrupted.
- Preserve public command names unless there is an explicit migration plan.
- Deprecated aliases must print a migration message and have a test.
- Every new command needs at least one parser test and one execution or error-path test.

## Current Layout

```text
src/dartlab/cli/
  __init__.py
  main.py
  parser.py
  context.py
  commands/
  services/
```

## Change Policy

- Prefer extending the existing command tree over adding ad-hoc helper scripts.
- Keep `argparse` as the default framework unless there is a deliberate CLI UX rewrite.
- When command output format changes, update both tests and user-facing docs in the same change.
- Hide deprecated aliases from top-level help once migration is in place, but keep them executable until removal.

## Release Gates

- CLI release changes must pass parser/unit tests and subprocess E2E smoke tests.
- Public help output and exit codes are treated as compatibility contracts.
- `pyproject.toml` script entrypoint must continue to target `dartlab.cli.main:main`.
- New deprecations must be documented in `CHANGELOG.md` and reflected in help behavior tests.
