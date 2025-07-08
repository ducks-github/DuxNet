# DuxOS Testing Infrastructure

## Overview

This directory contains the comprehensive testing suite for the DuxOS project, ensuring code quality, reliability, and performance.

## Test Types

### Unit Tests
Located in `tests/wallet/`, `tests/tasks/`, etc.
- Validate individual module functionality
- Test edge cases and error handling
- Ensure method-level correctness

### Integration Tests
Located in `tests/integration/`
- Test interactions between modules
- Validate system-wide behavior
- Simulate real-world usage scenarios

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Install the project in editable mode
pip install -e .
```

### Test Execution

```bash
# Run all tests
pytest tests/

# Run tests with coverage report
pytest --cov=duxos tests/

# Run tests for a specific module
pytest tests/wallet/

# Generate detailed HTML coverage report
pytest --cov=duxos --cov-report=html tests/
```

## Test Coverage

- Aim for >90% code coverage
- Focus on critical paths and edge cases
- Use `pytest-cov` for coverage analysis

## Best Practices

1. Write tests before or alongside code implementation
2. Test both successful and failure scenarios
3. Use mock objects for external dependencies
4. Keep tests independent and isolated
5. Use descriptive test names

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Merges to main branch
- Scheduled intervals

## Debugging

- Use `pytest -v` for verbose output
- Use `pytest -pdb` to drop into debugger on test failure
- Utilize `print()` or logging for additional insights

## Contributing

1. Add tests for new features
2. Update existing tests when changing functionality
3. Ensure all tests pass before submitting a PR

## Tools

- `pytest`: Test runner
- `pytest-cov`: Coverage reporting
- `mypy`: Static type checking
- `black`: Code formatting
- `flake8`: Linting 