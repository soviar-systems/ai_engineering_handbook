import os
import subprocess
from pathlib import Path
from typing import List, Optional


class GitService:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir:
            self.root_dir = Path(root_dir).resolve()
        else:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.root_dir = Path(result.stdout.strip()).resolve()
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise RuntimeError(f"Not a git repository: {e}")

    def run_cmd(self, cmd: List[str]) -> subprocess.CompletedProcess:
        # Prevent 'uv' virtualenv mismatch warnings by cleaning environment
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)

        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.root_dir), env=env
            )
        except FileNotFoundError:
            return subprocess.CompletedProcess(
                args=cmd, returncode=127, stdout="", stderr="Executable not found"
            )

    def is_in_index(self, path: Path) -> bool:
        # Use relative path to ensure consistency across different environments
        rel_path = (
            path.resolve().relative_to(self.root_dir) if path.is_absolute() else path
        )
        res = self.run_cmd(["git", "ls-files", "--error-unmatch", str(rel_path)])
        return res.returncode == 0

    def has_unstaged_changes(self, path: Path) -> bool:
        rel_path = (
            path.resolve().relative_to(self.root_dir) if path.is_absolute() else path
        )
        res = self.run_cmd(["git", "diff", "--exit-code", str(rel_path)])

        if res.returncode == 0:
            return False
        if res.returncode == 1:
            return True
        if res.returncode == 128:
            # Handle "State 8" ambiguous argument: file likely doesn't exist in git tree
            return False

        raise RuntimeError(
            f"Git diff failed with exit code {res.returncode}: {res.stderr}"
        )
