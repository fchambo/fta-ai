---
name: client-intake
description: Build a tailored questionnaire for a travel client based on the destinations and trip type they want (as a Word or PDF form, or a WhatsApp or email message), then load the client's answers into the trip's Excel Trip Sheet. Use when a travel agent needs to know what to ask a client, prepare an intake form, qualify a new lead, or process answers a client sent back (filled Word or PDF, email or WhatsApp chat).
---

# Client intake

First read `references/workspace.md` in this skill's folder (`${CLAUDE_SKILL_DIR}/references/workspace.md`): it says how to work in **folder mode** (Claude Code, Cowork) and **chat mode** (Claude chat, where files come as attachments and go back as downloads). In this skill and that file, `ta` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ta.py"`. If that path doesn't resolve, as can happen in Claude chat where the skill folder is copied into the sandbox, use `scripts/ta.py` inside the copied skill folder.

Ask clients the questions that matter for *their* trip, and nothing more. A beach week in Cancún and a multi-country trip through Southeast Asia need very different questions.

## Mode A: Create the questionnaire

1. **Gather context:** destinations, rough dates, number of travelers, the client's language, and how it will be sent. If the trip has a Trip Sheet, run `read-trip` and don't ask for anything already filled in.
2. **Choose the questions** from `references/question-bank.md`:
   - Always include the **Core** block.
   - Add every trip-type block that applies.
   - Add **destination-specific** questions you work out yourself:
     - entry rules for their nationality (visa, eTA/ESTA/ETIAS, passport validity, vaccines)
     - season conflicts with their dates (rainy season, hurricanes, peak prices, local holidays)
     - altitude, long layovers, or route order on multi-stop trips, but only when they change a decision
   - Aim for **12–20 questions**. Mark 3–5 as *needed to quote*.
3. **Deliver in the format the agent asked for:**
   - **Word form**, the default. Use the agent's first person and a warm greeting. Group questions under headings, put a blank answer line or checkbox options (`- [ ] Option`) under each one, and close with the next step and the agent's contact. Save it as `1 - Intake/Questionnaire - <Client>.docx` (Spanish: `Cuestionario - <Client>.docx`). Add `--pdf` if they will email it as a PDF.
   - **WhatsApp**: give the text in chat, ready to paste. Use 2–3 short messages with numbered questions and no tables. Offer to also save the Word version.
   - **Email**: give the subject and body in chat, ready to paste.
4. Write it in the **client's language**.

## Mode B: Load the answers

The client may reply with a filled-in Word or PDF form, an email, a WhatsApp export or screenshots, or the agent may paste the text.

1. Read the reply: `ta read-doc` for .docx, and the Read tool for PDFs and images.
2. Map the answers into the Trip Sheet with `update-trip`: the `trip` fields, one `travelers` row per passenger, and anything else under `trip.notes`. Store only the **last 4 digits** of passport numbers.
3. Save the client's original reply file into `1 - Intake/` if it isn't already there.
4. Reply to the agent with:
   - **Ready to quote?** Yes or no, and what's still missing
   - **Red flags**, such as a passport expiring within 6 months of return, a visa lead time longer than the time until departure, a budget that doesn't fit the destination or season, or a minor traveling without both parents (needs a notarized permission letter)
   - **Follow-up message** for the missing items, ready to paste into WhatsApp or email
