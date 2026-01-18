#!/bin/bash
set -euo pipefail


main() {
    # Validate JSON first (optional but good practice)
    jq . "$1" >/dev/null

    # Remove metadata and escape special characters
    yq 'del(.metadata)' "$1" -oy | sed "s/[*'\''\"\`#]//g" 
}


main "$@"
