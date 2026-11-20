#!/usr/bin/env python3
"""travel-agent tools: `python3 ta.py --help`.

Runs directly where openpyxl, python-docx and reportlab are installed (Claude's
chat sandbox). Elsewhere it creates a private environment once, in
~/.travel-agent (or $CLAUDE_PLUGIN_DATA), and re-runs itself there.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = ["openpyxl>=3.1,<4", "python-docx>=1.1,<2", "reportlab>=4,<5", "pypdf>=4,<6"]
READY_MARKER = ".ta-ready-2"


def have_libraries():
    try:
        import docx  # noqa: F401
        import openpyxl  # noqa: F401
        import reportlab  # noqa: F401
    except ImportError:
        return False
    return True


def venv_python(venv):
    for candidate in (os.path.join(venv, "bin", "python"), os.path.join(venv, "Scripts", "python.exe")):
        if os.path.exists(candidate):
            return candidate
    return None


def run_in_private_env():
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(os.path.expanduser("~"), ".travel-agent")
    venv = os.path.join(base, "venv")
    python = venv_python(venv)
    if python is None or not os.path.exists(os.path.join(venv, READY_MARKER)):
        print("Setting up travel-agent tools (first run only)...", file=sys.stderr)
        if python is None:
            subprocess.run([sys.executable, "-m", "venv", venv], check=True, stdout=sys.stderr)
            python = venv_python(venv)
        try:
            subprocess.run([python, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *REQUIREMENTS],
                           check=True, stdout=sys.stderr)
        except subprocess.CalledProcessError:
            sys.exit("travel-agent tools: couldn't install openpyxl, python-docx and reportlab here "
                     "(no internet access?). Install them with pip, or run where they're available.")
        open(os.path.join(venv, READY_MARKER), "w").close()
    env = {**os.environ, "TA_PRIVATE_ENV": "1"}
    sys.exit(subprocess.call([python, os.path.abspath(__file__), *sys.argv[1:]], env=env))


def main():
    if not have_libraries():
        if os.environ.get("TA_PRIVATE_ENV"):
            sys.exit("travel-agent tools: libraries missing. Delete the ~/.travel-agent folder and try again.")
        run_in_private_env()
    sys.path.insert(0, HERE)
    from travel_agent_tools.__main__ import main as run
    run()


if __name__ == "__main__":
    main()
