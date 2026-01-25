#!/usr/bin/env python3
"""Check that each script has a complete suite: script, test, and documentation.

Naming convention:
- Script: tools/scripts/<name>.py
- Test:   tools/tests/test_<name>.py
- Doc:    tools/docs/scripts_instructions/<name>_py_script.md

Validates:
1. Each script has matching test and doc files (naming convention)
2. When script/test changes, corresponding doc must be staged
3. When doc is renamed, config files must be staged
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path("tools/scripts")
TESTS_DIR = Path("tools/tests")
DOCS_DIR = Path("tools/docs/scripts_instructions")

# Scripts excluded from documentation requirement
EXCLUDED_SCRIPTS = {"paths.py", "__init__.py"}

# Config files that must be updated when doc is renamed
CONFIG_FILES = {".pre-commit-config.yaml", ".github/workflows/quality.yml"}


def get_staged_files() -> set[str]:
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()


def get_renamed_files() -> dict[str, str]:
    """Get renamed files from staging area. Returns {old_path: new_path}."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True,
        text=True,
    )
    renamed = {}
    for line in result.stdout.strip().split("\n"):
        if line.startswith("R"):
            parts = line.split("\t")
            if len(parts) >= 3:
                renamed[parts[1]] = parts[2]
    return renamed


def script_name_to_paths(name: str) -> tuple[Path, Path, Path]:
    """Convert script name to script, test, and doc paths."""
    script = SCRIPTS_DIR / f"{name}.py"
    test = TESTS_DIR / f"test_{name}.py"
    doc = DOCS_DIR / f"{name}_py_script.md"
    return script, test, doc


def get_all_scripts() -> list[str]:
    """Get all script names (without .py extension) from scripts directory."""
    if not SCRIPTS_DIR.exists():
        return []
    return [
        f.stem
        for f in SCRIPTS_DIR.glob("*.py")
        if f.name not in EXCLUDED_SCRIPTS
    ]


def check_naming_convention(verbose: bool = False) -> list[str]:
    """Check that each script has matching test and doc files."""
    errors = []
    for name in get_all_scripts():
        script, test, doc = script_name_to_paths(name)

        if not test.exists():
            errors.append(f"Missing test: {test} (for script {script})")
        if not doc.exists():
            errors.append(f"Missing doc: {doc} (for script {script})")

        if verbose and test.exists() and doc.exists():
            print(f"OK: {name} has script, test, and doc")

    return errors


def check_doc_staged(staged: set[str], verbose: bool = False) -> list[str]:
    """Check that doc is staged when script or test changes."""
    errors = []
    for name in get_all_scripts():
        script, test, doc = script_name_to_paths(name)

        script_changed = str(script) in staged
        test_changed = str(test) in staged
        doc_staged = str(doc) in staged

        if (script_changed or test_changed) and not doc_staged:
            trigger = str(script) if script_changed else str(test)
            errors.append(f"Doc not staged: {doc} (triggered by change in {trigger})")
        elif verbose and (script_changed or test_changed):
            print(f"OK: {doc} is staged with its script/test")

    return errors


def check_doc_rename(staged: set[str], verbose: bool = False) -> list[str]:
    """Check that config files are staged when doc is renamed."""
    errors = []
    renamed = get_renamed_files()

    for old_path, new_path in renamed.items():
        if old_path.startswith(str(DOCS_DIR)) and old_path.endswith("_py_script.md"):
            for config in CONFIG_FILES:
                if config not in staged:
                    errors.append(
                        f"Config not staged: {config} (doc renamed: {old_path} -> {new_path})"
                    )
            if verbose:
                print(f"Doc renamed: {old_path} -> {new_path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that each script has a complete suite (script, test, doc)."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--check-convention-only",
        action="store_true",
        help="Only check naming convention, skip staging checks",
    )
    args = parser.parse_args()

    errors = []

    # Always check naming convention
    errors.extend(check_naming_convention(args.verbose))

    # Check staging unless --check-convention-only
    if not args.check_convention_only:
        staged = get_staged_files()
        errors.extend(check_doc_staged(staged, args.verbose))
        errors.extend(check_doc_rename(staged, args.verbose))

    if errors:
        print("\nErrors found:")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1

    if args.verbose:
        print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
