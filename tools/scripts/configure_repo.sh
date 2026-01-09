#!/bin/bash
set -euo pipefail


main() {

    # Install the pre-commit hooks.
    uv add pre-commit
    uv run pre-commit install
}
