---
description: Tablero interactivo con las próximas fechas y pendientes de cada cliente y tuyos (pagos, vencimientos, cancelaciones, comisiones, tus tareas), o agregar y cerrar tus tareas. (Alias en español de dashboard.)
argument-hint: "[cliente], una tarea para agregar, o vacío para ver todo"
---

Spanish alias of the travel-agent **dashboard** skill.

1. Load the **dashboard** skill from the travel-agent plugin now, if it isn't loaded yet, and follow its instructions exactly, including the `references/workspace.md` it points to. Everything it says about files, chat mode and folder mode applies.
2. The agent's request is whatever they typed after the command, plus any files they attached. If they typed nothing, build the dashboard and say what's urgent. If they named a client, build it and point them to that client's card. If they described a task ("recordame…", "agregá…"), add it to their tasks first, then offer to rebuild the dashboard.
3. Reply in **Spanish**, unless the agent writes in another language. Follow the **Language** rules in `references/workspace.md`: the agent's register (*vos*, *tú* or *usted*), Spanish file names, and the travel-trade glossary.

If the **dashboard** skill isn't available, say so in one line and ask the agent to check that the Travel Agent plugin is turned on in Customize → Plugins.
