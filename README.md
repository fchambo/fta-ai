# fta-claude-plugin

Claude Code plugin marketplace with **travel-agent**, a toolkit for freelance travel agents who work in Excel, Word and PDF.

It covers social media content, destination research, client questionnaires, trip folders with an Excel Trip Sheet, trip and payment summaries, and provider commission tracking. The workspace can be in English or Spanish.

See [travel-agent/README.md](travel-agent/README.md) for what each skill does.

## Install

**In Claude (chat or Cowork):** open **Customize → Plugins → Add → Add marketplace**, enter `fchambo/fta-claude-plugin`, and add **Travel Agent**. Or use **Add → Upload plugin** with a `travel-agent.zip` built as shown below. If the repository is private, Claude asks you to connect GitHub and give the Claude GitHub App access to it.

**In Claude Code:**

```bash
claude plugin marketplace add fchambo/fta-claude-plugin
claude plugin install travel-agent@fta-marketplace
```

Python 3 is needed for Cowork and Claude Code ([python.org](https://www.python.org/downloads/); on Windows tick **"Add python.exe to PATH"**). Nothing is needed for Claude chat.

## Build the upload zip

```bash
python3 tools/build.py
cd travel-agent && zip -r ../travel-agent.zip . -x "*/__pycache__/*" "*.DS_Store"
```
