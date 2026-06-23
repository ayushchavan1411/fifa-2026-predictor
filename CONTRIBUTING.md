# Contributing to FIFA World Cup 2026 Predictor

We welcome contributions! Please follow these guidelines:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```
4. Run tests locally: `pytest tests/`
5. Commit with clear messages following [Conventional Commits](https://www.conventionalcommits.org/).
6. Push and open a merge request.

All code must pass the CI pipeline (lint, format, typecheck, deadcode, security, test).
