#!/bin/bash
set -euo pipefail

main() {
    declare -a staged_md
    declare -a staged_notebooks

    # Get staged .md and .ipynb files
    read -ra staged_md <<< $(git diff --cached --name-only --diff-filter=AMR | \
        grep "\.md$")
    read -ra staged_notebooks <<< $(git diff --cached --name-only --diff-filter=AMR | \
        grep "\.ipynb$")

    # Check .md → .ipynb
    for md in "${staged_md[@]}"; do
      ipynb="${md%.md}.ipynb"
      if [[ ! "${staged_notebooks[*]}" =~ "${ipynb}" ]]; then
        echo "ERROR: ${md} is staged, but its pair ${ipynb} is not."
        echo "Run: git add ${ipynb}"
        exit 1
      fi
    done

    # Check .ipynb → .md
    for ipynb in "${staged_notebooks[@]}"; do
      md="${ipynb%.ipynb}.md"
      if [[ ! "${staged_md[*]}" =~ "${md}" ]]; then
        echo "ERROR: ${ipynb} is staged, but its pair ${md} is not."
        echo "Run: git add ${md}"
        exit 1
      fi
    done
}


main "$@"
