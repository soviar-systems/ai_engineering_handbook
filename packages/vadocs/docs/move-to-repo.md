# Moving vadocs to a Dedicated Repository

## Step 1: Create the new repository

```bash
mkdir ~/projects/vadocs
cd ~/projects/vadocs
git init
```

## Step 2: Copy package files

```bash
# Copy the package contents (not the parent directory)
cp -r /path/to/ai_engineering_book/packages/vadocs/* ~/projects/vadocs/

# Remove the local .venv (you'll create a new one)
rm -rf ~/projects/vadocs/.venv
```

## Step 3: Initialize the new repository

```bash
cd ~/projects/vadocs

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.venv/
dist/
*.egg-info/
.pytest_cache/
.coverage
EOF

# Initialize uv and install dependencies
uv sync
uv pip install -e ".[dev]"

# Verify tests pass
uv run pytest tests/ -v
```

## Step 4: Create initial commit

```bash
git add .
git commit -m "feat: Initial vadocs v0.1.0 package

Documentation validation engine with YAML frontmatter sync.

Features:
- FrontmatterValidator for generic YAML validation
- AdrValidator for ADR-specific validation
- AdrTermValidator for MyST term references
- AdrFixer and SyncFixer for auto-fixes
- load_config() for YAML config loading

79 tests passing."
```

## Step 5: Push to GitHub

```bash
# Option A: Using GitHub CLI
gh repo create vadocs --public --source=. --push

# Option B: Manual
git remote add origin git@github.com:YOUR_USERNAME/vadocs.git
git push -u origin main
```

## Step 6: Test installation in target project

```bash
cd /path/to/your/project

# Install from GitHub
uv add "vadocs @ git+https://github.com/YOUR_USERNAME/vadocs.git"

# Verify it works
uv run python -c "from vadocs import AdrValidator; print('OK')"
```

## Step 7: Clean up original location

```bash
rm -rf /path/to/ai_engineering_book/packages/vadocs
```

## Optional: Tag a release

```bash
cd ~/projects/vadocs
git tag v0.1.0
git push origin v0.1.0
```

Then install specific version:

```bash
uv add "vadocs @ git+https://github.com/YOUR_USERNAME/vadocs.git@v0.1.0"
```
