#!/bin/bash
set -euo pipefail


main() {
    start="$1"
    end="$2"

    # имена измененных файлов
    git diff --name-status "${start}" "${end}"

    # коммитовские сообщения с файлами, которые правились
    git log "${start}..${end}" --format="%B" --name-only | grep -v '^$'
}


main "$@"
