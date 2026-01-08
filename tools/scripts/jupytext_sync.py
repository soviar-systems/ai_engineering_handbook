import subprocess
import sys
from pathlib import Path
from typing import List


def run(paths: List[str], test_only: bool = False) -> bool:
    """
    Syncs Jupytext pairs or tests their synchronization status.
    """
    if not paths:
        return True

    overall_success = True
    base_cmd = ["uv", "run", "jupytext"]

    for p in paths:
        # TC-08, 09, 10: Validate input type and content
        if not isinstance(p, (str, Path)) or not str(p).strip():
            overall_success = False
            continue

        try:
            path = Path(p).resolve()

            # TC-04: Filter extensions
            if path.suffix not in [".ipynb", ".md"]:
                continue

            # TC-06: Check disk existence
            if not path.exists():
                print(f"❌ Path does not exist: {p}", file=sys.stderr)
                overall_success = False
                continue

            # TC-01 & TC-02: Routing logic
            if test_only:
                cmd = base_cmd + ["--to", "ipynb", "--test", str(path)]
            else:
                cmd = base_cmd + ["--sync", str(path)]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                mode = "Test" if test_only else "Sync"
                print(f"❌ Jupytext {mode} failed for {path.name}", file=sys.stderr)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                overall_success = False

        except Exception as e:
            # This block covers lines 51-53 (Unexpected errors)
            print(f"❌ Unexpected error processing {p}: {e}", file=sys.stderr)
            overall_success = False

    return overall_success
