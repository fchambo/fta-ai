---
name: destination-research
description: Research a travel destination for a freelance travel agent, covering best season, entry requirements, getting there, where to stay, experiences, costs, risks, and which client profiles it suits, then save it as a reusable Word destination guide (optionally a client-ready PDF). Use when a travel agent asks to research, compare or learn about a destination, find new or trending destinations to sell, or check if a destination fits a client. También en español: investigar o comparar destinos, guía de destino, cuándo conviene viajar, requisitos de entrada o visa, destinos de moda para vender, si un destino le sirve a un cliente.
---

# Destination research

First read `references/workspace.md` in this skill's folder (`${CLAUDE_SKILL_DIR}/references/workspace.md`): it says how to work in **folder mode** (Claude Code, Cowork) and **chat mode** (Claude chat, where files come as attachments and go back as downloads). In this skill and that file, `ta` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ta.py"`. If that path doesn't resolve, as can happen in Claude chat where the skill folder is copied into the sandbox, use `scripts/ta.py` inside the copied skill folder.

Produce a guide a travel agent can **sell from**, not just a tourist overview. Save each guide once and reuse it.

## Before researching

- Look in `Destinations/` (or `Destinos/`) for an existing guide. Read it with `ta read-doc`. If it's less than 90 days old, update only what's stale (prices, entry rules, safety advisories) instead of starting over.
- Clarify the angle if it isn't obvious: a specific client (`read-trip` their Trip Sheet), a season, a budget level, or "trending destinations to add to my offer".

## Research rules

- Use web search for anything that changes: **entry and visa rules, health requirements, travel advisories, airline routes, and prices**. Prefer official sources (government immigration and foreign-affairs sites, tourism boards, airline route pages), and **cite them with the access date**.
- Give entry requirements **for the client's nationality**. If you don't know it, ask, or list the agent's main markets.
- Mark anything uncertain as *to verify with provider*. Never make up visa rules or prices.

## Guide structure

Draft it in markdown, then save it with `ta docx` as `Destinations/<Destination> - Guide.docx` (Spanish: `Destinos/<Destino> - Guía.docx`). Put the research date under the title. Write the guide in the workspace language, and a client PDF in the client's language.

1. **Snapshot**: one paragraph pitch, best for (couples, families, adventure, luxury...), ideal trip length
2. **When to go**: month-by-month table (weather · crowds · price level · events), plus months to avoid and why
3. **Entry & health**: passport validity, visa/eTA, vaccines, insurance requirements (cited)
4. **Getting there & around**: main airports, typical routes and layovers from the agent's market, internal transport, driving
5. **Where to stay**: areas or bases with pros and cons, and accommodation styles by budget
6. **Experiences**: signature experiences, hidden gems, things that need advance booking (permits, popular restaurants, limited-capacity tours)
7. **Sample itineraries**: 2–3 options (short, classic, extended), day by day in one line each
8. **Budget guide**: per person per day at value, mid and luxury levels, in the agent's currency, with the date
9. **Selling points & objections**: the hooks that sell it, common client worries and how to answer them
10. **Risks & watch-outs**: safety, scams, seasonal issues, strikes, overtourism rules or fees
11. **Suppliers to consider**: types of operators/DMCs. Cross-check the Providers & Commissions workbook (`read-providers`) and mention providers the agent already works with first
12. **Sources**: links with access dates

## Comparisons and trend scouting

- For "X vs Y", put the destinations side by side on season, cost, flight time, entry friction and best-fit profile, then give a recommendation for the client in question.
- For "new destinations to sell", propose 5–8 options with why now (new routes, visa changes, events, value), the target client and the margin opportunity. Offer to write a full guide for the ones the agent picks.

## For a specific client

When the research is for one client, also offer a **client-facing PDF**. It should be shorter and inspiring, cover only their dates and profile, leave out suppliers, margins and objections, and be saved in that trip's `2 - Research` folder (`ta docx … --pdf`).

When you're done, offer to turn the guide into social posts with the **social-content** skill.
