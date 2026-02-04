# Ecosystem Package Development Workflow

This guide documents the generic workflow for developing spoke packages while testing them against real documentation in the hub repository.

## Overview

### What is the Hub-Spoke Ecosystem Model?

The hub-spoke model separates concerns between:

| Component | Purpose |
|-----------|---------|
| **Hub** | Meta-documentation, ecosystem ADRs, real docs for integration testing |
| **Spoke** | Reusable package with focused capability |

See {term}`ADR-26020` for the complete hub-spoke architecture documentation.

### Why Extract Packages?

1. **Reusability:** Logic can be shared across multiple repos
2. **Single Source of Truth:** Bug fixes propagate via version updates
3. **Clear Ownership:** Each package has its own release cycle
4. **Community Potential:** Packages can be open-sourced independently

See {term}`ADR-26012` for the founding decision to extract packages.

## How Editable Installs Work

This is the critical concept that makes seamless ecosystem development possible.

### The Key Insight

When you run `uv pip install -e "../spoke-package"`, Python doesn't copy source code into `.venv/`. Instead, it creates **symlinks** pointing to the actual source files.

```
hub/.venv/lib/python3.13/site-packages/spoke_package/
  → symlink to → ../spoke-package/src/spoke_package/
```

### Why This Matters

| Without editable install | With editable install |
|--------------------------|----------------------|
| Edit spoke → reinstall → test | Edit spoke → test (instant) |
| Two separate environments | Single unified environment |
| Easy to forget reinstall step | Changes always reflected |

**Edit in spoke, test in hub, changes reflected instantly.**

## Development Workflow (Step-by-Step)

### Step 1: Create Spoke Repository

```bash
mkdir ~/projects/spoke-package
cd ~/projects/spoke-package
git init
```

Package structure:

```
spoke-package/
├── pyproject.toml
├── src/spoke_package/
│   └── __init__.py
├── tests/
└── ARCHITECTURE.md
```

### Step 2: Initialize the Repository

```bash
cd ~/projects/spoke-package

cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.venv/
dist/
*.egg-info/
.pytest_cache/
.coverage
EOF

uv sync
uv pip install -e ".[dev]"
uv run pytest tests/ -v
```

### Step 3: Push to GitHub

```bash
gh repo create spoke-package --public --source=. --push
```

### Step 4: Configure Editable Install in Hub

Add to hub's `pyproject.toml`:

```toml
[tool.uv.sources]
spoke-package = { path = "../spoke-package", editable = true }
```

Install:

```bash
cd /path/to/hub
uv pip install -e "../spoke-package[dev]"
```

### Step 5: Develop and Test

Edit spoke source, test in hub (changes reflected instantly):

```bash
cd /path/to/hub
uv run python -c "from spoke_package import SomeClass; print('works!')"
uv run pytest tools/tests/test_integration.py
```

### Step 6: Install from GitHub (for consumers)

```bash
uv add "spoke-package @ git+https://github.com/org/spoke-package.git"
```

Or pin a specific version:

```bash
uv add "spoke-package @ git+https://github.com/org/spoke-package.git@v0.1.0"
```

## Claude Code Workflow

A single Claude Code session can access both repositories using absolute paths.

### Path Reference

| Task | Path |
|------|------|
| Edit hub files | `/absolute/path/to/hub/...` |
| Edit spoke files | `/absolute/path/to/spoke-package/...` |
| Run hub tests | `uv run pytest tools/tests/` (from hub CWD) |
| Run spoke tests | `uv run pytest ../spoke-package/tests/` |

### Example Session

```
User: "Add a new feature to spoke-package and use it in hub"

Claude Code:
1. Read /path/to/spoke-package/src/... (understand pattern)
2. Write /path/to/spoke-package/src/.../new_feature.py
3. Write /path/to/spoke-package/tests/test_new_feature.py
4. Run spoke tests: uv run pytest ../spoke-package/tests/ -v
5. Edit /path/to/hub/tools/scripts/some_script.py (import and use)
6. Run hub tests: uv run pytest tools/tests/
```

**No context switching needed.** Single session, absolute paths, seamless development.

## Testing Strategy

### Unit Tests (Spoke)

Test components in isolation:

```bash
cd ../spoke-package
uv run pytest tests/ -v
uv run pytest tests/ --cov=. --cov-report=term-missing -q
```

### Integration Tests (Hub)

Test package against real documentation:

```bash
cd /path/to/hub
uv run pytest tools/tests/test_integration.py -v
```

The hub provides:
- Real files with various edge cases
- Real config files
- Integration tests that catch regressions

## ADR Management

### Ecosystem ADRs (Hub)

Decisions that apply across all packages:
- Testing standards ({term}`ADR-26011`)
- Interface contracts
- Development conventions

### Implementation ADRs (Spoke)

Decisions specific to package implementation:
- Internal module structure
- Dependency choices
- Performance trade-offs

### Spoke's ARCHITECTURE.md

Each spoke maintains an `ARCHITECTURE.md` that links to governing hub ADRs:

```markdown
# ARCHITECTURE.md

This package implements specifications from the hub ecosystem.

## Governing ADRs (in hub)
- [ADR-XXXXX: Package Purpose](link) - Why this package exists
- [ADR-YYYYY: Testing Standards](link) - Required test coverage

## Implementation ADRs (this repo)
- ADR-001: Internal design decisions
```

## Configuration

### Hub pyproject.toml

```toml
[tool.uv.sources]
spoke-package = { path = "../spoke-package", editable = true }

[tool.spoke-package]
# Configuration consumed by the spoke package
config_key = "value"
```

### Spoke pyproject.toml

```toml
[project]
name = "spoke-package"
version = "0.1.0"

[project.optional-dependencies]
dev = ["pytest", "pytest-cov"]
```

## Verification Commands

```bash
# Verify installation
uv run python -c "from spoke_package import SomeClass; print('OK')"

# Verify version
uv run python -c "import spoke_package; print(spoke_package.__version__)"

# Verify symlink
ls -la .venv/lib/python*/site-packages/ | grep spoke_package
```

## Governing ADRs

| ADR | Purpose |
|-----|---------|
| {term}`ADR-26012` | Extraction of Documentation Validation Engine (founding document) |
| {term}`ADR-26020` | Hub-and-Spoke Ecosystem Documentation Architecture |
| {term}`ADR-26011` | Mandatory Script Suite Workflow (testing standards) |

## Troubleshooting

### Import Error After Spoke Edit

1. Verify symlink exists: `ls -la .venv/lib/python*/site-packages/spoke_package`
2. Reinstall if needed: `uv pip install -e "../spoke-package"`
3. Check Python path: `uv run python -c "import spoke_package; print(spoke_package.__file__)"`

### Changes Not Reflected

1. Confirm you're editing spoke source (not a cached copy)
2. Clear `.pyc` files: `find ../spoke-package -name "*.pyc" -delete`
3. Restart Python interpreter (if using REPL)

### Version Mismatch

1. Check spoke version: `uv run python -c "import spoke_package; print(spoke_package.__version__)"`
2. Verify spoke has the expected API
3. Run spoke tests to confirm implementation is complete
