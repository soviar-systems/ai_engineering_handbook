#!/bin/bash


main() {
    # Run the check_broken_links.py script on each staged markdown file
    for FILE in "$@"; do
      if ! python3 ./helpers/scripts/check_broken_links.py "${FILE}"; then
        echo "Broken links found in ${FILE}. Please fix them before committing."
        exit 1
      fi
    done

    exit 0
}


main "$@"
