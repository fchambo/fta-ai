# travel-agent: AI toolkit for freelance travel agents

Agents keep working in **Excel, Word and PDF**. The assistant reads their vouchers, contracts and client replies, keeps their spreadsheets up to date, and writes their documents.

## Install in ChatGPT

ChatGPT Skills are available on eligible Business, Enterprise, Healthcare, and Edu workspaces, subject to product availability and workspace settings. From the repository root, run `python3 tools/build.py --chatgpt`; this updates the shared skill files and creates one ZIP per skill under `dist/chatgpt/`. In ChatGPT, open **Plugins → Plugin Directory → Skills → Create → Upload from your computer**, then upload the ZIPs for the skills you want to install. Repeat for each skill ZIP. If Skills or uploading is unavailable, ask your workspace admin whether it is enabled.

In ChatGPT, attach the current Trip Sheet, vouchers, contracts, or other source files to the conversation. Download the updated or generated files ChatGPT returns and save them in your agency folders. ChatGPT skills run in chat mode and do not access files on your computer directly. The Spanish slash commands below are Claude-only; you can still ask for any task in Spanish.

| Skill | What the agent gets | Try saying |
|---|---|---|
| `fta` (**FTA AI Agent**) | From a new request to a quote: finds the client or creates their workspace and **Client Profile**, recalls their past trips, routes to **MinnieAI** (Disney) and/or **FionaAI** (Universal), builds the itinerary with **Patty**, and makes a client **quote PDF** (itinerary, prices, payment schedule, park maps) plus an internal commission estimate | "New request from the Pérez family: 6 days in Orlando in December, Disney and Universal" |
| `minnie-ai` (**MinnieAI**) | Walt Disney World specialist: guides you through tickets, Disney resorts, Lightning Lane, parties, dining and transfers, with current prices and sources | "MinnieAI, Disney options for 2 adults and 2 kids, Dec 13–16" |
| `fiona-ai` (**FionaAI**) | Universal Orlando specialist: tickets (Park-to-Park, Epic Universe), hotels with Express, Universal Express, Volcano Bay and events | "FionaAI, is a Premier hotel cheaper than buying Express for 4?" |
| `trip-scaffold` | Client/trip folders + an Excel **Trip Sheet**. Loads PDF vouchers and confirmations into it | "New client: María Pérez, Patagonia, Dec 2026" · "Load these vouchers" |
| `client-intake` | Questionnaire tailored to the destination and trip type (Word/PDF or WhatsApp text). Client answers are loaded into the Trip Sheet | "What should I ask a family going to Japan in April?" |
| `destination-research` | Sourced destination guide in Word, plus an optional client-ready PDF | "Research Albania for Argentine couples in September" |
| `social-content` | Posts ready to paste, Word drafts, Excel content calendar | "Plan my November Instagram" |
| `trip-summary` | Client PDF or internal Word summary of dates, payments due and deadlines; "what's due" across all clients | "What's due this week?" |
| `commissions` | **Providers & Commissions** workbook, rules taken from contracts, Excel commission report | "How much will I earn on the Pérez trip?" |
| `park-itinerary` (**Patty**) | Disney World and Universal Orlando day-by-day plan built around the group's kids' heights, Lightning Lane/Express, accessibility, fears and must-dos. Client PDF with a route map per day and a fixed-time table | "Patty, 4 days of parks for a family with kids aged 4 and 9 in December" |

## Commands (English and Spanish)

Type `/` in Claude to pick a skill directly. Each skill also has a Spanish command:

| Skill | Spanish command | Use it to |
|---|---|---|
| `trip-scaffold` | `/nuevo-viaje` | New client or trip, agency setup, load vouchers |
| `client-intake` | `/cuestionario-cliente` | Client questionnaire, or load the client's answers |
| `destination-research` | `/investigar-destino` | Destination guide, comparisons, trending destinations |
| `social-content` | `/contenido-redes` | Posts, reels, stories, content calendar |
| `trip-summary` | `/resumen-de-viaje` | Trip summary, or what's due this week |
| `commissions` | `/comisiones` | Commissions, providers, commission report |
| `park-itinerary` | `/itinerario-parques` (or `/patty`) | Disney and Universal park plan with maps |
| `fta` | `/cotizar` (or `/fta`) | New request → client memory → specialists → quote PDF |
| `minnie-ai` | `/minnie` | Disney World research and pricing |
| `fiona-ai` | `/fiona` | Universal Orlando research and pricing |

In Cowork and Claude Code, use the plugin prefix: `/travel-agent:resumen-de-viaje`. You don't need any command: describing the task in English or Spanish also works.

## How FTA works

```
Travel request ─▶ FTA ─▶ new client? ── yes ─▶ client folder + Client Profile
                    │                  └─ no ──▶ profile + summary of every past trip ("what I remember")
                    ├─▶ routes by destination, attractions and special needs
                    │      ├─ Walt Disney World ─▶ MinnieAI ┐  guide the agent through research and pricing
                    │      └─ Universal Orlando ─▶ FionaAI  ┘  (+ background research agents in Claude Code / Cowork)
                    ├─▶ Patty: one park plan for all park days
                    └─▶ quote: totals, per person, payments, commission estimate (internal only)
                           └─▶ Quote PDF (itinerary + prices + park maps) · Trip Sheet updated · profile updated
```

Prices are never built in. MinnieAI and FionaAI look them up for the client's dates (or use the agent's provider rates) and note the source. Anything unconfirmed is flagged for the agent to verify before sending.

## Install

**Claude chat or Cowork** (web or desktop app): open **Customize → Plugins → Add**, then either:
- **Add marketplace** and enter `fchambo/fta-claude-plugin`, then add **Travel Agent**, or
- **Upload plugin** and select `travel-agent.zip`.

**Claude Code:**

```bash
claude plugin marketplace add fchambo/fta-claude-plugin
claude plugin install travel-agent@fta-marketplace
```

In **Claude chat**, attach your files (Trip Sheet, vouchers, contracts) to the conversation and download the files Claude returns. In **Cowork** and **Claude Code**, Claude works directly in your agency folder.

The first time a skill needs files, Claude asks where the agent keeps client files and whether they work in English or Spanish, then sets up:

```
Agencia/
├── Clientes/María Pérez/2026-12 Patagonia/
│   ├── Ficha del Viaje - María Pérez - Patagonia.xlsx   (Viaje · Pasajeros · Reservas · Pagos · Vencimientos)
│   ├── 1 - Consulta … 8 - Fotos y Reseñas
├── Comisiones/Proveedores y Comisiones.xlsx               (Configuración · Proveedores · Productos · Incentivos)
├── Marketing/
└── Destinos/
```

Spreadsheets have dropdowns, real Excel dates and frozen headers, so the agent can edit them directly. Claude merges its changes without overwriting theirs, and won't touch a file that's open in Excel or Word.

## Requirements

Nothing to install in Claude chat. In Cowork and Claude Code, Python 3 is needed (preinstalled on macOS; on Windows get it from python.org). The first time, the plugin installs its libraries (`openpyxl`, `python-docx`, `reportlab`) into a private folder. PDFs are generated without Word.

## For developers

- Shared code lives in `tools/` at the repository root. Each skill carries its own copy in `scripts/` and `references/workspace.md`, because in Claude chat a skill only sees its own folder. After editing `tools/`, run `python3 tools/build.py`. CI-style check: `python3 tools/build.py --check`.
- `tools/travel_agent_tools/schema.py`: every sheet, column and dropdown (EN/ES)
- `tools/workspace.md`: shared rules every skill reads (folder mode vs chat mode)
- `tools/travel_agent_tools/parks.py` / `parks_pdf.py`: Patty's planner and PDF. Park data (attractions, schematic map positions, heights, tags, Lightning Lane tiers, typical waits) lives only in `travel-agent/skills/park-itinerary/scripts/parks/*.json`. Re-check it each season: closures, heights and Lightning Lane rules change
- `tools/travel_agent_tools/clients.py`: client lookup and Client Profile. `quote.py`: quote pricing (commission through `logic.commissions`) and the quote PDF, which appends Patty's plan through `parks_pdf.build_story`
- `travel-agent/agents/`: background research agents for MinnieAI and FionaAI (Claude Code and Cowork; in Claude chat the skills work alone)
- `build.py` copies the park data into the skills listed in `PARK_DATA_SKILLS` (`fta`, `minnie-ai`, `fiona-ai`), because in Claude chat they run park plans or park info on their own
- Don't add a top-level `bin/` folder: Claude chat and Cowork refuse plugins that have one.
