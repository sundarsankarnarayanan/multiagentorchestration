# AI Agent System - Makefile
# ============================

.PHONY: help setup install run start stop ollama-start ollama-pull ollama-status test lint format clean

# Default Python
PYTHON := python3
VENV := venv
BIN := $(VENV)/bin
PORT := 8001

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "AI Agent System - Available Commands"
	@echo "====================================="
	@echo ""
	@echo "$(YELLOW)First-time setup:$(NC)"
	@echo "  make setup-all     - Complete setup (venv + deps + Ollama + model)"
	@echo ""
	@echo "$(YELLOW)Quick start (after setup):$(NC)"
	@echo "  make ollama-start  - Start Ollama (Terminal 1)"
	@echo "  make run           - Start the app (Terminal 2)"
	@echo "  -- OR --"
	@echo "  make start-all     - Start both in one command"
	@echo ""
	@echo "$(YELLOW)All commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================
# Setup & Installation
# ============================================

setup: ## Create virtual environment and install all dependencies
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	@echo ""
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "Activate venv with: source $(VENV)/bin/activate"

install: ## Install dependencies (assumes venv is active)
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install pytest pytest-asyncio mypy flake8 black

# ============================================
# Running the Application
# ============================================

run: ## Start the web server
	@echo "$(GREEN)Starting AI Agent System...$(NC)"
	@echo "URL: http://localhost:$(PORT)"
	@echo "Press Ctrl+C to stop"
	@echo ""
	$(BIN)/python web/server.py

start: run ## Alias for 'run'

run-dev: ## Start with auto-reload (development mode)
	@echo "$(GREEN)Starting in development mode...$(NC)"
	$(BIN)/uvicorn web.server:app --reload --host 0.0.0.0 --port $(PORT)

# ============================================
# Ollama (Local LLM)
# ============================================

ollama-install: ## Install Ollama (macOS via Homebrew)
	@echo "$(GREEN)Installing Ollama...$(NC)"
	@if command -v ollama >/dev/null 2>&1; then \
		echo "$(YELLOW)Ollama already installed$(NC)"; \
		ollama --version; \
	else \
		if [ "$$(uname)" = "Darwin" ]; then \
			echo "Installing via Homebrew..."; \
			brew install ollama; \
		elif [ "$$(uname)" = "Linux" ]; then \
			echo "Installing via install script..."; \
			curl -fsSL https://ollama.ai/install.sh | sh; \
		else \
			echo "$(RED)Please install manually from: https://ollama.ai$(NC)"; \
			exit 1; \
		fi \
	fi
	@echo ""
	@echo "$(GREEN)Ollama installed! Next steps:$(NC)"
	@echo "  1. make ollama-start   (in a separate terminal)"
	@echo "  2. make ollama-pull    (download the model)"
	@echo "  3. make run            (start the app)"

ollama-start: ## Start Ollama server
	@echo "$(GREEN)Starting Ollama...$(NC)"
	@if command -v ollama >/dev/null 2>&1; then \
		ollama serve; \
	else \
		echo "$(RED)Ollama not installed. Run: make ollama-install$(NC)"; \
		exit 1; \
	fi

ollama-pull: ## Pull the default LLM model (llama2)
	@echo "$(GREEN)Pulling llama2 model (~4GB)...$(NC)"
	@if command -v ollama >/dev/null 2>&1; then \
		ollama pull llama2; \
	else \
		echo "$(RED)Ollama not installed. Run: make ollama-install$(NC)"; \
		exit 1; \
	fi

ollama-pull-mistral: ## Pull Mistral model (alternative, ~4GB)
	@echo "$(GREEN)Pulling mistral model...$(NC)"
	ollama pull mistral

ollama-pull-small: ## Pull smaller/faster models for testing
	@echo "$(GREEN)Pulling smaller models...$(NC)"
	ollama pull phi
	@echo "$(GREEN)Phi model ready (~1.6GB, faster)$(NC)"

ollama-status: ## Check Ollama status and list models
	@echo "$(GREEN)Checking Ollama status...$(NC)"
	@if command -v ollama >/dev/null 2>&1; then \
		echo "Ollama installed: $$(ollama --version 2>/dev/null || echo 'yes')"; \
	else \
		echo "$(RED)Ollama not installed. Run: make ollama-install$(NC)"; \
	fi
	@echo ""
	@curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); models=data.get('models',[]); print('Server: Running'); print('Models:', ', '.join([m['name'] for m in models]) if models else 'None (run: make ollama-pull)')" 2>/dev/null || echo "$(RED)Server: Not running (run: make ollama-start)$(NC)"

ollama-setup: ollama-install ## Full Ollama setup: install + pull model
	@echo ""
	@echo "$(YELLOW)Starting Ollama server in background...$(NC)"
	@ollama serve > /dev/null 2>&1 & sleep 3
	@echo "$(GREEN)Pulling llama2 model...$(NC)"
	@ollama pull llama2
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)Ollama setup complete!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "To start the app, run: make run"
	@echo ""
	@echo "$(YELLOW)Note: Ollama server is running in background.$(NC)"
	@echo "To stop it: pkill ollama"

# ============================================
# Full Stack (Ollama + Server)
# ============================================

start-all: ## Start Ollama in background and then the server
	@echo "$(GREEN)Starting full stack...$(NC)"
	@if ! command -v ollama >/dev/null 2>&1; then \
		echo "$(RED)Ollama not installed. Run: make ollama-install$(NC)"; \
		exit 1; \
	fi
	@if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "Starting Ollama in background..."; \
		ollama serve > /dev/null 2>&1 & \
		sleep 3; \
	else \
		echo "Ollama already running"; \
	fi
	@$(MAKE) run

# ============================================
# First-Time Setup (Everything)
# ============================================

setup-all: ## Complete first-time setup: venv + deps + Ollama + model
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)Complete First-Time Setup$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@$(MAKE) setup
	@echo ""
	@$(MAKE) ollama-install
	@echo ""
	@echo "$(YELLOW)Starting Ollama server...$(NC)"
	@ollama serve > /dev/null 2>&1 & sleep 3
	@echo "$(GREEN)Pulling llama2 model (this may take a few minutes)...$(NC)"
	@ollama pull llama2
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "To start the application:"
	@echo "  Terminal 1: make ollama-start"
	@echo "  Terminal 2: make run"
	@echo ""
	@echo "Or in one command: make start-all"

# ============================================
# Testing
# ============================================

test: ## Run all tests
	$(BIN)/pytest tests/ -v

test-unit: ## Run unit tests only
	$(BIN)/pytest tests/unit/ -v

test-integration: ## Run integration tests
	$(BIN)/pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	$(BIN)/pytest tests/ -v --cov=. --cov-report=html

# ============================================
# Code Quality
# ============================================

lint: ## Run linting checks
	$(BIN)/flake8 agents/ models/ workflows/ web/ rag/ --max-line-length=120

format: ## Format code with black
	$(BIN)/black agents/ models/ workflows/ web/ rag/

typecheck: ## Run type checking with mypy
	$(BIN)/mypy agents/ models/ workflows/ --ignore-missing-imports

check: lint typecheck ## Run all code quality checks

# ============================================
# Database & Storage
# ============================================

inspect-db: ## Inspect the vector store database
	$(BIN)/python scripts/inspect_vector_store.py

clear-db: ## Clear the vector store (ChromaDB)
	@echo "$(YELLOW)Clearing vector store...$(NC)"
	rm -rf ./chroma_db
	@echo "$(GREEN)Vector store cleared$(NC)"

# ============================================
# Examples
# ============================================

example-basic: ## Run basic workflow example
	$(BIN)/python examples/basic_workflow.py

example-custom: ## Run custom workflow example
	$(BIN)/python examples/custom_workflow.py

example-ocr: ## Run OCR example
	$(BIN)/python example_ocr.py

# ============================================
# Cleanup
# ============================================

clean: ## Remove build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "$(GREEN)Cleaned!$(NC)"

clean-all: clean ## Remove venv and all generated files
	rm -rf $(VENV)
	rm -rf ./chroma_db
	@echo "$(GREEN)Full cleanup complete$(NC)"

# ============================================
# Docker (optional)
# ============================================

docker-build: ## Build Docker image
	docker build -t ai-agent-system .

docker-run: ## Run Docker container
	docker run -p $(PORT):$(PORT) ai-agent-system

# ============================================
# Info
# ============================================

info: ## Show project info and status
	@echo "$(GREEN)AI Agent System$(NC)"
	@echo "================"
	@echo "Python:  $(shell $(PYTHON) --version 2>&1)"
	@echo "Venv:    $(VENV)/"
	@echo "Port:    $(PORT)"
	@echo ""
	@echo "Endpoints:"
	@echo "  Web UI:    http://localhost:$(PORT)"
	@echo "  WebSocket: ws://localhost:$(PORT)/ws"
	@echo "  Chat:      ws://localhost:$(PORT)/chat"
	@echo "  Health:    http://localhost:$(PORT)/health"
	@echo ""
	@$(MAKE) ollama-status
