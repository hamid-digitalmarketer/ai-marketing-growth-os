# Contributing

Thanks for considering contributing to `ai-marketing-growth-os`. This project follows the
standards of the AI Marketing Engineer portfolio — please read
[the shared standards](https://github.com/hamid-digitalmarketer/ai-marketing-portfolio-meta/blob/main/docs/standards.md)
first.

## Development setup

```bash
pip install -e ../ai-marketing-shared
pip install -e ".[dev]"
```

## Commands

```bash
ruff check .                 # lint
mypy                         # type-check (configured in pyproject.toml)
pytest                       # unit tests + coverage (>= 80% on core modules)
pytest evaluation/ -q        # evaluation suite
python -m demo.run_demo      # zero-API-key demo pipeline
```

## Commit style

Conventional Commits:

- `feat: ...` new capability
- `fix: ...` bug fix
- `test: ...` tests only
- `docs: ...` documentation only
- `chore: ...` tooling / maintenance
- `refactor: ...` behavior-preserving change

## Pull request checklist

- [ ] `ruff check .` clean
- [ ] `mypy` clean
- [ ] `pytest` passes with coverage above threshold
- [ ] Evaluation suite passes
- [ ] Demo mode still runs with `AI_MARKETING_PROVIDER=mock`
- [ ] CHANGELOG updated for user-facing changes

## Code of conduct

Be respectful, constructive, and evidence-based — same standard we apply to agents.
