# travel-agent: Claude plugin for freelance travel agents

Agents keep working in **Excel, Word and PDF**. Claude reads their vouchers, contracts and client replies, keeps their spreadsheets up to date, and writes their documents.

| Skill | What the agent gets | Try saying |
|---|---|---|
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

In Cowork and Claude Code, use the plugin prefix: `/travel-agent:resumen-de-viaje`. You don't need any command: describing the task in English or Spanish also works.

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
- Don't add a top-level `bin/` folder: Claude chat and Cowork refuse plugins that have one.
