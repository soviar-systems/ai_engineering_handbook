#!/bin/bash
set -euo pipefail


main() {
    start="$1"
    end="$2"

    # имена измененных файлов
    echo "Changed files between ${start} and ${end}:"
    git diff --name-status "${start}" "${end}"

    # коммитовские сообщения с файлами, которые правились
    echo "Commits messages between ${start} and ${end}:"
    git log "${start}..${end}" --format="%B" --name-status | grep -v '^$'
}


main "$@"
