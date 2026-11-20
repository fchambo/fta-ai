---
name: social-content
description: Create social media content for a freelance travel agent, including Instagram posts and carousels, Reels/TikTok scripts, stories, Facebook and LinkedIn posts, WhatsApp broadcast messages, and monthly content calendars (delivered in chat, as Word drafts, or as an Excel calendar). Use when a travel agent asks for posts, captions, hashtags, reels, content ideas, a content calendar, or promotion of a destination, offer or client trip. También en español: posteos, publicaciones, carrusel, reels, historias, hashtags, ideas de contenido, calendario de contenidos, difusión de WhatsApp, promocionar un destino u oferta.
---

# Social media content

Content that builds trust in the agent as *the* expert and gets people to message them. It shouldn't read like a generic travel-inspiration account.

First read `references/workspace.md` in this skill's folder (`${CLAUDE_SKILL_DIR}/references/workspace.md`): it says how to work in **folder mode** (Claude Code, Cowork) and **chat mode** (Claude chat, where files come as attachments and go back as downloads). In this skill and that file, `ta` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ta.py"`. If that path doesn't resolve, as can happen in Claude chat where the skill folder is copied into the sandbox, use `scripts/ta.py` inside the copied skill folder.

**The agent's Knowledge Base.** Check it as **The agent's Knowledge Base** in `references/workspace.md` says, loading what fits their content: brand voice, social media, topics they never post about, promotions.

## First time: brand profile

Look for `Marketing/Brand Profile.docx` (Spanish: `Perfil de Marca.docx`) and read it with `ta read-doc`. If it doesn't exist, ask these questions (keep it short) and save the answers as that Word file, so the agent can edit it themselves:
- Agent/brand name, handles, and the main channels they use
- Language(s) and tone (warm, luxury, fun, expert...), Spanish register (*vos*, *tú* or *usted*), and words or emojis to avoid
- Niche and audience (honeymooners, families, luxury, adventure, seniors, corporate...)
- Home market and city (affects departure airports, seasons and currency)
- Call to action (WhatsApp link, DM keyword, booking link) and any legal lines they need, such as an agency license number

## Content types

| Request | Deliver |
|---|---|
| Single post | Hook (first line under 125 characters), body, CTA, 5–15 hashtags (a mix of broad, niche and local), alt text, image suggestion |
| Carousel | 6–10 slides: a hook slide, value slides with ≤25 words each, and a CTA slide, plus the caption |
| Reel/TikTok | 15–45s script: hook (0–3s), beats with on-screen text and the shot to film or stock footage to use, CTA, trending-audio *style* suggestion |
| Stories | 3–6 frames with interactive stickers (poll, quiz, question box) |
| WhatsApp broadcast | Under 600 characters, personal tone, one offer, one clear reply action |
| LinkedIn | Expert or business angle (corporate travel, the agent's journey as a business owner) |
| Content calendar | **Excel file** (`ta xlsx`) with columns Date, Channel, Format, Pillar, Topic, Hook, Caption, Status (Idea/Draft/Scheduled/Posted), mixing the pillars below |

## Content pillars (rotate them)

1. **Inspire**: destination highlights, seasonal "go now" ideas
2. **Educate**: entry-rule changes, packing, "best month for X", myths vs. reality
3. **Prove**: client trip stories and testimonials (**only with written client consent**, and without full names unless they agreed)
4. **Sell**: specific packages and offers, always with "from" prices, the dates, what's included and a validity date
5. **Personal**: the agent behind the brand, fam trips, how they work

## Sources

- A destination guide in `Destinations/`: use its facts, and don't invent new ones.
- A client trip: use the photos and reviews in its `8 - Photos & Reviews` folder, and remove personal data.
- Time-sensitive claims (visa changes, new routes, offers): check them with web search or ask the agent, and never present unverified prices as real.

## Output

- **One or two posts:** give them in chat, ready to copy and paste. That's how agents publish.
- **A batch** (a week of posts, a carousel with slide texts, reel scripts): also save a Word file in `Marketing/`, e.g. `Posts - Patagonia - 2026-10.docx`, with one heading per post so it's easy to copy from.
- **A calendar:** an Excel file in `Marketing/`, e.g. `Content Calendar - 2026-11.xlsx`, so the agent can update the Status column as they publish.

Include a variant B of the hook for testing. Write in the brand language(s), and for bilingual brands give both versions.
