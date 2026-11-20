---
name: trip-scaffold
description: Set up a travel agency workspace or create the folders and Excel Trip Sheet for a new client trip. Use when a travel agent mentions a new client or inquiry, or asks to set up, organize or create folders for a trip. For finding, opening or loading vouchers and confirmations, use the vouchers skill. También en español: nuevo cliente, nueva consulta, armar o configurar mi agencia, crear carpetas o la ficha del viaje.
---

# Trip scaffold

First read `references/workspace.md` in this skill's folder (`${CLAUDE_SKILL_DIR}/references/workspace.md`): it says how to work in **folder mode** (Claude Code, Cowork) and **chat mode** (Claude chat, where files come as attachments and go back as downloads). In this skill and that file, `ta` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ta.py"`. If that path doesn't resolve, as can happen in Claude chat where the skill folder is copied into the sandbox, use `scripts/ta.py` inside the copied skill folder.

**The agent's Knowledge Base.** Check it as **The agent's Knowledge Base** in `references/workspace.md` says, loading what fits setting up trips: how they name and organize trips, and what every new trip needs.

## New workspace (first time only)

**Chat mode:** create it in a scratch folder as `workspace.md` describes, give the agent the Providers & Commissions workbook to download, and tell them which folders to create on their computer (or give them the zipped folder).

**Folder mode:** if `ta find-trips <dir>` finds nothing and there's no `.travel-agent.json`, ask for:
- the folder where they keep client files (suggest `~/Documents/Agency` or `~/Documents/Agencia`)
- their working language (English or Spanish), agency/brand name, and main currency
- their brand colors (up to 3 hex codes, main first), used on client PDFs. Optional: if they don't have them handy, skip it; the skills that make client documents ask later.

Then run `ta init …` and tell them what was created. If they gave brand colors, save them with `update-providers` (`{"settings": {"brand_colors": "#0F766E, #EA580C"}}`). Ask them to fill in the **Providers & Commissions** workbook (or offer to do it with the **commissions** skill).

## New trip

1. Collect the **client name**, **main destination** and **travel month** (`YYYY-MM`). If the month isn't decided, use the inquiry month and say so.
2. Run `ta new-trip "<base>" "<Client>" "<Destination>" <YYYY-MM>`. Exit code 2 means the trip already exists, so offer to open that Trip Sheet instead.
3. If the agent already shared details (dates, travelers, budget, phone), write them in right away with `update-trip`.
4. Tell them where the folder is and what the Trip Sheet tabs are for:
   - **Trip**: client and trip details
   - **Travelers**: one row per passenger
   - **Bookings**: every service sold, with the provider ID, prices and free-cancellation date
   - **Payments**: what the client owes and what the agent owes providers, each with a due date
   - **Deadlines**: anything else with a date
5. In chat mode, give them the Trip Sheet to download and tell them where to save it: `Clients/<Client>/<YYYY-MM Destination>/`.
6. Suggest the next step, which is usually the **client-intake** questionnaire.

## Vouchers and confirmations

Finding, opening and loading vouchers and confirmations is the **vouchers** skill's job (`/recuperar-vouchers`). If the agent shares booking documents while you're creating a trip, finish creating it, then load them as the **vouchers** skill says.
