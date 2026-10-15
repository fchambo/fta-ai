#!/usr/bin/env python3
"""Copy the shared tools into every skill of the travel-agent plugin.

In Claude chat each skill runs on its own (only its folder reaches the sandbox),
so every skill carries its own copy. Edit files in tools/, then run:

    python3 tools/build.py          # copy into each skill
    python3 tools/build.py --check  # fail if any copy is out of date
"""
import filecmp
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SKILLS = os.path.join(ROOT, "travel-agent", "skills")

# source (relative to tools/) -> destination (relative to each skill folder)
FILES = {"ta.py": "scripts/ta.py", "workspace.md": "references/workspace.md"}
PACKAGE = "travel_agent_tools"


def package_files():
    src = os.path.join(TOOLS, PACKAGE)
    return {os.path.join(PACKAGE, f): f"scripts/{PACKAGE}/{f}"
            for f in sorted(os.listdir(src)) if f.endswith(".py")}


def main():
    check = "--check" in sys.argv
    stale = []
    mapping = {**FILES, **package_files()}
    for skill in sorted(os.listdir(SKILLS)):
        skill_dir = os.path.join(SKILLS, skill)
        if not os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
            continue
        pkg_dir = os.path.join(skill_dir, "scripts", PACKAGE)
        if os.path.isdir(pkg_dir):
            for name in os.listdir(pkg_dir):
                if name.endswith(".py") and f"scripts/{PACKAGE}/{name}" not in mapping.values():
                    stale.append(os.path.join(pkg_dir, name))
                    if not check:
                        os.remove(os.path.join(pkg_dir, name))
        for src, dest in mapping.items():
            src_path, dest_path = os.path.join(TOOLS, src), os.path.join(skill_dir, dest)
            if os.path.exists(dest_path) and filecmp.cmp(src_path, dest_path, shallow=False):
                continue
            stale.append(dest_path)
            if not check:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)
    if check and stale:
        sys.exit("Out of date (run python3 tools/build.py):\n  " + "\n  ".join(os.path.relpath(p, ROOT) for p in stale))
    print(f"{'Checked' if check else 'Updated'} {len(stale)} file(s)" if stale else "All skills up to date")


if __name__ == "__main__":
    main()
