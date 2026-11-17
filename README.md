# fta-claude-plugin

Claude Code plugin marketplace with **travel-agent**, a toolkit for freelance travel agents who work in Excel, Word and PDF.

Its front door is **FTA**, the Freelance Travel AI Agent. It takes a client's request, recalls the client's past trips, hands Disney World to **MinnieAI** and Universal Orlando to **FionaAI**, and turns their research plus Patty's park plan into a priced client quote.

It covers social media content, destination research, client questionnaires, trip folders with an Excel Trip Sheet, trip and payment summaries, an interactive dashboard of upcoming dates and pending tasks for every client and for the agent, provider commission tracking, and **Patty**, a Disney World / Universal Orlando park planner that delivers a client PDF with route maps. The workspace can be in English or Spanish.

See [travel-agent/README.md](travel-agent/README.md) for what each skill does.

## Install

**In Claude (chat or Cowork):** open **Customize → Plugins → Add → Add marketplace**, enter `fchambo/fta-claude-plugin`, and add **Travel Agent**. Or use **Add → Upload plugin** with a `travel-agent.zip` built as shown below. If the repository is private, Claude asks you to connect GitHub and give the Claude GitHub App access to it.

**In Claude Code:**

```bash
claude plugin marketplace add fchambo/fta-claude-plugin
claude plugin install travel-agent@fta-marketplace
```

Python 3 is needed for Cowork and Claude Code ([python.org](https://www.python.org/downloads/); on Windows tick **"Add python.exe to PATH"**). Nothing is needed for Claude chat.

**In ChatGPT (Plus and above):** build the skill zips (below), then in ChatGPT open **Skills** and upload each of the skill zips with **Upload from your computer**. In ChatGPT the agent attaches files to the chat and downloads the files ChatGPT returns. The Spanish slash commands are Claude-only, but Spanish requests work in both.

## Build the upload zips

```bash
python3 tools/build.py --chatgpt   # updates the Claude skills and writes dist/chatgpt/<skill>.zip
cd travel-agent && zip -r ../travel-agent.zip . -x "*/__pycache__/*" "*.DS_Store"   # Claude plugin zip
```

One repository serves both: `tools/` holds the shared code and rules, and `tools/workspace.md` marks Claude-only and ChatGPT-only passages with `<!-- only:claude -->` / `<!-- only:chatgpt -->` blocks.
