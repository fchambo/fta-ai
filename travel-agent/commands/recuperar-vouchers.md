---
description: Buscar y abrir los vouchers y confirmaciones de un viaje, ver qué reservas no tienen voucher, o cargar vouchers nuevos en la Ficha del Viaje. (Alias en español de vouchers.)
argument-hint: "[cliente] [qué voucher: hotel, vuelo, proveedor o nº de confirmación]"
---

Spanish alias of the travel-agent **vouchers** skill.

1. Load the **vouchers** skill from the travel-agent plugin now, if it isn't loaded yet, and follow its instructions exactly, including the `references/workspace.md` it points to. Everything it says about files, chat mode and folder mode applies.
2. The agent's request is whatever they typed after the command, plus any files they attached. If they attached vouchers or confirmations, load them into the Trip Sheet. Otherwise find and open the voucher they asked for. If they gave no details, ask for the client and which voucher they need.
3. Reply in **Spanish**, unless the agent writes in another language. Follow the **Language** rules in `references/workspace.md`: the agent's register (*vos*, *tú* or *usted*), Spanish file names, and the travel-trade glossary.

If the **vouchers** skill isn't available, say so in one line and ask the agent to check that the Travel Agent plugin is turned on in Customize → Plugins.
