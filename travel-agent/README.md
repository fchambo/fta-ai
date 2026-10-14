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

## Install

```bash
claude plugin marketplace add fchambo/fta-claude-plugin
claude plugin install travel-agent@fta-marketplace
```

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

Python 3 (preinstalled on macOS; on Windows, get it from python.org). On first use, `bin/ta` creates a private environment with `openpyxl`, `python-docx` and `reportlab`. Nothing else to install, and PDFs are generated without Word.

## For developers

- `bin/ta`: CLI entry point (`ta --help`)
- `lib/travel_agent_tools/schema.py`: every sheet, column and dropdown (EN/ES) is defined in this one file
- `references/workspace.md`: shared conventions every skill reads
