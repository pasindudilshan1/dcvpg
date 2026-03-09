# Contributing to DCVPG

Thank you for your interest in contributing to DCVPG! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/your-org/dcvpg.git
cd dcvpg

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install in editable mode with all extras
pip install -e "dcvpg/[all]"
pip install pytest pytest-asyncio pytest-cov ruff httpx
```

## Running Tests

```bash
# Unit tests (no external services required)
pytest dcvpg/tests/unit/ -v

# Integration tests (requires PostgreSQL)
docker-compose -f dcvpg/infra/docker-compose.yml up -d db
pytest dcvpg/tests/integration/ -v -m integration

# Performance tests
pytest dcvpg/tests/perf/ -v -m perf -s
```

## Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check dcvpg/        # check
ruff check dcvpg/ --fix  # auto-fix
ruff format dcvpg/       # format
```

## Making a Contribution

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Write tests** for any new behaviour. PRs without tests may be declined.

3. **Run the full test suite** before opening a PR:
   ```bash
   pytest dcvpg/tests/unit/ -v
   ruff check dcvpg/
   ```

4. **Open a Pull Request** with:
   - A clear description of the change and motivation
   - Link to any related issue
   - Test results

## Adding a Connector

1. Copy `dcvpg/templates/custom_connector.py.template`
2. Implement `connect()`, `fetch_batch()`, and `fetch_sample()`
3. Register it in `engine/connectors/__init__.py`
4. Add unit tests in `tests/unit/test_connectors.py`
5. Add documentation in `docs/connectors.md`

## Adding a Rule

1. Copy `dcvpg/templates/custom_rule.py.template`
2. Implement `validate()` in a class extending `BaseRule`
3. Add tests in `tests/unit/test_validator.py`
4. Document in `docs/custom_rules.md`

## Reporting Issues

Please open a GitHub Issue with:
- DCVPG version (`dcvpg --version`)
- Python version
- Steps to reproduce
- Expected vs actual behaviour
- Relevant logs or tracebacks

## Security Issues

For security vulnerabilities, please **do not** open a public issue. Email security@your-org.com instead.
