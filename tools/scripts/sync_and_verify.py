#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from typing import List


class GitInterface:
    def run(self, cmd: List[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(cmd, capture_output=True, text=True)
        except (FileNotFoundError, PermissionError) as e:
            # Return a failed process instead of crashing the script
            return subprocess.CompletedProcess(
                args=cmd, returncode=1, stdout="", stderr=str(e)
            )

    def jupytext_sync(self, filepath: Path) -> subprocess.CompletedProcess:
        return self.run(["uv", "run", "jupytext", "--sync", str(filepath)])

    def is_in_index(self, filepath: Path) -> bool:
        res = self.run(["git", "ls-files", "--error-unmatch", str(filepath)])
        return res.returncode == 0

    def is_file_fully_staged(self, filepath: Path) -> bool:
        res = self.run(["git", "diff", "--exit-code", str(filepath)])
        return res.returncode == 0


class NotebookPairProcessor:
    # Add new patterns here as needed
    EXCLUDED_PATHS = [
        "pr/tg_channel",
        "architecture/",
    ]

    def __init__(self, filepath: Path, git: GitInterface):
        self.filepath = filepath
        self.git = git
        self.base = filepath.with_suffix("")

    def should_skip(self) -> bool:
        base_str = str(self.base)
        return any(pattern in base_str for pattern in self.EXCLUDED_PATHS)

    def process(self) -> bool:
        if self.should_skip():
            print(f"✅ {self.base}.md is not under jupytext workflow")
            return True

        # 1. SYNC
        sync_result = self.git.jupytext_sync(self.filepath)
        if sync_result.returncode != 0:
            print(f"❌ Jupytext sync failed: {sync_result.stderr}", file=sys.stderr)
            return False

        # 2. CHECK PAIR
        md_path = self.base.with_suffix(".md")
        ipynb_path = self.base.with_suffix(".ipynb")

        success = True
        for p in [md_path, ipynb_path]:
            if not self.git.is_in_index(p):
                print(f"⚠️  INCOMPLETE STAGING: {p.name} (not staged)", file=sys.stderr)
                success = False
            elif not self.git.is_file_fully_staged(p):
                print(
                    f"⚠️  INCOMPLETE STAGING: {p.name} (unstaged changes)",
                    file=sys.stderr,
                )
                success = False
        return success


class SyncOrchestrator:
    def __init__(self):
        self.git = GitInterface()

    def run(self, file_args: List[str]) -> int:
        exit_code = 0
        processed_any = False
        for f in file_args:
            filepath = Path(f)
            if not filepath.exists():
                continue
            processor = NotebookPairProcessor(filepath, self.git)
            if processor.should_skip():
                continue
            processed_any = True
            if not processor.process():
                exit_code = 1

        if exit_code == 0 and processed_any:
            print("✅ Notebook pairs are synced and staged correctly.")
        return exit_code


if __name__ == "__main__":
    sys.exit(SyncOrchestrator().run(sys.argv[1:]))
