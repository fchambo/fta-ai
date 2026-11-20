# Workspace & office files: shared rules for every travel-agent skill

Travel agents work in **Excel, Word and PDF**. They never see JSON, YAML or Markdown files. Everything you hand them is an `.xlsx`, `.docx` or `.pdf` in their agency folder, or text they can paste into WhatsApp or email.

## The `ta` tool

All file work goes through one Python script, `ta.py`, in this skill's `scripts/` folder. The skill gives its full path; below it's written `ta`. Run it with `python3` (on Windows, `python` if `python3` isn't found). Where the needed libraries aren't already installed, it sets itself up on first run, which takes about 30 s.

| Command | Purpose |
|---|---|
| `ta init <base> --lang es --agency "Name" --currency USD` | Create the workspace folders and the Providers & Commissions workbook |
| `ta new-trip <base> "<Client>" "<Destination>" <YYYY-MM>` | Create the trip folders and Trip Sheet. Exits with code 2 if the trip already exists |
| `ta find-trips <base> [--active]` | List all Trip Sheets (status, dates) |
| `ta read-trip <file.xlsx>` / `read-providers …` / `read-tasks …` | Workbook → JSON (for you to read) |
| `ta update-trip <file.xlsx> '<json>'` / `update-providers …` / `update-tasks …` | Merge changes into the workbook (see below) |
| `ta timeline <file.xlsx>…` or `--base <dir> --active` | Dated events, payment totals and data checks |
| `ta commissions <providers.xlsx> [trip.xlsx…] [--report out.xlsx]` | Commission calculation (all trips if none are given) |
| `ta docx <draft.md> <out.docx> [--pdf] [--footer "…"] [--title "…"]` | Your markdown → styled Word document (and PDF) |
| `ta xlsx '<json>' <out.xlsx>` | Generic tables → Excel file (`[{name, columns, rows}]`) |
| `ta read-doc <file.docx/.xlsx>` | Extract the text of a Word or Excel file |
| `ta vouchers <agency folder, trip folder or Trip Sheet> [--client "<name>"] [--query "<words>"] [--active]` | Vouchers saved in each trip's `4 - Bookings & Vouchers` folder, linked to their bookings, plus bookings with no voucher (vouchers skill) |
| `ta kb <agency folder or files> [--tag <tag>…] [--query "<words>"] [--all]` | The agent's **Knowledge Base**: files and the tags in use; with `--tag`, `--query` or `--all`, the matching files' text (see **The agent's Knowledge Base**) |
| `ta kb-note <agency folder> --tags <Tag> --add "<text>"` · `--doc "<file>" --replace "<old>" --with "<new>"` · `--remove "<old>"` | Add, change or remove a rule in a Knowledge Base Word file, **only when the agent asks** (knowledge-base skill) |
| `ta open <file>…` | Open files in the agent's default app (Claude Code on their own computer only) |
| `ta parks` · `park-info <park> [--party …]` | Theme parks with planning data, and who can ride what (park-itinerary skill only) |
| `ta park-plan <request.json> [--out plan.json]` · `park-pdf <plan.json> <out.pdf>` | Plan park days, and render the client PDF with route maps (park-itinerary skill only) |
| `ta client <base> "<name>" [--create]` | Find a client (ignores accents and case): their profile and a summary of every past trip. `--create` makes the client folder and profile |
| `ta quote <quote.json> [--providers <xlsx>]` | Price a quote: totals, per person, payment schedule, **internal** commission estimate, warnings, and rows ready for `update-trip` |
| `ta quote-pdf <quote.json> <out.pdf> [--plan plan.json] [--palette …]` | Client quote PDF: itinerary, prices, payments, conditions, plus Patty's park plan with `--plan` |
| `ta dashboard <agency folder or .xlsx files…> [--out file.html]` | The agent's **internal** interactive dashboard (one HTML file): next dates and pending tasks per client and for the agent, plus what needs attention as JSON (dashboard skill) |

Read **PDFs** (vouchers, confirmations, rate sheets, passports) and images (screenshots of WhatsApp chats or tickets) with your own file-reading ability.

## Where you're running: pick the mode first

**Folder mode (Claude Code, or Cowork with a folder selected).** You can read and write the agent's own files, so everything lives in their agency folder.

**Chat mode (Claude on the web, desktop Chat tab, or mobile).** You run in a sandbox and can't see the agent's computer. You're in chat mode if the agent attached files to the conversation, or if there's an uploads/outputs folder such as `/mnt/user-data/`. In chat mode:

- **Files come in as attachments.** Look in the uploads folder (often `/mnt/user-data/uploads`). Uploaded files may be read-only, so **copy a workbook to the outputs folder before updating it** and update the copy.
- **Files go out as downloads.** Save every file you produce, including updated Trip Sheets, in the outputs folder (often `/mnt/user-data/outputs`), so the agent can download it. Use the same human file name as the original.
- **The agent keeps the files.** After updating a Trip Sheet or the Providers workbook, say clearly: *"Download the updated file and replace your copy."* At the start of trip work, ask them to attach the latest Trip Sheet (and the Providers & Commissions workbook for commissions).
- **New workspace or trip:** run `ta init` and `ta new-trip` in a scratch folder (e.g. `/tmp/agency`), then copy the new workbook(s) to the folder you hand files out from. Tell the agent which folder on their computer to save each one in, using the layout below. They can create the folders themselves, or you can zip the scratch folder for them.
- **Across many clients** ("what's due this week?"), the agent has to attach every active Trip Sheet. If they do this often, mention that **Cowork** in the Claude desktop app can work directly in their agency folder.

## Workspace layout

`init` creates the folders and workbooks below, named in the workspace language (English or Spanish). Running it again on an existing workspace only adds what's missing, such as the Knowledge Base folder. It writes the language to a hidden `.travel-agent.json`, and `ta` finds that file automatically from any path inside the workspace. A workbook's own sheet names tell `ta` its language, so a single uploaded file works without the workspace.

```
<agency folder>/
├── Clients|Clientes/<Client>/
│   ├── Client Profile.md                             ← what we remember about the client (Claude keeps it)
│   └── <YYYY-MM Destination>/
│       ├── Trip Sheet - <Client> - <Destination>.xlsx   ← the trip's source of truth
│       ├── 1 - Intake … 8 - Photos & Reviews
├── Commissions|Comisiones/Providers & Commissions.xlsx
├── My Tasks.xlsx | Mis Tareas.xlsx                    ← the agent's own to-dos (dashboard skill)
├── Dashboard.html | Tablero.html                      ← built by `ta dashboard`, open in a browser
├── Knowledge Base|Base de Conocimiento/            ← the agent's own rules and policies, tagged #DisneyPolicy… (every skill reads it)
├── Marketing/
└── Destinations|Destinos/
```

In folder mode, if there's no workspace yet, ask where the agent keeps client files (e.g. `~/Documents/Agencia`) and which language they want, then run `init`.

## Language (English / Spanish)

Every skill works in English and Spanish. Decide three things separately:

1. **Talking to the agent:** use the language the agent writes in. If it changes mid-conversation, follow the switch.
2. **Agent-facing files** (Trip Sheet, providers workbook, internal summaries, reports, guides): use the **workspace language**. In folder mode it's in `.travel-agent.json`; otherwise it's the language of the workbook's sheet names (`ta` reports it as `_lang`/`lang`). Never mix languages inside one workbook: new rows use the same dropdown labels as the existing ones.
3. **Client-facing material** (questionnaires, client summaries, WhatsApp messages, reminders): use the **client's language** (`client_language` in the Trip Sheet). If it's empty, ask the agent and save the answer there. A Spanish-speaking agent can have English-speaking clients, and the other way round.

**Spanish register.** Ask the agent once which form they use with clients, then keep it:
- **vos** (Argentina, Uruguay, Paraguay, much of Central America): *"¿Cuándo querés viajar?"*, *"Contame"*
- **tú** (Spain, Mexico, Colombia, Peru, Chile, most of the Caribbean): *"¿Cuándo quieres viajar?"*, *"Cuéntame"*
- **usted** (formal or corporate clients, older travelers): *"¿Cuándo desea viajar?"*

Agent-facing text defaults to the agent's own form. Use neutral Spanish when you don't know.

**Formats**
| | English | Spanish |
|---|---|---|
| Dates in text and documents | 14 Oct 2026 or 2026-10-14 | 14/10/2026 |
| Money | USD 1,234.50 | USD 1.234,50 |
| Workbook dates | Real Excel dates (`ta` applies the right display format) | Same |

**File names.** Use these and replace the parts in angle brackets:
| Document | English | Spanish |
|---|---|---|
| Trip Sheet | `Trip Sheet - <Client> - <Destination>.xlsx` | `Ficha del Viaje - <Cliente> - <Destino>.xlsx` |
| Providers workbook | `Providers & Commissions.xlsx` | `Proveedores y Comisiones.xlsx` |
| Questionnaire | `Questionnaire - <Client>.docx` | `Cuestionario - <Cliente>.docx` |
| Client summary | `Trip Summary - <Client> - <YYYY-MM-DD>.pdf` | `Resumen del Viaje - <Cliente> - <AAAA-MM-DD>.pdf` |
| Internal checklist | `Internal Checklist - <Client> - <YYYY-MM-DD>.docx` | `Checklist Interno - <Cliente> - <AAAA-MM-DD>.docx` |
| Destination guide | `<Destination> - Guide.docx` | `<Destino> - Guía.docx` |
| Commission report | `Commissions Report <YYYY-MM-DD>.xlsx` | `Reporte de Comisiones <AAAA-MM-DD>.xlsx` |
| Content calendar | `Content Calendar - <YYYY-MM>.xlsx` | `Calendario de Contenidos - <AAAA-MM>.xlsx` |
| Post drafts | `Posts - <Topic> - <YYYY-MM>.docx` | `Publicaciones - <Tema> - <AAAA-MM>.docx` |
| Brand profile | `Brand Profile.docx` | `Perfil de Marca.docx` |
| What's due | `Due This Week - <YYYY-MM-DD>.xlsx` | `Vencimientos de la Semana - <AAAA-MM-DD>.xlsx` |
| Park plan | `Park Plan - <Client>.pdf` | `Plan de Parques - <Cliente>.pdf` |
| Quote | `Quote - <Client> - v<N>.pdf` | `Cotización - <Cliente> - v<N>.pdf` |
| Client profile | `Client Profile.md` (in the client folder) | `Perfil del Cliente.md` |
| Agent's tasks | `My Tasks.xlsx` (agency folder) | `Mis Tareas.xlsx` |
| Dashboard | `Dashboard.html` (agency folder) | `Tablero.html` |
| Knowledge Base folder | `Knowledge Base` (agency folder) | `Base de Conocimiento` |

**Travel-trade glossary.** Use the terms agents use, not literal translations:
| English | Spanish (LatAm) | Notes |
|---|---|---|
| deposit | seña | Spain: *depósito* or *paga y señal* |
| balance / final payment | saldo | |
| voucher | voucher | Not *cupón* |
| booking / reservation | reserva | |
| quote / proposal | cotización / presupuesto | |
| tour operator / wholesaler | operador / mayorista | |
| DMC / ground handler | receptivo | |
| consolidator | consolidador | |
| net rate | tarifa neta | |
| markup | markup / margen | |
| commission | comisión | |
| travel insurance / assistance | asistencia al viajero / seguro | In Argentina, *asistencia* |
| free cancellation until | cancelación sin cargo hasta | |
| ticketing time limit | plazo de emisión | |
| final names | nombres definitivos | |
| transfer | traslado | |
| layover | escala | |
| agency license number | legajo (AR) / número de licencia | Shown in document footers |
| fam trip | fam trip / viaje de familiarización | |
| rope drop (be there at opening) | llegar a la apertura (*rope drop*) | |
| height requirement | altura mínima | |

## The agent's Knowledge Base

Every agent works their own way. Their rules, policies and preferences live in the **Knowledge Base** folder (`Base de Conocimiento`) in the agency folder: Word files (and PDFs) the agent writes, with **hashtags** saying what each one covers, such as `#DisneyPolicy`, `#Commissions`, `#Payments` or `#Hotels`. A tag can go anywhere in the file or in its file name. The tags are the agent's own: any word works, and case, accents and dashes don't matter (`#Comisiones` is `#comisiones`).

**Before you start a task:**

1. Run `ta kb "<agency folder>"`. It lists every file with its tags, and every tag in use. In chat mode, ask the agent to attach the Knowledge Base files for this kind of task (or all of them, if there are few) along with the other files, and pass those files instead.
2. Load what applies: `ta kb "<agency folder>" --tag DisneyPolicy --tag Payments` returns those files' full text. Pick tags by meaning, not exact spelling: for a Disney quote, `#DisneyPolicy`, `#Disney`, `#Hotels`, `#Payments`, `#Commissions` or `#Cotizaciones` may all apply. If the result says the Knowledge Base is small, load all of it with `--all`. Find untagged files with `--query "<words>"`. A file marked `read_yourself` is a PDF whose text `ta` couldn't extract: read it with your own file reading.
3. Treat what you load as the agent's standing instructions. They take priority over this skill's defaults: if their `#DisneyPolicy` says the deposit is 25%, use 25%. When a rule changes what you do, say so in a few words, e.g. "(25% deposit, per your #DisneyPolicy.)". A rule never overrides the **hard rules**: never invent a price, never get around height limits or accessibility programs, and never show commission or net rates to a client. If following a rule would break one of these, tell the agent and follow the hard rule.
4. If two files disagree, or it's unclear whether a rule covers this case, ask the agent. Don't guess.

Check the Knowledge Base once per task, and skip files whose tags clearly don't fit (a `#SocialMedia` file isn't needed for a commission report). If there's no Knowledge Base yet, carry on with the skill's defaults; `ta init` creates the folder in an existing workspace.

**It's internal.** Use a policy in client-facing text only when it's meant for clients (cancellation terms, the payment schedule), and write it for the client. Rules about commissions and net rates never reach a client.

**Writing to it** happens only when the agent asks ("add to my #DisneyPolicy that…", "save this as a rule", "change the deposit in my policies to 30%"). Follow the **knowledge-base** skill. Never save anything on your own initiative. Facts about one client go in their **Client Profile**, not the Knowledge Base.

## Updating workbooks

- JSON keys are section names: `trip` (object), plus `travelers`, `bookings`, `payments` and `deadlines` (lists of objects). For the providers workbook they're `settings`, `providers`, `products` and `incentives`. Get the field keys from `read-trip`/`read-providers` output.
- Rows are **merged** by key: bookings by `id`, travelers by `name`, payments by `booking`+`description`, deadlines by `date`+`what`, providers by `id`, and products by `provider_id`+`product_id`. A row with a new key is appended. To overwrite a whole section, add `--replace bookings`.
- Dates: `YYYY-MM-DD` (DD/MM/YYYY is also accepted). Dropdown fields take the code (`booked`, `client`, `percentage`…) or the label in either language.
- In folder mode, if `ta` says the file is **open in Excel or Word**, ask the agent to close it. Never work around this, because their unsaved edits would be lost.
- After any update, briefly tell the agent what changed (e.g. "Added 3 bookings and 2 payments to the Trip Sheet").

## Producing documents

1. Write the content as markdown in a temp directory. The supported formatting is headings, bold/italic, bullets, numbered lists, `- [ ]` checkboxes, tables, `>` quotes and links.
2. Run `ta docx draft.md "<destination>/<Nice Name>.docx" [--pdf]`. In folder mode the destination is the right trip subfolder; in chat mode it's the folder you hand files out from.
   - Use **`--pdf` for anything going to a client.** The PDF is generated directly and doesn't need Word.
   - Add `--footer "<agency name> · <license/legajo>"` when `agency_name` is set in the providers workbook Settings sheet.
   - Use the agency's main brand color for client documents: `--color <first color of brand_colors>` from the same Settings sheet.
3. Name files the way a person would, using the file-name table in **Language**. Don't use slugs.
4. Never leave the markdown draft in the agency folder or the outputs folder.
5. Status markers ✅ 🔴 🟡 ⚪ render correctly in both the Word document and the PDF.

## Privacy

Trip Sheets and `5 - Documents (private)` contain personal data. Store only the **last 4 digits** of a passport number. Never put commissions or net rates in a client-facing file. The Knowledge Base is agency-wide: never write client names, health details or other personal data in it.
