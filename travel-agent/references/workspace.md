# Workspace & office files: shared rules for every travel-agent skill

Travel agents work in **Excel, Word and PDF**. They never see JSON, YAML or Markdown files. Everything you hand them is an `.xlsx`, `.docx` or `.pdf` in their agency folder, or text they can paste into WhatsApp or email.

## The `ta` tool

All file work goes through one command, `ta`. The skill that sent you here gives its full path. It sets itself up on first run, which takes about 30 s.

| Command | Purpose |
|---|---|
| `ta init <base> --lang es --agency "Name" --currency USD` | Create the workspace folders and the Providers & Commissions workbook |
| `ta new-trip <base> "<Client>" "<Destination>" <YYYY-MM>` | Create the trip folders and Trip Sheet. Exits with code 2 if the trip already exists |
| `ta find-trips <base> [--active]` | List all Trip Sheets (status, dates) |
| `ta read-trip <file.xlsx>` / `read-providers <file.xlsx>` | Workbook → JSON (for you to read) |
| `ta update-trip <file.xlsx> '<json>'` / `update-providers …` | Merge changes into the workbook (see below) |
| `ta timeline <file.xlsx>…` or `--base <dir> --active` | Dated events, payment totals and data checks |
| `ta commissions <providers.xlsx> [trip.xlsx…] [--report out.xlsx]` | Commission calculation (all trips if none are given) |
| `ta docx <draft.md> <out.docx> [--pdf] [--footer "…"] [--title "…"]` | Your markdown → styled Word document (and PDF) |
| `ta xlsx '<json>' <out.xlsx>` | Generic tables → Excel file (`[{name, columns, rows}]`) |
| `ta read-doc <file.docx/.xlsx>` | Extract the text of a Word or Excel file |

Read **PDFs** (vouchers, confirmations, rate sheets, passports) with your own Read tool. Read images (screenshots of WhatsApp chats or tickets) the same way.

## Workspace

`init` creates the folders below (names follow the workspace language, English or Spanish). It writes the language to a hidden `.travel-agent.json`, and `ta` finds that file automatically from any path inside the workspace.

```
<agency folder>/
├── Clients|Clientes/<Client>/<YYYY-MM Destination>/
│   ├── Trip Sheet - <Client> - <Destination>.xlsx   ← the trip's source of truth
│   ├── 1 - Intake … 8 - Photos & Reviews
├── Commissions|Comisiones/Providers & Commissions.xlsx
├── Marketing/
└── Destinations|Destinos/
```

If there's no workspace yet, ask where the agent keeps client files (e.g. `~/Documents/Agencia`) and which language they want, then run `init`.

## Updating workbooks

- JSON keys are section names: `trip` (object), plus `travelers`, `bookings`, `payments` and `deadlines` (lists of objects). For the providers workbook they're `settings`, `providers`, `products` and `incentives`. Get the field keys from `read-trip`/`read-providers` output.
- Rows are **merged** by key: bookings by `id`, travelers by `name`, payments by `booking`+`description`, deadlines by `date`+`what`, providers by `id`, and products by `provider_id`+`product_id`. A row with a new key is appended. To overwrite a whole section, add `--replace bookings`.
- Dates: `YYYY-MM-DD` (DD/MM/YYYY is also accepted). Dropdown fields take the code (`booked`, `client`, `percentage`…) or the label in either language.
- If `ta` says the file is **open in Excel or Word**, ask the agent to close it. Never work around this, because their unsaved edits would be lost.
- After any update, briefly tell the agent what changed (e.g. "Added 3 bookings and 2 payments to the Trip Sheet").

## Producing documents

1. Write the content as markdown in your scratchpad or temp directory. The supported formatting is headings, bold/italic, bullets, numbered lists, `- [ ]` checkboxes, tables, `>` quotes and links.
2. Run `ta docx draft.md "<trip folder>/<subfolder>/<Nice Name>.docx" [--pdf]`.
   - Use **`--pdf` for anything going to a client.** The PDF is generated directly and doesn't need Word.
   - Add `--footer "<agency name> · <license/legajo>"` when `agency_name` is set in the providers workbook Settings sheet.
3. Name files the way a person would: `Questionnaire - María Pérez.docx`, `Cuestionario - María Pérez.docx`, `Trip Summary 2026-10-14.pdf`. Don't use slugs.
4. Never leave the markdown draft in the agency folder.
5. Status markers ✅ 🔴 🟡 ⚪ render correctly in both the Word document and the PDF.

## Privacy

Trip Sheets and `5 - Documents (private)` contain personal data. Store only the **last 4 digits** of a passport number. Never put commissions or net rates in a client-facing file.
