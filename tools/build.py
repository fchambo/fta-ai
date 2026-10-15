#!/usr/bin/env python3
"""Build the travel-agent skills from the shared sources in tools/.

In Claude chat and in ChatGPT each skill runs on its own (only its folder reaches
the sandbox), so every skill carries its own copy of the tools. Edit files in
tools/ (and the SKILL.md files in travel-agent/skills/), then run:

    python3 tools/build.py            # update the Claude plugin's skills in place
    python3 tools/build.py --check    # fail if any copy is out of date
    python3 tools/build.py --chatgpt  # also write dist/chatgpt/<skill>.zip for ChatGPT

workspace.md may contain platform blocks:
    <!-- only:claude --> ... <!-- /only -->
    <!-- only:chatgpt --> ... <!-- /only -->
"""
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SKILLS = os.path.join(ROOT, "travel-agent", "skills")
CHATGPT_DIST = os.path.join(ROOT, "dist", "chatgpt")
PACKAGE = "travel_agent_tools"
PLATFORM_BLOCK = re.compile(r"<!-- only:(\w+) -->\n(.*?)<!-- /only -->\n", re.S)

CLAUDE_INTRO = re.compile(r"^First read `references/workspace\.md` in this skill's folder \(`\$\{CLAUDE_SKILL_DIR\}.*$", re.M)
CHATGPT_INTRO = (
    "First read `references/workspace.md` in this skill's folder: it explains how to work with the agent's "
    "files in ChatGPT (attachments in, downloads out) and the English/Spanish rules. In this skill and that "
    "file, `ta` means `python3 <skill folder>/scripts/ta.py`, where `<skill folder>` is the folder this "
    "SKILL.md was installed in. Always call it with that full path."
)


def for_platform(text, platform):
    return PLATFORM_BLOCK.sub(lambda m: m.group(2) if m.group(1) == platform else "", text)


def shared_files(platform):
    """{destination relative to a skill folder: file content (bytes)}"""
    files = {"scripts/ta.py": open(os.path.join(TOOLS, "ta.py"), "rb").read()}
    with open(os.path.join(TOOLS, "workspace.md"), encoding="utf-8") as f:
        files["references/workspace.md"] = for_platform(f.read(), platform).encode("utf-8")
    pkg = os.path.join(TOOLS, PACKAGE)
    for name in sorted(os.listdir(pkg)):
        if name.endswith(".py"):
            files[f"scripts/{PACKAGE}/{name}"] = open(os.path.join(pkg, name), "rb").read()
    return files


def skill_dirs():
    return [os.path.join(SKILLS, d) for d in sorted(os.listdir(SKILLS))
            if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))]


def sync_claude(check):
    stale = []
    files = shared_files("claude")
    for skill_dir in skill_dirs():
        pkg_dir = os.path.join(skill_dir, "scripts", PACKAGE)
        if os.path.isdir(pkg_dir):
            for name in os.listdir(pkg_dir):
                if name.endswith(".py") and f"scripts/{PACKAGE}/{name}" not in files:
                    stale.append(os.path.join(pkg_dir, name))
                    if not check:
                        os.remove(os.path.join(pkg_dir, name))
        for dest, content in files.items():
            path = os.path.join(skill_dir, dest)
            if os.path.exists(path) and open(path, "rb").read() == content:
                continue
            stale.append(path)
            if not check:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(content)
    return stale


def build_chatgpt():
    shutil.rmtree(CHATGPT_DIST, ignore_errors=True)
    os.makedirs(CHATGPT_DIST)
    shared = shared_files("chatgpt")
    built = []
    for skill_dir in skill_dirs():
        name = os.path.basename(skill_dir)
        archive = os.path.join(CHATGPT_DIST, f"{name}.zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for folder, dirs, filenames in os.walk(skill_dir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for filename in sorted(filenames):
                    if filename == ".DS_Store":
                        continue
                    path = os.path.join(folder, filename)
                    rel = os.path.relpath(path, skill_dir).replace(os.sep, "/")
                    if rel in shared:
                        content = shared[rel]
                    elif rel == "SKILL.md":
                        text = open(path, encoding="utf-8").read()
                        text, count = CLAUDE_INTRO.subn(CHATGPT_INTRO, text)
                        if count != 1:
                            sys.exit(f"{name}/SKILL.md: expected one Claude intro paragraph to replace, found {count}")
                        if "CLAUDE_" in text:
                            sys.exit(f"{name}/SKILL.md: still mentions a Claude-only placeholder")
                        content = text.encode("utf-8")
                    else:
                        content = open(path, "rb").read()
                    zf.writestr(f"{name}/{rel}", content)
        built.append(archive)
    return built


def main():
    check = "--check" in sys.argv
    stale = sync_claude(check)
    if check and stale:
        sys.exit("Out of date (run python3 tools/build.py):\n  " + "\n  ".join(os.path.relpath(p, ROOT) for p in stale))
    print(f"{'Checked' if check else 'Updated'} {len(stale)} file(s)" if stale else "All skills up to date")
    if "--chatgpt" in sys.argv:
        for archive in build_chatgpt():
            print("ChatGPT:", os.path.relpath(archive, ROOT))


if __name__ == "__main__":
    main()
