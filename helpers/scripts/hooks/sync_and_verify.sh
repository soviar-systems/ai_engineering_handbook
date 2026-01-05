#!/bin/bash
set -euo pipefail

main() {
    local exit_code=0

    for file in "$@"; do
        base="${file%.*}"
        if [[ "${base}" =~ "pr/tg_channel" ]]; then
            echo "✅ ${base}.md is not under jupytext workflow"
            exit 0
        fi

        # 1. Sync using your project's specific uv environment
        # This respects your pyproject.toml and local kernelspecs
        if ! uv run jupytext --sync "$file"; then
            echo "❌ Jupytext sync failed for $file"
            exit 1
        fi

        # 2. Force-add both files.
        # (Inside pre-commit, this usually only stages files that were already
        # partly staged, but it's necessary for the next check.)
        git add "${base}.md" "${base}.ipynb"

        # 3. The Integrity Check
        # We check the actual Git Index (the --cached files)
        STAGED_FILES=$(git diff --cached --name-only)

        if ! echo "$STAGED_FILES" | grep -q "${base}.md" || \
           ! echo "$STAGED_FILES" | grep -q "${base}.ipynb"; then
            echo
            echo "⚠️  INCOMPLETE STAGING: ${base}.{md,ipynb} pair is not fully staged."
            echo "👉 ACTION: Run: git add ${base}.md ${base}.ipynb"
            exit_code=1
        fi
    done

    if [[ $exit_code -eq 0 ]]; then
        echo "✅ Notebook pairs are synced and staged correctly."
    fi

    exit $exit_code
}

main "$@"
