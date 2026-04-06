#!/bin/bash
set -euo pipefail


main() {
    start="$1"
    end="$2"

    #echo "Changed files between ${start} and ${end}:"
    #git --no-pager diff --name-status "${start}" "${end}"

    echo "Commits messages between ${start} and ${end}:"
    git log "${start}..${end}" --format="%B" --name-status | grep -v "^pr:" | grep -v '/pr/' | grep -v '^$' | grep -v 'Co-Authored-By:' | grep -v 'misc/plan/' | grep -v 'CLAUDE.md'
}


main "$@"
