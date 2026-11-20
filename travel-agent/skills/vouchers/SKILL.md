---
name: vouchers
description: Find and open the vouchers and confirmations saved in a client's trip (hotel, flight, park tickets, transfers, insurance), check which bookings still have no voucher, and load new vouchers or confirmations (PDF, Word, email, screenshots) into the trip's Excel Trip Sheet. Use when a travel agent asks for a voucher, a confirmation number or a booking document ("send me the Pérez hotel voucher", "where's the flight e-ticket?"), asks which vouchers are missing, or shares vouchers or confirmations to record. También en español: buscar, abrir o recuperar un voucher, pasame el voucher, número de confirmación, qué vouchers faltan, cargar vouchers o confirmaciones en la ficha del viaje.
---

# Vouchers

First read `references/workspace.md` in this skill's folder (`${CLAUDE_SKILL_DIR}/references/workspace.md`): it says how to work in **folder mode** (Claude Code, Cowork) and **chat mode** (Claude chat, where files come as attachments and go back as downloads). In this skill and that file, `ta` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ta.py"`. If that path doesn't resolve, as can happen in Claude chat where the skill folder is copied into the sandbox, use `scripts/ta.py` inside the copied skill folder.

Every trip keeps its vouchers in its `4 - Bookings & Vouchers` folder (`4 - Reservas y Vouchers`), and every booking is a row in the Trip Sheet's **Bookings** tab. This skill does two things with them: **find and open** vouchers already saved, and **load** new ones into the Trip Sheet. Creating the client, the trip and its folders is the **trip-scaffold** skill's job: if the trip doesn't exist yet, set it up there first.

Run `ta lessons "<agency folder>" --skill vouchers` before you start and follow what it returns (see **Learning from the agent's feedback** in `workspace.md`).

## Find and open vouchers

1. **Work out what the agent wants:** the client, and which voucher (a provider, a product such as "Pop Century", a type such as hotel or flight, or a confirmation number). "All the Pérez vouchers" is fine too.
2. **Search.** In folder mode, find the workspace (`.travel-agent.json`) and run:

   ```
   ta vouchers "<agency folder>" --client "<client>" [--query "<words>"] [--active]
   ```

   Pass a trip folder or a Trip Sheet instead of the agency folder when you already know the trip. `--query` matches every word, in any order, ignoring accents and case, against file names and the bookings' provider, product, confirmation number and type (in English or Spanish, so "vuelo" finds flights). Without `--client`, it searches every trip.

   The result lists, per trip (most recent first), each **file** with the **booking** it belongs to (matched by the confirmation number, booking ID or product in the file name), plus `bookings_without_file` and `files_without_booking`.
   - `client_not_found` or `ambiguous`: show the candidates and ask which client.
   - `nothing_found`: search again with fewer words, then without `--query`, and show what the trip has.
   - Several trips or files match: list them (client, trip, file, booking, dates) and ask which one, unless the agent asked for all of them.
   - A file name says nothing useful ("scan001.pdf"): read the candidate PDFs and images in that folder with your own file reading until you find the right one, and suggest renaming it (see below).
3. **Open it** in the way the agent can use it:
   - **Claude Code on the agent's computer:** `ta open "<file>" …` opens it in their default app (Preview, Acrobat, Word).
   - **Cowork:** you can't open apps on their screen. Give the full path of each file as a link they can click, and say which folder it's in.
   - **Chat mode:** you can't see the agent's computer. If they attached the Trip Sheet, tell them which file to look for and in which folder (`Clients/<Client>/<Trip>/4 - Bookings & Vouchers/`). If they attached the voucher itself, read it.
4. **Answer what they needed it for.** Often the agent wants a detail rather than the file: read the voucher and give the confirmation number, check-in time, address or what's included, quoting it exactly as written. If they're sending it to the client, offer a short message in the client's language (`client_language`) to go with it.
5. **Point out gaps** in one line when the trip is booked or about to travel: bookings without a voucher ("No voucher yet for B3, Epic Universe tickets") and documents not linked to any booking. Offer to load the missing ones when the agent has them.

Never send a voucher, or any file from `5 - Documents (private)`, to anyone yourself. The agent decides what goes to the client.

## Load new vouchers and confirmations

When the agent shares booking documents (PDF vouchers, airline e-tickets, hotel confirmations, provider invoices, forwarded emails, screenshots):

1. **Find the trip** with `ta client` or `ta vouchers --client`. If it doesn't exist yet, create it with the **trip-scaffold** skill first.
2. Read each file: use your own file reading for PDFs and images, and `ta read-doc` for .docx and .xlsx.
3. Extract the bookings: type, provider, product, confirmation number, dates, passengers, nights, client price, taxes, net, currency and free-cancellation deadline. Also extract **payments** (deposit and balance due dates) and any deadlines (final names, ticketing time limit). If a document matches a booking already in the Trip Sheet (same confirmation number), update that row instead of adding a new one.
4. Match `provider` to an existing ID in the Providers workbook. If none fits, ask whether to add the provider.
5. Before writing, show the agent a short table of what you extracted and ask them to confirm amounts and dates. Mistakes here end up in their summaries and commissions.
6. Run `update-trip`.
7. **Save the files** (folder mode) into the trip's `4 - Bookings & Vouchers` folder if they aren't already there, named so the next search finds them: `<Type> - <Product> - <Confirmation #>.<ext>`, for example `Hotel - Pop Century - DIS-448812.pdf` (Spanish: `Hotel - Pop Century - DIS-448812.pdf`, `Vuelo - EZE-MCO - XKQ7PL.pdf`). Never rename a file the agent already saved without asking. In chat mode, return the updated Trip Sheet for download and tell the agent to save the vouchers in that folder with those names.
8. Tell the agent what changed in one or two lines (e.g. "Added 2 bookings and the balance due on 28/11 to the Trip Sheet; saved both vouchers").

## Rules

- **Exact details.** Confirmation numbers, names, dates and times go to the agent exactly as the voucher shows them. If two documents disagree (the voucher and the Trip Sheet), say so and ask which is right.
- **Privacy.** Vouchers carry personal data. Store only the last 4 digits of a passport, as `workspace.md` says, and never put net rates or commissions in a message for the client.
