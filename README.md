# Freelance Travel Agent with AI

**travel-agent** is an AI Agent's plugin for freelance travel agents who work in Excel, Word and PDF. It works in Claude (chat, Cowork and Claude Code) and in ChatGPT.

Its front door is **FTA**, the Freelance Travel AI Agent. It takes a client's request, recalls the client's past trips, hands Disney World to **MinnieAI** and Universal Orlando to **FionaAI**, and turns their research plus Patty's park plan into a priced client quote.

It covers social media content, destination research, client questionnaires, trip folders with an Excel Trip Sheet, finding and loading vouchers, the agent's own Knowledge Base of rules and policies tagged with hashtags, trip and payment summaries, an interactive dashboard of upcoming dates and pending tasks for every client and for the agent, provider commission tracking, and **Patty**, a Disney World / Universal Orlando park planner that delivers a client PDF with route maps. The workspace can be in English or Spanish.

See [travel-agent/README.md](travel-agent/README.md) for what each skill does.

## Install

**In Claude (chat or Cowork):** open **Customize → Plugins → Add → Add marketplace**, enter `fchambo/fta-ai`, and add **Travel Agent**. Or use **Add → Upload plugin** with `travel-agent.zip` from the [latest release](https://github.com/fchambo/fta-ai/releases/latest). If the repository is private, Claude asks you to connect GitHub and give the Claude GitHub App access to it.

**In Claude Code:**

```bash
claude plugin marketplace add fchambo/fta-ai
claude plugin install travel-agent@fta-marketplace
```

Python 3 is needed for Cowork and Claude Code ([python.org](https://www.python.org/downloads/); on Windows tick **"Add python.exe to PATH"**). Nothing is needed for Claude chat.

**In ChatGPT:** ChatGPT Skills are available on eligible Business, Enterprise, Healthcare, and Edu workspaces, subject to workspace settings. No Python or building needed:

1. Open the [latest release](https://github.com/fchambo/fta-ai/releases/latest) and, under **Assets**, download the ZIP for each skill you want (don't unzip them). For quotes, FTA needs `fta.zip`, `minnie-ai.zip`, `fiona-ai.zip` and `park-itinerary.zip`. `travel-agent.zip` is for Claude, not ChatGPT.
2. In ChatGPT, open **Plugins → Plugin Directory → Skills → Create → Upload from your computer** and upload the ZIPs one at a time.
3. To update, download the newer ZIPs from the latest release and upload them again.

If Skills or uploading is unavailable, ask the workspace admin to enable it. The agent attaches files to the chat and downloads the files ChatGPT returns. Spanish slash commands are Claude-only; Spanish requests work in both.

## Build the upload zips (developers)

To publish a release, build the zips and attach them to it, so agents never have to build anything:

```bash
python3 tools/build.py --chatgpt   # updates the Claude skills and writes dist/chatgpt/<skill>.zip
cd travel-agent && zip -r ../travel-agent.zip . -x "*/__pycache__/*" "*.DS_Store"   # Claude plugin zip
cd .. && gh release create v<version> dist/chatgpt/*.zip travel-agent.zip   # version from travel-agent/.claude-plugin/plugin.json
```

One repository serves both: `tools/` holds the shared code and rules, and `tools/workspace.md` marks Claude-only and ChatGPT-only passages with `<!-- only:claude -->` / `<!-- only:chatgpt -->` blocks.
