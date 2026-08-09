#!/usr/bin/env python3
"""Install this skill into BB's user skill directory."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

SKILL_NAME = "skill-create-ebook"
EXCLUDED = {".git", ".venv", "__pycache__", ".DS_Store"}


def main() -> int:
    source = Path(__file__).resolve().parents[1]
    destination = Path.home() / ".bb" / "skills" / SKILL_NAME
    if source == destination:
        print(destination)
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or destination.exists():
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(*EXCLUDED, "*.pyc"),
    )
    os.chmod(destination / "scripts" / "install_skill.py", 0o755)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
