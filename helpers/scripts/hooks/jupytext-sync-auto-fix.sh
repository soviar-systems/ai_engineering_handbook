#!/bin/bash
set -euo pipefail

main() {
    local -a staged_notebooks
    local base

    # Get staged files matching .md or .ipynb
    staged_notebooks=( $(git diff --cached --name-only --diff-filter=AMR | grep -E "\.(md|ipynb)$") )

    if [[ ${#staged_notebooks[@]} -eq 0 ]]; then
      exit 0  # No notebook files staged → skip
    fi

    # Sync and re-stage
    for file in "${staged_notebooks[@]}"; do
      # sync
      if ! uv run jupytext --sync "${file}"; then
          echo "Error: Failed to sync ${file}" >&2
          exit 1
      fi

      # re-stage
      base="${file%.*}"
      if ! git add "${base}.md"; then
          echo "Error: Failed to add ${base}.md" >&2
          exit 1
      fi
      if ! git add "${base}.ipynb"; then
          echo "Error: Failed to add ${base}.ipynb" >&2
          exit 1
      fi
    done
}


main "$@"
