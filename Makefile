# Makefile for ANM Home Assistant integration

.PHONY: help install-deps test test-api test-unit lint format clean

# Default target
help: ## Show this help message
	@echo '$(tput bold)ANM Home Assistant Integration$(tput sgr0)'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"}; {printf "  %-20s %s\n", $$1, $$2}' 		$(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?##' | sort
	@echo ''
	@echo 'Usage: make [target]'

# Install dependencies
install-deps: ## Install dependencies using UV
	@echo "Installing dependencies..."
	uv sync

# Run all tests
test: ## Run all tests
	@echo "Running all tests..."
	pytest tests/ -v

# Run only API tests
test-api: ## Run only API tests
	@echo "Running API tests..."
	pytest tests/test_api.py -v

# Run only unit tests
test-unit: ## Run only unit tests (coordinator, config_flow)
	@echo "Running unit tests..."
	pytest tests/test_config_flow.py tests/test_coordinator.py -v

# Run tests with coverage
test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	pytest tests/ --cov=custom_components/anm --cov-report=html --cov-report=term

# Format code with ruff
format: ## Format code with ruff
	@echo "Formatting code..."
	ruff format custom_components/ tests/

# Sort imports with isort
sort-imports: ## Sort imports with isort
	@echo "Sorting imports..."
	isort custom_components/ tests/

# Lint code with ruff
lint: ## Lint code with ruff
	@echo "Linting code..."
	ruff check custom_components/ tests/

# Type check with mypy
type-check: ## Type check with mypy
	@echo "Type checking..."
	mypy custom_components/ tests/

# Clean temporary files
clean: ## Clean temporary files
	@echo "Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .coverage -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".DS_Store" -delete

# Full check: format + lint + type-check + test
check: format lint type-check test ## Run format, lint, type-check and tests
	@echo "Running full check..."

# Development setup
setup: install-deps ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run tests with: make test"
