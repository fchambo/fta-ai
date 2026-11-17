---
description: Cotizar un viaje con FTA. Desde la consulta del cliente hasta el PDF de la cotización con itinerario y precios (Disney con MinnieAI, Universal con FionaAI, parques con Patty). (Alias en español de fta.)
argument-hint: "[pegá la consulta del cliente]"
---

Spanish alias of the travel-agent **fta** skill.

1. Load the **fta** skill from the travel-agent plugin now, if it isn't loaded yet, and follow its instructions exactly, including the `references/workspace.md` it points to. Everything it says about files, chat mode and folder mode applies.
2. The travel request is whatever the agent typed after the command, plus any files they attached. If they gave nothing, introduce yourself as FTA in one line and ask them to paste the client's request.
3. Reply in **Spanish**, unless the agent writes in another language. Follow the **Language** rules in `references/workspace.md`: the agent's register (*vos*, *tú* or *usted*), Spanish file names, and the travel-trade glossary.

If the **fta** skill isn't available, say so in one line and ask the agent to check that the Travel Agent plugin is turned on in Customize → Plugins.
