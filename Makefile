UV = uv
HATCH = hatch


.PHONY: dev
dev: ## 🚀 Configure Environment (editable install)
	@echo "🔹 Building environments..."
	hatch env create default
	hatch env create gtk
	@echo "🔹 Install Packages in Edit Mode..."
	$(HATCH) run dev
	@echo "✅ Install Completed. Use 'make run-gtk'"


.PHONY: shell
shell: ## 🐚 Open Shell'
	$(HATCH) shell


.PHONY: run
run: ## ▶️ Execute using GTK
	@echo "🔹 Execute GTK"
	$(HATCH) run run

# =============================================================================
# Dependencies
# =============================================================================

.PHONY: install-gtk
install-gtk: ## 🎨 Install Dependences in GTK
	$(UV) pip install ".[gtk]"

.PHONY: install-dev
install-dev: ## 💻 Install Development Dependencies
	$(UV) pip install ".[dev]"

# =============================================================================
# Test And Quality
# =============================================================================

.PHONY: test
test: ## 🧪 Test
	$(HATCH) run test

.PHONY: cov
cov: ## 📊 Coverage
	$(HATCH) run cov

.PHONY: lint
lint: ## 🔍 Lint with ruff
	$(HATCH) run lint

.PHONY: fix
fix: ## ✨ Fix Code
	$(HATCH) run fix

.PHONY: type-check
type-check: ## 🧠 MyPy
	$(HATCH) run type-check

.PHONY: check
check: lint type-check ## 🔎 Complete Check

# =============================================================================
# LIMPIEZA
# =============================================================================

.PHONY: clean
clean: ## 🧹 Clean Code
	find . -type d -name "__pycache__" -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ .mypy_cache/ .coverage coverage.xml htmlcov/ .ruff_cache/
	rm -rf build/ dist/ *.egg-info/

.PHONY: clean-env
clean-env: clean ## 🧽 Clear Environments
	$(HATCH) env prune

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help: ## ❓ Show Help
	@echo "🛠️  health-control-chackra - Comandos disponibles"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Default
.PHONY: default
default: help