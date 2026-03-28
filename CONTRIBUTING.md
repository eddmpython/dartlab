# Contributing to DartLab

Thank you for your interest in contributing! 기여에 관심을 가져주셔서 감사합니다.

## Getting Started

```bash
git clone https://github.com/eddmpython/dartlab.git
cd dartlab
uv pip install -e ".[all]"
pre-commit install
```

## Development Workflow

1. Create a branch from `master`.
2. Make your changes.
3. Run checks locally:
   ```bash
   ruff check src/dartlab/ tests/
   ruff format --check src/dartlab/ tests/
   pytest tests/ -m "unit" -v --tb=short
   ```
4. Open a pull request against `master`.

## Testing

DartLab uses pytest with three test tiers:

| Marker | Scope | CI |
|--------|-------|----|
| `unit` | Pure logic, no data loading | Yes |
| `integration` | Needs one Company loaded | Selective |
| `heavy` | Large data, run alone | No |

Run unit tests first -- they are fast and catch most issues:

```bash
pytest tests/ -m "unit" -v --tb=short
```

## Code Style

- **Linter/Formatter:** ruff (config in `pyproject.toml`)
- **Type checker:** pyright (basic mode)
- Pre-commit hooks handle formatting and linting automatically.

## What to Contribute

- Bug fixes with a failing test
- New financial analysis functions
- Documentation improvements (English or Korean)
- Performance optimizations
- Additional provider support

## Reporting Bugs

Please use the [Bug Report](https://github.com/eddmpython/dartlab/issues/new?template=bug_report.yml) template.

## Security Issues

See [SECURITY.md](SECURITY.md) for responsible disclosure.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
