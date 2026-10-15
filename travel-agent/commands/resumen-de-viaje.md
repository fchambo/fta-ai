---
description: Resumen del viaje de un cliente (fechas, reservas, pagos y vencimientos) en PDF para el cliente o checklist interno, o lo que vence esta semana en todos los clientes. (Alias en español de trip-summary.)
argument-hint: "[cliente] o qué vence esta semana"
---

Spanish alias of the travel-agent **trip-summary** skill.

1. Load the **trip-summary** skill from the travel-agent plugin now, if it isn't loaded yet, and follow its instructions exactly, including the `references/workspace.md` it points to. Everything it says about files, chat mode and folder mode applies.
2. The agent's request is whatever they typed after the command, plus any files they attached. If the agent named a client, summarize that trip and ask whether it's for the client (PDF) or internal (Word). If they asked what's due, or named no client, show what's due across all clients.
3. Reply in **Spanish**, unless the agent writes in another language. Follow the **Language** rules in `references/workspace.md`: the agent's register (*vos*, *tú* or *usted*), Spanish file names, and the travel-trade glossary.

If the **trip-summary** skill isn't available, say so in one line and ask the agent to check that the Travel Agent plugin is turned on in Customize → Plugins.
