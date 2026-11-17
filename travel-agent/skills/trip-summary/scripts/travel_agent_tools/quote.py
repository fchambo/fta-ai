"""Trip quotes: price the lines, estimate the agent's commission (internal only), and render the client PDF
with the day-by-day itinerary, prices and payment schedule, optionally followed by Patty's park plan."""
from datetime import date, timedelta
from xml.sax.saxutils import escape

from . import i18n, logic, schema
from .workbooks import parse_date

CATEGORIES = {  # quote category -> (Trip Sheet booking type, EN label, ES label)
    "flight": ("flight", "Flights", "Vuelos"),
    "hotel": ("hotel", "Hotel", "Hotel"),
    "tickets": ("activity", "Park tickets", "Entradas a parques"),
    "ll_express": ("activity", "Lightning Lane / Express", "Lightning Lane / Express"),
    "dining": ("activity", "Dining", "Comidas"),
    "transfer": ("transfer", "Transfers", "Traslados"),
    "car": ("car", "Car rental", "Alquiler de auto"),
    "insurance": ("insurance", "Travel insurance", "Asistencia al viajero"),
    "activity": ("activity", "Activities & events", "Actividades y eventos"),
    "package": ("tour", "Package", "Paquete"),
    "cruise": ("cruise", "Cruise", "Crucero"),
    "fee": ("other", "Service fee", "Fee de servicio"),
    "other": ("other", "Other", "Otros"),
}
ORDER = list(CATEGORIES)

L = {
    "title": ("Travel Quote", "Cotización de Viaje"),
    "for": ("Prepared for {client}", "Preparada para {client}"),
    "issued": ("Issued {date}", "Emitida el {date}"),
    "valid": ("Valid until {date}", "Válida hasta el {date}"),
    "dates": ("Travel dates: {start} to {end}", "Fechas del viaje: del {start} al {end}"),
    "party": ("Travelers", "Pasajeros"),
    "name": ("Name", "Nombre"), "age": ("Age", "Edad"),
    "itinerary": ("Day by day", "Día por día"),
    "day": ("Day", "Día"), "date": ("Date", "Fecha"), "plan": ("Plan", "Plan"),
    "prices": ("Your quote", "Tu cotización"),
    "item": ("Item", "Concepto"), "details": ("Details", "Detalle"), "amount": ("Amount", "Importe"),
    "total": ("Total", "Total"), "per_person": ("Per person ({pax} travelers)", "Por persona ({pax} pasajeros)"),
    "optional": ("Optional extras (not included in the total)", "Opcionales (no incluidos en el total)"),
    "payments": ("Payment schedule", "Forma de pago"),
    "due": ("Due", "Vence"), "what": ("What", "Concepto"),
    "on_confirm": ("On confirmation", "Al confirmar"),
    "included": ("Included", "Incluye"), "not_included": ("Not included", "No incluye"),
    "terms": ("Conditions", "Condiciones"),
    "t_avail": ("Prices are subject to availability and are only guaranteed once booked and paid.",
                "Los precios están sujetos a disponibilidad y solo quedan garantizados al reservar y abonar."),
    "t_dynamic": ("Theme-park tickets, Lightning Lane and Express use dynamic pricing: they can change daily until purchased.",
                  "Las entradas a parques, Lightning Lane y Express tienen precio dinámico: pueden cambiar día a día hasta su compra."),
    "nights": ("{n} nights", "{n} noches"), "night": ("1 night", "1 noche"),
    "pax": ("{n} pax", "{n} pax"), "qty": ("× {n}", "× {n}"),
    "park_plan_follows": ("Your park plan, with route maps for each day, follows on the next pages.",
                          "A continuación, tu plan de parques con el mapa del recorrido de cada día."),
    "dl_valid": ("Quote expires: {client}", "Vence la cotización: {client}"),
}


def tr(lang, key, **kw):
    en, es = L[key]
    return (es if lang == "es" else en).format(**kw)


def num(v):
    if v in (None, ""):
        return None
    return float(v)


def cat_label(cat, lang):
    c = CATEGORIES.get(cat) or CATEGORIES["other"]
    return c[2] if lang == "es" else c[1]


def fmt_date(value, lang):
    d = parse_date(value)
    return i18n.date_text(d, lang) if d else ""


def money(amount, currency, lang):
    return f"{currency} {i18n.money(amount, lang)}" if currency else i18n.money(amount, lang)


# --- pricing -----------------------------------------------------------------------

def compute(quote, providers=None, today=None):
    """Price every line. providers = read-providers output, for the commission estimate (internal)."""
    today = today or date.today()
    lang = quote.get("lang") if quote.get("lang") in schema.LANGS else "en"
    base_cur = quote.get("currency") or "USD"
    pax = quote.get("pax") or len(quote.get("travelers") or []) or None
    warnings, lines = [], []

    for n, raw in enumerate(quote.get("lines") or [], start=1):
        line = dict(raw)
        line.setdefault("id", f"Q{n:02d}")
        line["category"] = line.get("category") if line.get("category") in CATEGORIES else "other"
        line["currency"] = line.get("currency") or base_cur
        qty = num(line.get("qty")) or 1
        gross = num(line.get("gross"))
        if gross is None and num(line.get("unit_price")) is not None:
            gross = round(num(line["unit_price"]) * qty, 2)
        line["gross"] = gross
        if gross is None:
            warnings.append(f"{line['id']} {line.get('description')}: no price")
        if line.get("verify"):
            warnings.append(f"{line['id']} {line.get('description')}: price to verify before sending"
                            + (f" (source: {line['source']})" if line.get("source") else ""))
        if line["currency"] != base_cur:
            warnings.append(f"{line['id']}: in {line['currency']}, quote currency is {base_cur}")
        net = num(line.get("net"))
        line["margin"] = round(gross - net, 2) if gross is not None and net is not None else None
        lines.append(line)

    totals, optional = {}, {}
    for line in lines:
        bucket = optional if line.get("optional") else totals
        if line["gross"] is not None:
            bucket[line["currency"]] = round(bucket.get(line["currency"], 0) + line["gross"], 2)
    per_person = {c: round(v / pax, 2) for c, v in totals.items()} if pax else {}

    # Payment schedule: pct of the (single-currency) total, or a fixed amount.
    schedule = []
    for p in quote.get("payments") or []:
        amount, cur = num(p.get("amount")), p.get("currency") or base_cur
        if amount is None and num(p.get("pct")) is not None:
            if len(totals) > 1:
                warnings.append(f"Payment '{p.get('description')}': % of a multi-currency total, give an amount per currency")
            amount = round(totals.get(cur, 0) * num(p["pct"]) / 100, 2)
        schedule.append({**p, "amount": amount, "currency": cur})
    if schedule and len(totals) == 1:
        cur, total = next(iter(totals.items()))
        scheduled = sum(p["amount"] or 0 for p in schedule if p["currency"] == cur)
        if abs(scheduled - total) > 0.01:
            warnings.append(f"Payment schedule adds up to {money(scheduled, cur, 'en')}, total is {money(total, cur, 'en')}")

    valid = parse_date(quote.get("valid_until"))
    if not valid:
        warnings.append("No valid_until date: theme-park and hotel prices change, give the quote an expiry")
    elif valid < today:
        warnings.append(f"valid_until {valid.isoformat()} is in the past")
    for d in (quote.get("start_date"), quote.get("end_date")):
        if d and parse_date(d) and parse_date(d) < today:
            warnings.append(f"Travel date {d} is in the past")

    # Internal: commission and margin per line, with the agent's own rules.
    commission = None
    if providers:
        trip = {"trip": {"client_name": quote.get("client"), "status": "quoting", "trip_id": "quote"},
                "bookings": [booking_row(l) for l in lines if not l.get("optional") and l["gross"] is not None and l.get("provider")],
                "payments": []}
        result = logic.commissions({**providers, "_lang": lang}, [trip], today)
        by_line = {r["booking"]: r for r in result["bookings"]}
        for line in lines:
            r = by_line.get(line["id"])
            line["commission"] = r["commission"] if r else None
        commission = {}
        for r in result["bookings"]:
            commission[r["currency"]] = round(commission.get(r["currency"], 0) + r["commission"], 2)
        warnings += [w for w in result["warnings"] if not w.startswith(("VAT", "IVA"))]
        unpriced = [l["id"] for l in lines if not l.get("optional") and not l.get("provider") and l.get("margin") is None]
        if unpriced:
            warnings.append(f"No provider on {', '.join(unpriced)}: commission unknown for those lines")

    deadlines = []
    if valid:
        deadlines.append({"date": valid.isoformat(), "what": tr(lang, "dl_valid", client=quote.get("client") or ""), "done": "no"})
    return {
        "lang": lang, "currency": base_cur, "pax": pax, "lines": lines,
        "totals": totals, "per_person": per_person, "optional_totals": optional,
        "payments": schedule, "commission_estimate": commission,
        "margin_from_net": {c: round(sum(l["margin"] for l in lines if l["margin"] is not None and not l.get("optional")
                                         and l["currency"] == c), 2) for c in totals} if any(l["margin"] is not None for l in lines) else None,
        "trip_bookings": [booking_row(l) for l in lines if not l.get("optional")],
        "trip_optional_bookings": [booking_row(l) for l in lines if l.get("optional")],
        "trip_deadlines": deadlines,
        "warnings": warnings,
    }


def booking_row(line):
    row = {
        "id": line["id"], "type": CATEGORIES[line["category"]][0], "provider": line.get("provider"),
        "product": line.get("product"), "start": line.get("start"), "end": line.get("end"),
        "details": line.get("description"), "pax": line.get("pax"), "nights": line.get("nights"),
        "gross_amount": line.get("gross"), "taxes_amount": line.get("taxes"), "net_amount": line.get("net"),
        "currency": line.get("currency"), "cancellation_deadline": line.get("cancellation_deadline"),
    }
    return {k: v for k, v in row.items() if v not in (None, "")}


def itinerary_from_plan(plan, lang):
    """One line per park day from a Patty plan, for quotes that don't list their own itinerary."""
    out = []
    for d in plan.get("days") or []:
        must = [s.get("short") or s["name"] for s in d.get("steps", []) if s.get("level") == "must"]
        details = f'{d.get("open")}–{d.get("close")}' + (f' · {", ".join(must[:4])}' if must else "")
        out.append({"date": d.get("date"), "title": d.get("park_name"), "details": details})
    return out


def line_details(line, lang):
    parts = []
    s, e = fmt_date(line.get("start"), lang), fmt_date(line.get("end"), lang)
    if s:
        parts.append(f"{s} – {e}" if e and e != s else s)
    nights = num(line.get("nights"))
    if nights:
        parts.append(tr(lang, "night") if nights == 1 else tr(lang, "nights", n=int(nights)))
    if line.get("pax"):
        parts.append(tr(lang, "pax", n=int(num(line["pax"]))))
    if num(line.get("qty")) and num(line["qty"]) != 1 and line.get("unit_price") is not None:
        parts.append(f'{money(num(line["unit_price"]), line["currency"], lang)} {tr(lang, "qty", n=int(num(line["qty"])))}')
    if line.get("notes"):
        parts.append(str(line["notes"]))
    return " · ".join(parts)


# --- PDF ---------------------------------------------------------------------------

def render(quote, out_path, plan=None, footer=None, palette=None, color=None, lang=None, providers=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from . import parks_pdf
    from .docs import _pdf_font

    if lang:
        quote = {**quote, "lang": lang}
    priced = compute(quote, providers=None)  # never put commission into a client document
    lang = priced["lang"]
    font = _pdf_font()
    brand = parks_pdf.parse_palette(palette) if isinstance(palette, str) else list(palette or [])
    if not brand and color:
        brand = parks_pdf.parse_palette(color)
    main = brand[0] if brand else parks_pdf.DEFAULTS[0]
    second = brand[1] if len(brand) > 1 else main
    accent = colors.HexColor(parks_pdf.on_white(main))
    band = colors.HexColor(main)
    tint = colors.HexColor(parks_pdf._mix(second, 0.88))

    base = getSampleStyleSheet()
    body = ParagraphStyle("qb", parent=base["BodyText"], fontName=font, fontSize=9.5, leading=12.5)
    small = ParagraphStyle("qs", parent=body, fontSize=8.4, leading=10.6)
    right = ParagraphStyle("qr", parent=small, alignment=2)
    th = ParagraphStyle("qth", parent=small, textColor=colors.HexColor(parks_pdf.text_on(main)))
    thr = ParagraphStyle("qthr", parent=th, alignment=2)
    h0 = ParagraphStyle("qh0", parent=body, fontSize=22, leading=26, textColor=accent, spaceAfter=2)
    h1 = ParagraphStyle("qh1", parent=body, fontSize=13, leading=17, textColor=accent, spaceAfter=6)
    h2 = ParagraphStyle("qh2", parent=body, fontSize=11.5, leading=15, textColor=accent, spaceBefore=10, spaceAfter=4)
    muted = ParagraphStyle("qm", parent=body, textColor=colors.HexColor("#4B5563"))
    bold = ParagraphStyle("qbold", parent=small, fontName=font, fontSize=9.5)
    usable = A4[0] - 3.6 * cm

    def para(text, style=body):
        return Paragraph(escape(str(text if text is not None else "")), style)

    def table(header, rows, widths, align_last=False, strong_rows=()):
        hdr = [para(h, thr if align_last and i == len(header) - 1 else th) for i, h in enumerate(header)]
        data = [hdr] + [[c if not isinstance(c, (str, int, float)) else
                         para(c, right if align_last and i == len(r) - 1 else small) for i, c in enumerate(r)] for r in rows]
        t = Table(data, colWidths=[usable * w for w in widths], repeatRows=1, hAlign="LEFT")
        style = [("BACKGROUND", (0, 0), (-1, 0), band), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                 ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
        for i in strong_rows:
            style.append(("BACKGROUND", (0, i + 1), (-1, i + 1), tint))
        t.setStyle(TableStyle(style))
        return t

    story = [para(tr(lang, "title"), h0)]
    if quote.get("title"):
        story.append(para(quote["title"], h1))
    meta = []
    if quote.get("client"):
        meta.append(tr(lang, "for", client=quote["client"]))
    meta.append(tr(lang, "issued", date=fmt_date(quote.get("date") or date.today().isoformat(), lang)))
    if quote.get("valid_until"):
        meta.append(tr(lang, "valid", date=fmt_date(quote["valid_until"], lang)))
    story.append(para(" · ".join(meta), muted))
    if quote.get("start_date") and quote.get("end_date"):
        story.append(para(tr(lang, "dates", start=fmt_date(quote["start_date"], lang), end=fmt_date(quote["end_date"], lang)), muted))
    story.append(Spacer(1, 6))

    travelers = quote.get("travelers") or []
    if travelers:
        story.append(para(tr(lang, "party"), h2))
        story.append(table([tr(lang, "name"), tr(lang, "age")],
                           [[t.get("name", ""), t.get("age", "—") if t.get("age") not in (None, "") else "—"] for t in travelers],
                           [0.7, 0.3]))

    itinerary = quote.get("itinerary") or (itinerary_from_plan(plan, lang) if plan else [])
    if itinerary:
        story.append(para(tr(lang, "itinerary"), h2))
        rows = []
        for i, d in enumerate(itinerary, start=1):
            dd = parse_date(d.get("date")) if d.get("date") else None
            when = parks_pdf.day_text(dd.isoformat(), lang) if dd else ""
            rows.append([str(d.get("day") or i), when,
                         Paragraph(f"<b>{escape(str(d.get('title') or ''))}</b>"
                                   + (f"<br/>{escape(str(d['details']))}" if d.get("details") else ""), small)])
        story.append(table([tr(lang, "day"), tr(lang, "date"), tr(lang, "plan")], rows, [0.08, 0.17, 0.75]))

    def price_rows(lines):
        rows = []
        for cat in ORDER:
            for line in [l for l in lines if l["category"] == cat]:
                amount = money(line["gross"], line["currency"], lang) if line["gross"] is not None else "—"
                rows.append([Paragraph(f"<b>{escape(cat_label(cat, lang))}</b><br/>{escape(str(line.get('description') or ''))}", small),
                             line_details(line, lang), amount])
        return rows

    included = [l for l in priced["lines"] if not l.get("optional")]
    rows = price_rows(included)
    strong = []
    for cur, total in priced["totals"].items():
        strong.append(len(rows))
        rows.append([Paragraph(f"<b>{escape(tr(lang, 'total'))}</b>", bold), "",
                     Paragraph(f"<b>{escape(money(total, cur, lang))}</b>", ParagraphStyle('qtr', parent=bold, alignment=2))])
    for cur, pp in priced["per_person"].items():
        rows.append([tr(lang, "per_person", pax=priced["pax"]), "", money(pp, cur, lang)])
    story.append(para(tr(lang, "prices"), h2))
    story.append(table([tr(lang, "item"), tr(lang, "details"), tr(lang, "amount")], rows, [0.42, 0.38, 0.2],
                       align_last=True, strong_rows=strong))

    optional = [l for l in priced["lines"] if l.get("optional")]
    if optional:
        story.append(KeepTogether([para(tr(lang, "optional"), h2),
                                   table([tr(lang, "item"), tr(lang, "details"), tr(lang, "amount")], price_rows(optional),
                                         [0.42, 0.38, 0.2], align_last=True)]))

    if priced["payments"]:
        rows = [[fmt_date(p.get("due_date"), lang) or tr(lang, "on_confirm"), p.get("description") or "",
                 money(p["amount"], p["currency"], lang) if p.get("amount") is not None else "—"] for p in priced["payments"]]
        story.append(KeepTogether([para(tr(lang, "payments"), h2),
                                   table([tr(lang, "due"), tr(lang, "what"), tr(lang, "amount")], rows, [0.2, 0.6, 0.2], align_last=True)]))

    for key in ("included", "not_included"):
        if quote.get(key):
            block = [para(tr(lang, key), h2)] + [Paragraph("• " + escape(str(x)), small) for x in quote[key]]
            story.append(KeepTogether(block))

    terms = list(quote.get("terms") or []) + [tr(lang, "t_avail")]
    if any(l["category"] in ("tickets", "ll_express") for l in priced["lines"]):
        terms.append(tr(lang, "t_dynamic"))
    story.append(KeepTogether([para(tr(lang, "terms"), h2)] + [Paragraph("• " + escape(str(x)), small) for x in terms]))
    for n in quote.get("notes") or []:
        story.append(Spacer(1, 3))
        story.append(para(n, muted))

    if plan:
        story.append(Spacer(1, 8))
        story.append(para(tr(lang, "park_plan_follows"), muted))
        story.append(PageBreak())
        plan_story, _, _ = parks_pdf.build_story({**plan, "lang": lang}, palette=brand or None)
        story += plan_story

    def decorate(canvas, doc):
        canvas.setFont(font, 7.5)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        if footer:
            canvas.drawString(1.8 * cm, 1.1 * cm, footer)
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, str(doc.page))

    SimpleDocTemplate(out_path, pagesize=A4, title=tr(lang, "title"), leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                      topMargin=1.6 * cm, bottomMargin=1.8 * cm).build(story, onFirstPage=decorate, onLaterPages=decorate)
    return out_path
