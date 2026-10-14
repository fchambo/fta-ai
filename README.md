# fta-claude-plugin

Claude Code plugin marketplace with **travel-agent**, a toolkit for freelance travel agents who work in Excel, Word and PDF.

It covers social media content, destination research, client questionnaires, trip folders with an Excel Trip Sheet, trip and payment summaries, and provider commission tracking. The workspace can be in English or Spanish.

See [travel-agent/README.md](travel-agent/README.md) for what each skill does.

## Install

Requirements: [Claude Code](https://claude.com/claude-code) and [Python 3](https://www.python.org/downloads/). On Windows you also need [Git for Windows](https://git-scm.com/download/win), and when installing Python, tick **"Add python.exe to PATH"**.

```bash
claude plugin marketplace add fchambo/fta-claude-plugin
claude plugin install travel-agent@fta-marketplace
```

To get updates:

```bash
claude plugin marketplace update fta-marketplace
```

If the repository is private, git on that computer must be signed in to a GitHub account with access to it. On Windows, Git Credential Manager opens a browser to sign in the first time.

On first use the plugin spends about 30 seconds installing its Python libraries (it needs internet once). Then Claude asks where to keep the agency's files.
