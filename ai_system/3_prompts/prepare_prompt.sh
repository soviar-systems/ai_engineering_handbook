#!/bin/bash
set -euo pipefail


main() {
    jq . "$1" >/dev/null
    yq -oy "$1"
}


main "$@"
