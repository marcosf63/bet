# AGENTS.md

This file provides guidance to agentic coding agents working in this repository.

## Build/Lint/Test Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

If you prefer `uv`, keep `requirements.txt` in sync and use:
```bash
uv venv
uv pip install -r requirements.txt
uv pip install -e .
```

### Testing Commands
```bash
# Run all tests
pytest

# Run single test file
pytest tests/test_core_models.py

# Run single test function
pytest tests/test_core_models.py::TestPartida::test_partida_creation

# Run tests with coverage
pytest --cov=bet --cov-report=term-missing

# Run tests with coverage HTML report
pytest --cov=bet --cov-report=html
```

### Code Quality Commands
```bash
# Format code with Black
black bet/ tests/

# Lint with Ruff
ruff check bet/ tests/

# Auto-fix what Ruff can
ruff check --fix bet/ tests/

# Type checking with MyPy
mypy bet/

# Run all quality checks together
black bet/ tests/ && ruff check bet/ tests/ && mypy bet/
```

### Build Commands
```bash
# Build package
python -m build

# Install build dependencies
pip install build
```

## Code Style Guidelines

### Import Organization
- Use `isort` rules (configured via Ruff)
- Standard library imports first
- Third-party imports second
- Local application imports last
- Use absolute imports for local modules: `from bet.core.models import Partida`

### Type Hints
- Use type hints for all function parameters and return values
- Use `|` syntax for union types (Python 3.10+): `str | None`
- Import from `typing` for complex types (prefer built-ins like `list[...]` / `dict[...]` when possible)
- Use `TYPE_CHECKING` for imports that are only needed for type hints

### Naming Conventions
- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE` (module-level)
- **Private members**: Leading underscore `_private_method`
- **Pydantic models**: `PascalCase` with descriptive names

### Error Handling
- Prefer domain-specific exceptions (add under `bet.core.exceptions` when it exists)
- Document non-obvious exceptions in docstrings
- Use specific exception types, avoid bare `except:`
- Log errors appropriately when handling exceptions

### Documentation
- Use triple quotes for docstrings
- Keep docstrings short and practical; Google-style is fine
- Document complex algorithms and business logic

### Pydantic Models
- All models must inherit from `BaseModel`
- Use proper field types with validation
- Implement `__eq__` and `__hash__` for models that represent unique entities
- Use `Optional` for fields that may be None

### CLI Commands
- All CLI commands must be in `bet.cli.commands` package
- Use Typer for CLI framework
- Commands should be named descriptively (e.g., `mday_command`, `fav_command`)
- Use Rich for formatted output
- Include proper help text and parameter descriptions

### File Structure
- Keep modules focused and cohesive
- Maximum 200-300 lines per module when possible
- Use `__init__.py` to control package exports
- Follow the established package structure: `core/`, `cli/`, `services/`, `analysis/`, `storage/`, `utils/`

### Testing
- Test files must be named `test_*.py` in the `tests/` directory
- Test classes must be named `Test*`
- Test functions must be named `test_*`
- Use descriptive test names that explain what is being tested
- Mock external dependencies (APIs, databases)
- Test both success and failure cases

### Configuration
- Use Dynaconf for configuration management
- Store configuration in `settings.toml`
- Use environment variables for sensitive data
- Never commit secrets or API keys to the repository

### Database Operations
- Use the `BettingDatabase` class for all database operations
- Always close database connections properly
- Use context managers when possible
- Handle database errors gracefully

### External APIs
- Use the service classes in `bet.services/` for external API calls
- Handle API errors and rate limits appropriately
- Cache responses when appropriate
- Use proper authentication methods

### Performance Considerations
- Use generators for large datasets
- Optimize database queries
- Cache expensive computations
- Profile code before optimizing

### Security
- Never log sensitive data (passwords, API keys)
- Validate all user inputs
- Use proper authentication for external services
- Follow principle of least privilege

## Project Notes
- Python >= 3.10; formatting/linting config lives in `pyproject.toml`
- CLI entry point: `bet = bet.cli.main:main`
