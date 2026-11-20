---
name: knowledge-base
description: The travel agent's own Knowledge Base of rules, policies and preferences, kept as Word files tagged with hashtags (#DisneyPolicy, #Commissions, #Payments…) in their agency folder. Use when the agent wants to set it up, add, change or remove a rule or policy ("add to my #DisneyPolicy that the deposit is 25%", "save this as my cancellation policy", "from now on my rule is…"), tag a document they already have, or see or search what's in it ("what are my Universal policies?", "which tags do I use?"). Every other skill reads it on its own. También en español: base de conocimiento, mis reglas, mis políticas, agregar o cambiar una política, etiquetas, guardar como regla, qué dice mi política de Disney.
---

# Knowledge Base

First read `references/workspace.md` in this skill's folder (`${CLAUDE_SKILL_DIR}/references/workspace.md`): it says how to work in **folder mode** (Claude Code, Cowork) and **chat mode** (Claude chat, where files come as attachments and go back as downloads). In this skill and that file, `ta` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ta.py"`. If that path doesn't resolve, as can happen in Claude chat where the skill folder is copied into the sandbox, use `scripts/ta.py` inside the copied skill folder.

The Knowledge Base is the agent's: their agency's rules, supplier policies and the way they like to work, in their own words. **The Knowledge Base** section of `workspace.md` says how every skill reads it. This skill helps the agent **build, change and search** it. You only write what the agent asks you to write.

## Set it up

1. In folder mode, find the workspace (`.travel-agent.json`). If the agency folder has no `Knowledge Base` folder (`Base de Conocimiento`), run `ta init "<agency folder>"`: on an existing workspace it only adds what's missing. With no workspace at all, set one up as `workspace.md` says.
2. Explain it in three lines, in the agent's language: one Word file per subject (e.g. *Disney policies*, *Payments*, *My commissions*, *How I quote*); hashtags anywhere in the file say what it covers; they can drop in policy documents they already have (Word or PDF) and just add tags, or put the tag in the file name (`Cancellations #UniversalPolicy.pdf`).
3. Offer to start it for them: ask for their main rules on deposits and payments, cancellations, the suppliers they prefer, and how they like quotes presented, then save each one as below. Suggest tags only as examples; theirs are whatever they choose.

## Add, change or remove a rule

1. **Work out the file and the tags.** If the agent names a tag ("add to my #DisneyPolicy…"), run `ta kb "<agency folder>"` to see which file has it. Otherwise suggest a tag from those already in use (reuse `#Payments`; don't create `#Payment`) and confirm it in one line.
2. **Write the rule as the agent said it**, clear and short, in the workspace language. One rule per paragraph; start a line with `- ` for a bullet. Don't add rules they didn't ask for, and don't soften or "improve" theirs.
3. **Check for conflicts** before saving: load that tag (`ta kb … --tag <tag>`). If an existing rule says something different ("Deposit is 20%"), ask whether to **replace** it rather than adding a second one.
4. **Save:**
   - Add: `ta kb-note "<agency folder>" --tags DisneyPolicy --add "Deposit is 25%, balance 45 days before arrival."` The file that already has the first tag gets the text; a new tag makes a new file named after it (`Disney Policy.docx`). Name a file yourself with `--doc "Payments"`. More tags after the first one are added to the text.
   - Change: `ta kb-note "<agency folder>" --doc "Disney policies" --replace "Deposit is 20%" --with "Deposit is 25%"`. `--replace` takes text from one paragraph; quote more of it if `ta` says several match.
   - Remove: `ta kb-note "<agency folder>" --doc "Disney policies" --remove "<text of the paragraph>"`.
   - Tag a file the agent already has: `ta kb-note "<agency folder>" --doc "<file name>" --tags Cancellations UniversalPolicy`.
   - `ambiguous`: several files have that tag. Ask which one, then pass `--doc`.
   - PDFs can't be edited. Offer to put the new rule in a Word file with the same tag, and tell the agent the PDF still says the old thing.
   - If `ta` says the file is open in Word, ask the agent to close it.
5. **Tell the agent** in one line what changed and where ("Saved in *Disney policies.docx* under #DisneyPolicy."). In chat mode, the agent attaches the file to change (pass that `.docx` as the path), and you return the updated file to download and save in their Knowledge Base folder. To start a new file in chat mode, run `ta kb-note` on a scratch folder with `--doc` and hand that file over.

Never save on your own initiative, even when the agent corrects you mid-task. You can offer once ("Want me to save that as a rule in your Knowledge Base?"), and save only if they say yes.

## Find what's in it

- "Which tags do I use?" / "What's in my Knowledge Base?": `ta kb "<agency folder>"`. Show the tags with their files in a short list, plus untagged files, which skills only find by searching. Offer to tag them.
- "What's my Universal cancellation policy?": `ta kb … --tag UniversalPolicy --tag Cancellations`, or `--query "<words>"` when no tag fits, then answer quoting the agent's own words and naming the file.
- Point out what would help them, briefly: rules that contradict each other, two tags that mean the same thing (`#Commission` and `#Comisiones`), or a long untagged file.

## Rules

- **The agent's words.** Save rules exactly as meant. If a rule is ambiguous ("deposit 20%" of what?), ask before saving.
- **No client data.** The Knowledge Base is agency-wide. A client's preferences, health details or documents go in their **Client Profile** or trip folder, never here.
- **No prices that change.** A rule can say where prices come from ("my wholesaler's rate first") or a fixed fee the agent charges, but not today's price of a ticket or a hotel. Those are researched fresh every time.
