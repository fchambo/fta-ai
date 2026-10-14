---
name: trip-scaffold
description: Set up a travel agency workspace or create the folders and Excel Trip Sheet for a new client trip, and load booking vouchers or confirmations (PDF, Word, email, screenshots) into that Trip Sheet. Use when a travel agent mentions a new client, inquiry or booking, asks to set up, organize or create folders for a trip, or shares vouchers or confirmations to record.
---

# Trip scaffold

First read `${CLAUDE_PLUGIN_ROOT}/references/workspace.md`, which explains the `ta` tool, folder layout and update rules. In this skill and that file, `ta` means `"${CLAUDE_PLUGIN_ROOT}/bin/ta"`. Always call it with that full path, quoted.

## New workspace (first time only)

If `ta find-trips <dir>` finds nothing and there's no `.travel-agent.json`, ask for:
- the folder where they keep client files (suggest `~/Documents/Agency` or `~/Documents/Agencia`)
- their working language (English or Spanish), agency/brand name, and main currency

Then run `ta init …` and tell them what was created. Ask them to fill in the **Providers & Commissions** workbook (or offer to do it with the **commissions** skill).

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
5. Suggest the next step, which is usually the **client-intake** questionnaire.

## Recording vouchers and confirmations

When the agent shares booking documents (PDF vouchers, airline e-tickets, hotel confirmations, provider invoices, forwarded emails, screenshots):

1. Read each file: use the Read tool for PDFs and images, and `ta read-doc` for .docx and .xlsx.
2. Extract the bookings: type, provider, product, confirmation number, dates, passengers, nights, client price, taxes, net, currency and free-cancellation deadline. Also extract **payments** (deposit and balance due dates) and any deadlines (final names, ticketing time limit).
3. Match `provider` to an existing ID in the Providers workbook. If none fits, ask whether to add the provider.
4. Before writing, show the agent a short table of what you extracted and ask them to confirm amounts and dates. Mistakes here end up in their summaries and commissions.
5. Run `update-trip`, and save the original files into `4 - Bookings & Vouchers` if they aren't already there.
