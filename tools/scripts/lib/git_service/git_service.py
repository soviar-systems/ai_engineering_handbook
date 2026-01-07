import subprocess
from pathlib import Path
from typing import List, Optional

class GitService:
    def __init__(self, root_dir: Optional[Path] = None):
        """Discovers git root or validates the provided path."""
        if root_dir:
            self.root_dir = Path(root_dir).resolve()
        else:
            try:
                # Use check=True to trigger CalledProcessError on non-zero exits
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.root_dir = Path(result.stdout.strip()).resolve()
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise RuntimeError(f"Not a git repository: {e}")

    def run_cmd(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Centralized execution point with path sanitization."""
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.root_dir)
            )
        except FileNotFoundError:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=127,
                stdout="",
                stderr="Executable not found"
            )

    def is_in_index(self, path: Path) -> bool:
        """Checks if file is tracked by git."""
        res = self.run_cmd(["git", "ls-files", "--error-unmatch", str(path)])
        return res.returncode == 0

    def has_unstaged_changes(self, path: Path) -> bool:
        """
        Checks if file has modified content not yet staged.
        Returns True ONLY if git diff returns 1 (changes detected).
        Raises RuntimeError if git returns an error code (e.g., 128).
        """
        res = self.run_cmd(["git", "diff", "--exit-code", str(path)])
        
        if res.returncode == 0:
            return False
        if res.returncode == 1:
            return True
        
        # Any other code (like 128) is a system failure, not a "dirty" state
        raise RuntimeError(f"Git diff failed with exit code {res.returncode}: {res.stderr}")
