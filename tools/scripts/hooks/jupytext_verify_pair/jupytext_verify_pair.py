import sys
from pathlib import Path
from typing import List

from tools.scripts.configs.paths import is_ignored
from tools.scripts.lib.git_service.git_service import GitService


def run(paths: List[str]) -> bool:
    """
    Verifies the integrity of Jupytext pairs in the Git index.

    Logic Matrix:
    - State 0: Neither file tracked -> Skip (Success).
    - State 1: Both tracked and clean -> Success.
    - States 2, 3, 7: Unstaged changes -> Failure (Action: git add).
    - States 4, 5, 6: Partial tracking -> Failure (Action: git add missing).
    - State 8: Git system failure -> Failure.
    """
    git = GitService()
    overall_success = True
    count = 0

    for p in paths:
        print("count:", count)
        count += 1
        if not isinstance(p, str) or not p:
            overall_success = False
            continue

        # Convert to Path object and resolve to handle absolute/relative inputs
        path = Path(p)

        # 1. Exclusion Logic: Respect EXCLUDED_DIRS defined in paths.py
        if is_ignored(str(path)):
            continue

        # 2. Physical Validation
        if not path.is_file():
            # If the file is missing from disk, we skip it to let Git handle deletions
            continue

        # 3. Pair Identification
        if path.suffix == ".ipynb":
            ipynb_path, md_path = path, path.with_suffix(".md")
        elif path.suffix == ".md":
            ipynb_path, md_path = path.with_suffix(".ipynb"), path
        else:
            # Skip non-notebook/markdown files
            continue

        # 4. Verification Logic
        try:
            # Check Staging Status
            ipynb_tracked = git.is_in_index(ipynb_path)
            md_tracked = git.is_in_index(md_path)

            # --- State 0: Both Untracked ---
            # If neither file is in the Git index, ignore them (allow WIP files)
            if not ipynb_tracked and not md_tracked:
                continue

            # --- States 4/5/6: Partial Tracking ---
            if not ipynb_tracked or not md_tracked:
                missing = ipynb_path if not ipynb_tracked else md_path
                tracked = md_path if not ipynb_tracked else ipynb_path
                print(
                    f"❌ Partial Tracking: {tracked} is staged but {missing} is not. "
                    f"Run 'git add {missing}'",
                    file=sys.stderr,
                )
                overall_success = False
                continue

            # --- States 2/3/7: Unstaged Changes (Dirty) ---
            i_dirty = git.has_unstaged_changes(ipynb_path)
            m_dirty = git.has_unstaged_changes(md_path)

            if i_dirty or m_dirty:
                if i_dirty:
                    print(
                        f"❌ Unstaged changes in {ipynb_path}. Run 'git add {ipynb_path}'.",
                        file=sys.stderr,
                    )
                if m_dirty:
                    print(
                        f"❌ Unstaged changes in {md_path}. Run 'git add {md_path}'.",
                        file=sys.stderr,
                    )
                overall_success = False
                continue

            # State 1: Both tracked and clean (Implicit Success)

        except Exception as e:
            # State 8: System Failure (e.g., Git error code 128)
            print(
                f"❌ State 8 Failure: Git service error on {path.name}: {e}",
                file=sys.stderr,
            )
            overall_success = False

    return overall_success
