---
name: dashboard
description: Build the travel agent's interactive dashboard, one HTML page that opens in any browser, with the next important dates and pending tasks for every client (departures, client payments due, free-cancellation deadlines, provider payments, trip deadlines, data to fix) and for the agent (their own to-do list in a My Tasks workbook, commissions to collect). The page filters by client, by who has to act and by date range. Also adds, updates and closes the agent's own tasks. Use when a travel agent asks for a dashboard, an agenda, what's coming up, what's pending, "my tasks", "remind me to…", or a view of all their clients. También en español: tablero, panel, agenda, qué tengo pendiente, próximas fechas, mis tareas, recordame, agregar una tarea, ver todos mis clientes.
---

# Dashboard

First read `references/workspace.md` in this skill's folder (`${CLAUDE_SKILL_DIR}/references/workspace.md`): it says how to work in **folder mode** (Claude Code, Cowork) and **chat mode** (Claude chat, where files come as attachments and go back as downloads). In this skill and that file, `ta` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ta.py"`. If that path doesn't resolve, as can happen in Claude chat where the skill folder is copied into the sandbox, use `scripts/ta.py` inside the copied skill folder.

The dashboard is **one HTML file** that the agent opens in their browser. It needs no internet and no installation. `ta dashboard` reads the files, works out every date and writes the page. You don't write any HTML.

## What goes on it

| Where it comes from | What the agent sees | Who acts |
|---|---|---|
| Each active Trip Sheet (not *closed* or *cancelled*) | Departure and return, booking start dates | Key dates |
| Payments sheet, payer *client*, not paid | Client payments due, plus the client's balance on their card | Client |
| Payments sheet, payer *me (agent)*, not paid | Provider payments due | Me |
| Bookings sheet, free cancellation until | The date free cancellation ends | Me |
| Deadlines sheet, not done | Trip deadlines (final names, quote validity…) | Me |
| Trip Sheet data checks | Missing confirmation numbers, passports expiring, payments that don't add up | Me, with no date |
| **My Tasks** workbook (`My Tasks.xlsx` / `Mis Tareas.xlsx`, in the agency folder) | The agent's own tasks, with or without a client and a due date, with priority | Me |
| Providers & Commissions workbook (optional) | Commissions still to collect and when they're expected | Me |

The page has six totals at the top: overdue, due in 7 days, trips in 30 days, what clients owe, commissions to collect, and open tasks. Clicking a total filters the agenda. Below them are the filters: who acts (everything / my tasks / client to-dos / key dates), client, date range and search. The **agenda** is grouped into overdue, today, next 7 days, 8–14 days, later, no date, and things to fix. A **card per client** shows the departure countdown, the balance due and their next items. **Hide amounts** blurs every amount for screen sharing. Countdowns use the date the page is opened, and the page warns when its data is 2 or more days old.

## Build it

**Folder mode:**
1. Find the agency folder (where `.travel-agent.json` is). If there's none, follow **trip-scaffold** to set it up first.
2. Run `ta dashboard "<agency folder>"`. It writes `Dashboard.html` (or `Tablero.html` in a Spanish workspace) in the agency folder, replacing the previous one. Add `--out <file>` to save it elsewhere.
3. If the result's `warnings` say there's no My Tasks workbook, run `ta init "<agency folder>"`. It's safe on an existing workspace and only creates what's missing. Then build again.
4. Give the agent the file path and tell them to open it in their browser and bookmark it. In Claude Code on a Mac you can offer to open it with `open "<path>"`.

**Chat mode:**
1. Ask the agent to attach every active Trip Sheet, their My Tasks workbook and, for commissions, the Providers & Commissions workbook.
2. Run `ta dashboard <every attached .xlsx> --out "<outputs folder>/Dashboard.html"` (`Tablero.html` in Spanish), and give the agent the download.
3. If they have no My Tasks workbook yet, create one: `ta init /tmp/agency --lang <es|en>`, then hand out `/tmp/agency/My Tasks.xlsx` (`Mis Tareas.xlsx`) and say to keep it in their agency folder.

## Tell the agent what matters

`ta dashboard` also returns counts and an `attention` list (overdue items first, then the next 7 days). Don't make the agent open the page to learn what's urgent. Write 3–6 lines in chat:
- Overdue items first, especially client payments and provider payments, with amounts.
- Free cancellation that ends in the next few days, because missing it costs money.
- How many data checks need fixing.
Then offer the usual next steps: payment-reminder messages to clients (ready for WhatsApp, in the client's language), or loading what's done.

## The agent's own tasks

The agent can ask at any time: "remind me to call the Pérez family on Friday", "add: renew my agency insurance by the 30th, high priority", "what's on my list?".

- Add or change tasks with `ta update-tasks "<My Tasks.xlsx>" '{"tasks":[{"task":"…","due":"YYYY-MM-DD","client":"…","priority":"high|normal|low","notes":"…"}]}'`. Rows match on the task text, so to change one, send the same text with the new fields.
- Close a task with `"done":"yes"`. Don't delete tasks: done tasks stay in the workbook as a record and drop off the dashboard.
- Turn relative dates ("Friday", "in two weeks") into real dates and repeat the date back to the agent. Use the exact client name from their folder (`ta client` finds it), so the task shows up on that client's card.
- Read the list with `ta read-tasks "<My Tasks.xlsx>"`.
- In chat mode, update a copy and give the agent the file to download (see `references/workspace.md`).
- After any change, offer to rebuild the dashboard.

## When the agent ticks items on the page

Ticks are saved only in that browser. They don't change the Excel files. The page has a **Copy done items for the assistant** button. When the agent pastes that list, update the files, ask for whatever's missing (the date a payment was received, a confirmation number), then rebuild:

| Kind on the page | Update |
|---|---|
| Client payment / Pay provider | `paid_date` on that row in the Trip Sheet's Payments sheet (ask the date if they didn't say) |
| Deadline | `"done": "yes"` on that row in Deadlines |
| Free cancellation | Nothing to mark. If the client confirmed, move the trip status forward (for example to *booked*) |
| Check | Fix the data (for example the booking's `confirmation`) |
| Commission | `commission_received_date` on the booking (see the **commissions** skill) |
| Task | `"done": "yes"` in My Tasks |

## Rules

- The dashboard is **internal**: it shows commissions, provider payments and every client's balance. Never send it to a client. For a client-facing summary, use **trip-summary**.
- Never invent a date or amount to fill a gap. Missing data shows up as a check to fix.
- The files are the source of truth. If the page and a file disagree, rebuild the page.
