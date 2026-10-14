---
name: trip-summary
description: Summarize a client's trip from its Excel Trip Sheet, covering travel dates, bookings, payment due dates, cancellation deadlines and balances, as an internal checklist or a client-facing Word/PDF summary, or list what's due across all clients. Use when a travel agent asks for a trip summary, itinerary overview, payment schedule, "what's due", upcoming deadlines, or a status of their clients.
---

# Trip summary

First read `${CLAUDE_PLUGIN_ROOT}/references/workspace.md`. In this skill and that file, `ta` means `"${CLAUDE_PLUGIN_ROOT}/bin/ta"`. Always call it with that full path, quoted.

The dates are computed by `ta timeline`, so overdue and upcoming items are always correct. You write the words, and `ta docx` produces the files.

## One trip

1. Find the Trip Sheet. Use `ta find-trips <base>` and match the client, or ask.
2. Run `ta timeline "<Trip Sheet.xlsx>"`. It returns `events` (with a status of done, overdue, due_soon or upcoming), `payment_totals` per currency, and `checks` (data problems).
3. Pick the **audience**:
   - **Client-facing (PDF)**: a warm tone in the client's language. Include only what *they* need: dates, what's booked, what they owe and when, documents to bring, and the agent's contact. **Never** include provider payments, net rates or commissions, so leave out events where `payer` is `agent`.
   - **Internal (Word)**: everything, including provider payments, cancellation deadlines, the data checks, next actions, and the commission estimate from the **commissions** skill if useful.
4. Draft the markdown using this layout, then run `ta docx … --pdf` for the client version (Word only for internal):

   ```
   # <Client> — <Destinations>
   **<start> → <end>** · <n> nights · <n> travelers
   ## At a glance            (table: paid / pending / overdue / next due)
   ## Timeline               (table: date | status | item | amount)  ✅ done · 🔴 overdue · 🟡 within 14 days · ⚪ upcoming
   ## Bookings               (table: type | provider/product | dates | confirmation)
   ## Travelers & documents
   ## Next steps             (- [ ] checkboxes)
   ```
   Write dates in the format the agent's market uses (DD/MM/YYYY for Spanish workspaces).
5. Save to `7 - Itinerary & Summaries/`, e.g. `Trip Summary - <Client> - <YYYY-MM-DD>.pdf` or `Resumen del Viaje - <Client> - <fecha>.pdf`.

## All clients ("what's due this week?")

1. Run `ta timeline --base "<base>" --active`.
2. Merge every `overdue` and `due_soon` event into one table: client, date, item, amount and status. Put overdue client payments and expiring free-cancellation deadlines first.
3. Show it in chat. If the agent wants to keep it, also save it as an Excel file with `ta xlsx` (e.g. `Due this week - <date>.xlsx` in the agency root).
4. Offer to draft payment-reminder messages to clients with overdue balances, in their language and ready for WhatsApp.

## Data checks

Always report the `checks` from the timeline in internal output: missing confirmation numbers, payments without a due date, client payments due after departure, passports expiring within 6 months of return, and client payments that don't add up to the booking prices.
