---
description: Calcular cuánto vas a ganar por viaje o período, armar el reporte de comisiones en Excel, cargar proveedores y contratos, o registrar una comisión cobrada. (Alias en español de commissions.)
argument-hint: "[cliente, período o proveedor]"
---

Spanish alias of the travel-agent **commissions** skill.

1. Load the **commissions** skill from the travel-agent plugin now, if it isn't loaded yet, and follow its instructions exactly, including the `references/workspace.md` it points to. Everything it says about files, chat mode and folder mode applies.
2. The agent's request is whatever they typed after the command, plus any files they attached. If the agent attached a contract or rate sheet, add or update that provider. If they named a client or period, calculate those commissions. Otherwise ask what they need.
3. Reply in **Spanish**, unless the agent writes in another language. Follow the **Language** rules in `references/workspace.md`: the agent's register (*vos*, *tú* or *usted*), Spanish file names, and the travel-trade glossary.

If the **commissions** skill isn't available, say so in one line and ask the agent to check that the Travel Agent plugin is turned on in Customize → Plugins.
