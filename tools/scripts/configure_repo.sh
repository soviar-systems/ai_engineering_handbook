#!/bin/bash
set -euo pipefail


main() {

    # Install the pre-commit hooks.
    uv add pre-commit
    uv run pre-commit install

    # Copy the aider.conf.yaml file
    copy_aider_files
}


copy_aider_files() {
    local aider_conf_src="./tools/configs/aider.conf.yml"
    local aider_conf_tgt="./.aider.conf.yml"

    cp "${aider_conf_src}" "${aider_conf_tgt}"

    echo "Done! Run 'uv run' to start coding."
}

main "$@"
