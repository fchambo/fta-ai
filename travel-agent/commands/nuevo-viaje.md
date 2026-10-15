---
description: Crear la carpeta y la Ficha del Viaje de un cliente nuevo, configurar la agencia o cargar vouchers y confirmaciones en la Ficha del Viaje. (Alias en español de trip-scaffold.)
argument-hint: "[cliente, destino, mes]"
---

Spanish alias of the travel-agent **trip-scaffold** skill.

1. Load the **trip-scaffold** skill from the travel-agent plugin now, if it isn't loaded yet, and follow its instructions exactly, including the `references/workspace.md` it points to. Everything it says about files, chat mode and folder mode applies.
2. The agent's request is whatever they typed after the command, plus any files they attached. If the agent gave no details, ask for the client's name, the destination and the travel month. If they attached vouchers or confirmations, load them into the Trip Sheet.
3. Reply in **Spanish**, unless the agent writes in another language. Follow the **Language** rules in `references/workspace.md`: the agent's register (*vos*, *tú* or *usted*), Spanish file names, and the travel-trade glossary.

If the **trip-scaffold** skill isn't available, say so in one line and ask the agent to check that the Travel Agent plugin is turned on in Customize → Plugins.
