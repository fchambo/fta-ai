---
description: Armar el cuestionario para un cliente según su destino y tipo de viaje (Word, PDF o WhatsApp), o cargar las respuestas que mandó el cliente. (Alias en español de client-intake.)
argument-hint: "[cliente o destino, canal]"
---

Spanish alias of the travel-agent **client-intake** skill.

1. Load the **client-intake** skill from the travel-agent plugin now, if it isn't loaded yet, and follow its instructions exactly, including the `references/workspace.md` it points to. Everything it says about files, chat mode and folder mode applies.
2. The agent's request is whatever they typed after the command, plus any files they attached. If the agent attached or pasted the client's answers, process them (Mode B). Otherwise build the questionnaire (Mode A) and ask for the destination, trip type and channel if they're missing.
3. Reply in **Spanish**, unless the agent writes in another language. Follow the **Language** rules in `references/workspace.md`: the agent's register (*vos*, *tú* or *usted*), Spanish file names, and the travel-trade glossary.

If the **client-intake** skill isn't available, say so in one line and ask the agent to check that the Travel Agent plugin is turned on in Customize → Plugins.
