---
name: commissions
description: Set up and maintain a travel agent's Providers & Commissions Excel workbook (percentage, net-rate markup, fixed fees and volume incentives per provider and product), load rules from provider contracts or rate sheets (PDF, Word, Excel), calculate expected commissions per trip or period into an Excel report, and track what's received, retained, pending or overdue. Use when a travel agent mentions commissions, providers, suppliers, net rates, markups, operators, consolidators, incentives, or asks "how much will I earn".
---

# Providers & commissions

First read `${CLAUDE_PLUGIN_ROOT}/references/workspace.md`. In this skill and that file, `ta` means `"${CLAUDE_PLUGIN_ROOT}/bin/ta"`. Always call it with that full path, quoted. Column meanings and rule types are in `references/schema.md`.

Everything lives in the **Providers & Commissions** workbook (`Commissions/` or `Comisiones/`). It has these sheets:
- **Settings**: agency name, language, currency, VAT on commissions %, withholding %
- **Providers**: one row per provider, with its default commission rule and how and when it pays
- **Products**: rules for specific products that override the provider default
- **Incentives**: volume tiers that earn an extra %
- **How it works**: a plain-language explanation for the agent

## Set up or edit providers

1. Run `read-providers` to see what's already there.
2. The agent can describe providers in chat, or share **contracts, rate sheets or commission agreements** (PDF, Word, Excel, emails). Read them and extract for each provider:
   - an ID
   - name and category
   - currency
   - how the agent gets paid: *collect gross and pay net*, *invoice the provider*, or *provider pays*
   - when they get paid, and how many days after
   - the default rule
   - any product overrides and volume incentives
3. Put the source in `notes` (e.g. "Contract 2026 §4.2: 12% on fares excl. taxes"), so the agent can check it later.
4. Show a summary table and confirm it with the agent, then run `update-providers`.
5. Remind them that each booking in a Trip Sheet must use the same **Provider ID**, and the same **Product** code for product rules to apply.

## Calculate

```bash
ta commissions "<Providers & Commissions.xlsx>" [Trip Sheet.xlsx …] --report "<agency>/Commissions/Commissions Report <YYYY-MM-DD>.xlsx"
```
With no Trip Sheets given, it includes every trip in the workspace. Use `--report` whenever the agent wants something to keep or share with their accountant.

Present the results in chat:
- **Per trip:** booking, provider, rule, client price, commission and expected date/status, then the total and the margin as a % of the price.
- **Per period:** totals by provider and currency, split into received, retained, pending and overdue.
- **Incentives:** the current tier and how much more volume is needed to reach the next one. This helps the agent decide which provider to push.
- **Every warning**, since each one means the expected income may be wrong (missing taxes amount, unknown provider, markup below target, expired contract).

## Track payments

When the agent says a commission arrived, set `commission_received_date` on that booking with `update-trip`.
- `retained` means the agent kept it when paying the provider net, so there's nothing to collect.
- `overdue` means it should be chased. Offer to draft a polite reminder to the provider.

## Guardrails

- Never put commissions or net rates in anything client-facing.
- These are estimates, not tax advice. Say so when VAT or withholding % in Settings are empty.
