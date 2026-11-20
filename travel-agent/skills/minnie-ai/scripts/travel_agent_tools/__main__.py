"""travel-agent tools CLI. Run through bin/ta. Output is JSON for Claude, files are for the agent."""
import argparse
import glob
import json
import os
import re
import sys
from datetime import date

from . import docs, i18n, logic, schema, workbooks
from .workbooks import FileOpenError

CONFIG = ".travel-agent.json"

HOW_TO = {
    "en": [
        ("How commissions are calculated", ""),
        ("Percentage", "Rate % × client price. 'Gross without taxes' subtracts the booking's taxes first."),
        ("Net rate + my markup", "Client price − net. 'Suggested markup %' warns you when you price below it."),
        ("Fixed amount", "Amount × 1 booking, × passengers or × nights."),
        ("Products sheet", "Overrides the provider's rule for a specific product. The product must match the Bookings 'Product' column."),
        ("Incentives sheet", "Extra % on the whole period's sales once the volume tier is reached."),
        ("How I get paid", "'I collect gross and pay net': you keep the commission when paying the provider. "
                           "'I invoice the provider': you bill them (VAT added). 'Provider pays me': they transfer it."),
        ("Provider ID", "Short code (e.g. andes-dmc). Use the same code in each trip's Bookings sheet."),
    ],
    "es": [
        ("Cómo se calculan las comisiones", ""),
        ("Porcentaje", "Tasa % × precio al cliente. 'Bruto sin impuestos' resta primero los impuestos de la reserva."),
        ("Tarifa neta + mi markup", "Precio al cliente − neto. 'Markup sugerido %' te avisa si cotizás por debajo."),
        ("Monto fijo", "Monto × 1 reserva, × pasajeros o × noches."),
        ("Hoja Productos", "Reemplaza la regla del proveedor para un producto puntual. El producto debe coincidir con la columna 'Producto' de Reservas."),
        ("Hoja Incentivos", "% extra sobre las ventas del período al alcanzar el volumen indicado."),
        ("Cómo cobro", "'Cobro bruto y pago neto': te quedás la comisión al pagarle al proveedor. "
                       "'Le facturo al proveedor': le emitís factura (con IVA). 'El proveedor me paga': te transfiere."),
        ("ID proveedor", "Código corto (ej. andes-dmc). Usá el mismo código en la hoja Reservas de cada viaje."),
    ],
}


def out(data):
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def safe_name(text):
    return re.sub(r'[\\/:*?"<>|]+', "-", str(text)).strip().strip(".")


def find_config(path):
    path = os.path.abspath(path)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    while True:
        candidate = os.path.join(path, CONFIG)
        if os.path.exists(candidate):
            with open(candidate, encoding="utf-8") as f:
                return path, json.load(f)
        parent = os.path.dirname(path)
        if parent == path:
            return None, {}
        path = parent


def lang_of(lang):
    return lang if lang in schema.LANGS else "en"


def folder(key, lang):
    return schema.ROOT_FOLDERS[key][schema.LANGS.index(lang)]


def load_json_arg(value):
    if os.path.exists(value):
        with open(value, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(value)


def today_arg(args):
    return date.fromisoformat(args.today) if args.today else date.today()


# --- commands ------------------------------------------------------------------------

def cmd_init(args):
    base, lang = os.path.abspath(args.base), lang_of(args.lang)
    os.makedirs(base, exist_ok=True)
    existing_base, cfg = find_config(base)
    if existing_base == base:
        lang = cfg.get("lang", lang)
    for key in schema.ROOT_FOLDERS:
        os.makedirs(os.path.join(base, folder(key, lang)), exist_ok=True)
    cfg = {**cfg, "lang": lang, "agency_name": args.agency or cfg.get("agency_name", "")}
    with open(os.path.join(base, CONFIG), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    providers = os.path.join(base, folder("commissions", lang), schema.FILE_NAMES["providers"][schema.LANGS.index(lang)])
    created = False
    if not os.path.exists(providers):
        workbooks.create(providers, schema.PROVIDERS_WORKBOOK, {"settings": {
            "agency_name": cfg["agency_name"], "language": lang, "home_currency": args.currency}}, lang)
        from openpyxl import load_workbook
        wb = load_workbook(providers)
        ws = wb.create_sheet("How it works" if lang == "en" else "Cómo funciona")
        ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 30, 110
        for r, (k, v) in enumerate(HOW_TO[lang], start=1):
            ws.cell(row=r, column=1, value=k).font = workbooks.LABEL_FONT
            ws.cell(row=r, column=2, value=v)
        wb.save(providers)
        created = True
    tasks = os.path.join(base, schema.FILE_NAMES["tasks"][schema.LANGS.index(lang)])
    tasks_created = not os.path.exists(tasks)
    if tasks_created:
        workbooks.create(tasks, schema.TASKS_WORKBOOK, {}, lang)
    out({"base": base, "lang": lang, "providers_workbook": providers, "providers_created": created,
         "tasks_workbook": tasks, "tasks_created": tasks_created,
         "folders": [folder(k, lang) for k in schema.ROOT_FOLDERS]})


def cmd_new_trip(args):
    if not re.fullmatch(r"\d{4}-\d{2}", args.month):
        sys.exit(f"Month must be YYYY-MM, got: {args.month}")
    base, cfg = find_config(args.base)
    if base is None:
        sys.exit("No travel-agent workspace here. Run 'init' first.")
    lang = lang_of(cfg.get("lang"))
    idx = schema.LANGS.index(lang)
    trip_dir = os.path.join(base, folder("clients", lang), safe_name(args.client),
                            safe_name(f"{args.month} {args.destination}"))
    if os.path.exists(trip_dir):
        print(json.dumps({"error": "exists", "trip_dir": trip_dir}, ensure_ascii=False))
        sys.exit(2)
    for names in schema.TRIP_FOLDERS:
        os.makedirs(os.path.join(trip_dir, names[idx]))
    slug = re.sub(r"[^a-z0-9]+", "-", __import__("unicodedata").normalize("NFKD", f"{args.client} {args.destination}")
                  .encode("ascii", "ignore").decode().lower()).strip("-")
    sheet = os.path.join(trip_dir, f"{schema.FILE_NAMES['trip_sheet'][idx]} - {safe_name(args.client)} - {safe_name(args.destination)}.xlsx")
    workbooks.create(sheet, schema.TRIP_WORKBOOK, {"trip": {
        "trip_id": f"{args.month}-{slug}", "status": "inquiry", "created": date.today(),
        "client_name": args.client, "destinations": args.destination}}, lang)
    out({"trip_dir": trip_dir, "trip_sheet": sheet, "lang": lang,
         "subfolders": [n[idx] for n in schema.TRIP_FOLDERS]})


def _trip_sheets(base):
    base_dir, cfg = find_config(base)
    root = base_dir or os.path.abspath(base)
    found = []
    for path in sorted(glob.glob(os.path.join(root, "*", "*", "*", "*.xlsx"))):
        if not os.path.basename(path).startswith("~$") and workbooks.is_layout(path, schema.TRIP_WORKBOOK):
            found.append(path)
    return found


def cmd_find_trips(args):
    trips = []
    for path in _trip_sheets(args.base):
        info = workbooks.read(path, schema.TRIP_WORKBOOK)["trip"]
        if args.active and info.get("status") in ("closed", "cancelled"):
            continue
        trips.append({"path": path, "client": info.get("client_name"), "destinations": info.get("destinations"),
                      "start_date": info.get("start_date"), "status": info.get("status")})
    out(trips)


def cmd_read(layout):
    def run(args):
        out(workbooks.read(args.file, layout))
    return run


def cmd_update(layout):
    def run(args):
        changes = load_json_arg(args.changes)
        out(workbooks.update(args.file, layout, changes, replace=tuple(args.replace or ())))
    return run


def cmd_timeline(args):
    results = []
    files = args.files or _trip_sheets(args.base or ".")
    for path in files:
        trip = workbooks.read(path, schema.TRIP_WORKBOOK)
        if args.active and (trip["trip"].get("status") in ("closed", "cancelled")):
            continue
        result = logic.timeline(trip, today_arg(args))
        result["path"] = path
        results.append(result)
    out(results[0] if len(results) == 1 and args.files else results)


def cmd_commissions(args):
    cfg = workbooks.read(args.providers, schema.PROVIDERS_WORKBOOK)
    files = args.trips or _trip_sheets(os.path.dirname(args.providers))
    result = logic.commissions(cfg, [workbooks.read(p, schema.TRIP_WORKBOOK) for p in files], today_arg(args))
    result["trip_sheets"] = files
    if args.report:
        lang = cfg.get("_lang", "en")

        def sheet(name_key, keys, rows):
            return {"name": i18n.r(lang, name_key), "columns": [i18n.r(lang, k) for k in keys],
                    "rows": [[row.get(k) for k in keys] for row in rows]}

        bookings = [{**b, "rule": b["rule_label"], "status": i18n.r(lang, b["status"])} for b in result["bookings"]]
        incentives = [{**i, "next_tier": i18n.r(lang, "next_tier_text", missing=i18n.money(i["next_tier"]["missing"], lang),
                                                extra=i["next_tier"]["extra_pct"], start=i18n.money(float(i["next_tier"]["from"]), lang))
                       if i["next_tier"] else ""} for i in result["incentives"]]
        currency_rows = [{"currency": k, **{s: v[s] for s in ("received", "retained", "pending", "overdue")}}
                         for k, v in result["by_currency"].items()]
        workbooks.write_tables(args.report, [
            sheet("sheet_commissions", ["client", "booking", "provider", "product", "rule", "gross", "commission",
                                        "withholding", "vat_to_invoice", "currency", "expected_date", "status"], bookings),
            sheet("sheet_by_provider", ["provider", "bookings", "gross", "commission", "currency"],
                  [{"provider": k, **v} for k, v in result["by_provider"].items()]),
            sheet("sheet_by_currency", ["currency", "received", "retained", "pending", "overdue"], currency_rows),
            sheet("sheet_incentives", ["provider", "year", "volume", "current_extra_pct", "bonus_estimate", "next_tier"], incentives),
            sheet("sheet_warnings", ["warning"], [{"warning": w} for w in result["warnings"]]),
        ])
        result["report"] = args.report
    out(result)


def cmd_docx(args):
    with open(args.markdown, encoding="utf-8") as f:
        text = f.read()
    workbooks.ensure_closed(args.output)
    docs.markdown_to_docx(text, args.output, title=args.title, footer=args.footer, color=args.color)
    result = {"docx": args.output}
    if args.pdf:
        pdf = os.path.splitext(args.output)[0] + ".pdf"
        workbooks.ensure_closed(pdf)
        docs.markdown_to_pdf(text, pdf, title=args.title, footer=args.footer, color=args.color)
        result["pdf"] = pdf
    out(result)


def cmd_xlsx(args):
    workbooks.ensure_closed(args.output)
    workbooks.write_tables(args.output, load_json_arg(args.tables))
    out({"xlsx": args.output})


def cmd_pdf(args):
    out({"pdf": docs.to_pdf(args.file)})


def cmd_read_doc(args):
    print(docs.read_text(args.file))


def cmd_parks(args):
    from . import parks
    out([{"id": p["id"], "name": p["name"], "resort": p["resort"], "attractions": len(p["attractions"]),
          "data_checked": p.get("data_checked")} for p in parks.load_parks().values()])


def cmd_park_info(args):
    from . import parks
    park = parks.find_park(parks.load_parks(), args.park)
    people = parks.prepare_party(load_json_arg(args.party)) if args.party else None
    out(parks.park_info(park, people))


def cmd_park_plan(args):
    from . import parks
    result = parks.plan(load_json_arg(args.request))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    out(result)


def cmd_park_pdf(args):
    from . import parks_pdf
    plan = load_json_arg(args.plan)
    if args.lang:
        plan["lang"] = args.lang
    workbooks.ensure_closed(args.output)
    out({"pdf": parks_pdf.render(plan, args.output, footer=args.footer, color=args.color, palette=args.palette)})


def cmd_client(args):
    from . import clients
    base_dir, cfg = find_config(args.base)
    root = base_dir or os.path.abspath(args.base)
    lang = lang_of(cfg.get("lang"))
    matches = clients.find(root, args.name, _trip_sheets(root))
    best = [m for m in matches if m["score"] == matches[0]["score"]] if matches else []
    if len(best) == 1 and best[0]["score"] >= 2:
        out({"status": "found", **clients.load(best[0], lang)})
    elif args.create and not (best and best[0]["score"] >= 2):
        if base_dir is None:
            sys.exit("No travel-agent workspace here. Run 'init' first.")
        out({"status": "created", **clients.create(os.path.join(root, folder("clients", lang)), args.name, lang, safe_name)})
    else:
        out({"status": "ambiguous" if best else "not_found",
             "candidates": [{"client": m["client"], "client_dir": m["client_dir"], "names": m["names"],
                             "trips": len(m["trip_paths"]), "score": m["score"]} for m in matches[:8]],
             "hint": "Confirm with the agent, then re-run with the exact folder name"
                     + ("" if best and best[0]["score"] >= 2 else ", or with --create for a new client")})


def _providers_for_quote(path):
    if not path:
        return None
    return workbooks.read(path, schema.PROVIDERS_WORKBOOK)


def cmd_quote(args):
    from . import quote
    result = quote.compute(load_json_arg(args.quote), providers=_providers_for_quote(args.providers), today=today_arg(args))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    out(result)


def cmd_quote_pdf(args):
    from . import quote
    plan = load_json_arg(args.plan) if args.plan else None
    workbooks.ensure_closed(args.output)
    out({"pdf": quote.render(load_json_arg(args.quote), args.output, plan=plan, footer=args.footer,
                             palette=args.palette, color=args.color, lang=args.lang)})


def cmd_vouchers(args):
    from . import vouchers
    if os.path.isfile(args.path):
        sheets = [args.path]
    elif any(workbooks.is_layout(p, schema.TRIP_WORKBOOK) for p in glob.glob(os.path.join(args.path, "*.xlsx"))):
        sheets = [p for p in glob.glob(os.path.join(args.path, "*.xlsx")) if workbooks.is_layout(p, schema.TRIP_WORKBOOK)]
    else:
        sheets = _trip_sheets(args.path)
        if args.client:
            from . import clients
            matches = clients.find(find_config(args.path)[0] or os.path.abspath(args.path), args.client, sheets)
            best = [m for m in matches if m["score"] == matches[0]["score"]] if matches else []
            if not best or best[0]["score"] < 2:
                out({"status": "client_not_found", "candidates": [m["client"] for m in matches[:8]]})
                return
            if len(best) > 1:
                out({"status": "ambiguous", "candidates": [m["client"] for m in best]})
                return
            sheets = best[0]["trip_paths"]
    trips = []
    for path in sheets:
        result = vouchers.trip(path, args.query)
        if args.active and result["status"] in ("closed", "cancelled"):
            continue
        if args.query and not (result["files"] or result["bookings"]):
            continue
        trips.append(result)
    trips.sort(key=lambda t: str(t.get("start_date") or ""), reverse=True)
    out({"status": "ok" if trips else "nothing_found", "query": args.query, "trips": trips,
         "files_found": sum(len(t["files"]) for t in trips)})


def cmd_open(args):
    from . import vouchers
    out({"opened": [vouchers.open_file(p) for p in args.files]})


def _kb_sources(paths):
    """(Knowledge Base folder or None, paths to read). An agency folder means its Knowledge Base folder."""
    from . import kb
    sources, kb_dir = [], None
    for path in paths:
        base, _ = find_config(path)
        if os.path.isdir(path) and base and os.path.abspath(path) == base:
            found = kb.folder_for(base)
            if found:
                kb_dir = kb_dir or found
                sources.append(found)
        else:
            if os.path.isdir(path):
                kb_dir = kb_dir or os.path.abspath(path)
            sources.append(path)
    return kb_dir, sources


def cmd_kb(args):
    from . import kb
    kb_dir, sources = _kb_sources(args.paths or ["."])
    if not sources:
        out({"folder": None, "missing": True, "files": [], "tags": [],
             "hint": "No Knowledge Base folder yet. 'ta init' creates it; in chat mode ask the agent to attach their Knowledge Base files."})
        return
    entries = kb.index(sources, root=kb_dir)
    total = sum(e["chars"] for e in entries)
    if args.tag or args.query or args.all:
        picked = entries if args.all else kb.select(entries, args.tag or [], args.query)
        out({"folder": kb_dir, "matched": [kb.public(e, True) for e in picked],
             "other_tags": [t["tag"] for t in kb.summary(entries)
                            if kb.tag_key(t["tag"]) not in {kb.tag_key(x) for e in picked for x in e["tags"]}]})
        return
    result = {"folder": kb_dir, "files": [kb.public(e, False) for e in entries], "tags": kb.summary(entries),
              "untagged": [e["file"] for e in entries if not e["tags"]], "total_chars": total}
    if not entries:
        result["hint"] = "The Knowledge Base is empty."
    elif total <= kb.SMALL_KB_CHARS:
        result["hint"] = "Small Knowledge Base: read all of it with --all."
    out(result)


def _camel_words(tag):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", tag.lstrip("#")).replace("-", " ").replace("_", " ").strip()


def cmd_kb_note(args):
    from . import kb
    if (args.replace is None) != (args.with_text is None):
        sys.exit("--replace needs --with (the new text), and the other way round")
    actions = sum(x is not None for x in (args.add, args.replace, args.remove))
    if actions > 1 or (actions == 0 and not (args.tags and args.doc)):
        sys.exit("Pass one of --add, --replace … --with, or --remove (or --doc with --tags to just tag a file)")
    target = None
    if os.path.isfile(args.path):
        target, kb_dir = args.path, os.path.dirname(os.path.abspath(args.path))
    else:
        base, cfg = find_config(args.path)
        if base and os.path.abspath(args.path) == base:
            kb_dir = kb.folder_for(base) or os.path.join(base, folder("knowledge", lang_of(cfg.get("lang"))))
        else:
            kb_dir = os.path.abspath(args.path)
        existing = kb.index([kb_dir], root=kb_dir) if os.path.isdir(kb_dir) else []
        if args.doc:
            wanted = kb._plain(os.path.splitext(args.doc)[0])
            same = [e for e in existing if kb._plain(os.path.splitext(os.path.basename(e["file"]))[0]) == wanted]
            target = same[0]["path"] if same else os.path.join(kb_dir, safe_name(os.path.splitext(args.doc)[0]) + ".docx")
        elif args.tags:
            having = [e for e in existing if kb.tag_key(args.tags[0]) in e["_keys"]]  # the first tag picks the file
            if len(having) > 1:
                out({"status": "ambiguous", "candidates": [e["file"] for e in having],
                     "hint": "Several files have this tag: ask the agent which one, then pass --doc"})
                return
            target = having[0]["path"] if having else os.path.join(kb_dir, safe_name(_camel_words(args.tags[0])) + ".docx")
        else:
            sys.exit("Say which file with --doc, or give --tags so the file with that tag is used")
    if not target.lower().endswith(kb.WRITABLE):
        sys.exit(f"Only Word files can be edited ({os.path.basename(target)}): ask the agent to change it, or add the rule to a Word file")
    try:
        result = kb.write(target, title=args.doc and os.path.splitext(args.doc)[0], add=args.add if args.replace is None else args.with_text,
                          tags=args.tags or [], replace=args.replace, remove=args.remove)
    except (ValueError, PermissionError) as e:
        sys.exit(str(e))
    entry = kb.read(target, kb_dir)
    out({"status": "ok", "file": target, **result, "tags": entry["tags"]})


def cmd_dashboard(args):
    from . import dashboard
    paths = args.paths or ["."]
    data = dashboard.collect(paths, today=today_arg(args), lang=args.lang)
    base_dir = next((b for b in (find_config(p)[0] for p in paths) if b), None)
    output = args.out
    if not output:
        root = base_dir or (paths[0] if os.path.isdir(paths[0]) else os.path.dirname(os.path.abspath(paths[0])))
        output = os.path.join(root, schema.FILE_NAMES["dashboard"][schema.LANGS.index(data["lang"])])
    dashboard.render(data, output)
    tasks = data["sources"]["tasks"]
    hint = None
    if not tasks:
        hint = ("No My Tasks workbook found: run 'ta init <base>' to create it" if base_dir
                else "No My Tasks workbook among the files: the agent's own tasks are missing")
    out({"html": os.path.abspath(output), "lang": data["lang"], "today": data["today"],
         **dashboard.summary(data), "trip_sheets": len(data["sources"]["trips"]),
         "tasks_workbook": tasks[0] if tasks else None, "providers_workbook": (data["sources"]["providers"] or [None])[0],
         "warnings": data["warnings"] + ([hint] if hint else [])})


def main():
    p = argparse.ArgumentParser(prog="ta")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="Create the agency workspace")
    s.add_argument("base"); s.add_argument("--lang", default="en", choices=schema.LANGS)
    s.add_argument("--agency", default=""); s.add_argument("--currency", default="USD")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("new-trip", help="Create a client trip folder + Trip Sheet")
    s.add_argument("base"); s.add_argument("client"); s.add_argument("destination"); s.add_argument("month")
    s.set_defaults(fn=cmd_new_trip)

    s = sub.add_parser("find-trips"); s.add_argument("base"); s.add_argument("--active", action="store_true")
    s.set_defaults(fn=cmd_find_trips)

    for name, layout in (("trip", schema.TRIP_WORKBOOK), ("providers", schema.PROVIDERS_WORKBOOK),
                         ("tasks", schema.TASKS_WORKBOOK)):
        s = sub.add_parser(f"read-{name}"); s.add_argument("file"); s.set_defaults(fn=cmd_read(layout))
        s = sub.add_parser(f"update-{name}", help="Merge JSON changes ({section: {...} or [...]}) into the workbook")
        s.add_argument("file"); s.add_argument("changes", help="JSON string or path to a .json file")
        s.add_argument("--replace", nargs="*", help="Sections to overwrite instead of merge")
        s.set_defaults(fn=cmd_update(layout))

    s = sub.add_parser("timeline"); s.add_argument("files", nargs="*"); s.add_argument("--base")
    s.add_argument("--active", action="store_true"); s.add_argument("--today")
    s.set_defaults(fn=cmd_timeline)

    s = sub.add_parser("commissions"); s.add_argument("providers"); s.add_argument("trips", nargs="*")
    s.add_argument("--report", help="Write an .xlsx report here"); s.add_argument("--today")
    s.set_defaults(fn=cmd_commissions)

    s = sub.add_parser("docx", help="Markdown file -> styled Word document")
    s.add_argument("markdown"); s.add_argument("output"); s.add_argument("--title"); s.add_argument("--footer")
    s.add_argument("--color", default="0F766E"); s.add_argument("--pdf", action="store_true")
    s.set_defaults(fn=cmd_docx)

    s = sub.add_parser("xlsx", help="JSON tables -> styled Excel file")
    s.add_argument("tables"); s.add_argument("output"); s.set_defaults(fn=cmd_xlsx)

    s = sub.add_parser("pdf"); s.add_argument("file"); s.set_defaults(fn=cmd_pdf)
    s = sub.add_parser("read-doc"); s.add_argument("file"); s.set_defaults(fn=cmd_read_doc)

    s = sub.add_parser("parks", help="List the theme parks with planning data"); s.set_defaults(fn=cmd_parks)
    s = sub.add_parser("park-info", help="Attractions of one park; with --party, who can ride each one")
    s.add_argument("park"); s.add_argument("--party", help="JSON list of travelers, or a path to one")
    s.set_defaults(fn=cmd_park_info)
    s = sub.add_parser("park-plan", help="Plan park days from a request JSON (see the park-itinerary skill)")
    s.add_argument("request", help="JSON string or path to a .json file"); s.add_argument("--out", help="Also save the plan here")
    s.set_defaults(fn=cmd_park_plan)
    s = sub.add_parser("park-pdf", help="Plan JSON -> client PDF with maps and schedules")
    s.add_argument("plan"); s.add_argument("output"); s.add_argument("--footer"); s.add_argument("--lang", choices=schema.LANGS)
    s.add_argument("--palette", help="Agency brand colors, main first: '#0F766E,#EA580C,#4150F7'")
    s.add_argument("--color", help="Main color only (use --palette for the full brand palette)")
    s.set_defaults(fn=cmd_park_pdf)
    s = sub.add_parser("client", help="Find a client (accent/case-insensitive): profile + past trips. --create for a new one")
    s.add_argument("base"); s.add_argument("name"); s.add_argument("--create", action="store_true")
    s.set_defaults(fn=cmd_client)
    s = sub.add_parser("quote", help="Price a quote JSON: totals, per person, payments, commission estimate (internal)")
    s.add_argument("quote", help="JSON string or path to a .json file")
    s.add_argument("--providers", help="Providers & Commissions workbook, for the commission estimate")
    s.add_argument("--out", help="Also save the priced quote here"); s.add_argument("--today")
    s.set_defaults(fn=cmd_quote)
    s = sub.add_parser("quote-pdf", help="Quote JSON -> client PDF (itinerary, prices, payments), plus the park plan with --plan")
    s.add_argument("quote"); s.add_argument("output"); s.add_argument("--plan", help="Patty's plan JSON to append")
    s.add_argument("--footer"); s.add_argument("--lang", choices=schema.LANGS)
    s.add_argument("--palette", help="Agency brand colors, main first"); s.add_argument("--color")
    s.set_defaults(fn=cmd_quote_pdf)

    s = sub.add_parser("vouchers", help="Vouchers and confirmations saved in trips, linked to their Trip Sheet bookings")
    s.add_argument("path", help="Agency folder, a trip folder, or a Trip Sheet")
    s.add_argument("--client", help="Only this client's trips (accent/case-insensitive)")
    s.add_argument("--query", help="Words to match in file names and bookings (provider, product, confirmation #, type)")
    s.add_argument("--active", action="store_true", help="Skip closed and cancelled trips")
    s.set_defaults(fn=cmd_vouchers)
    s = sub.add_parser("open", help="Open files with the computer's default app (folder mode on the agent's own computer)")
    s.add_argument("files", nargs="+"); s.set_defaults(fn=cmd_open)

    s = sub.add_parser("kb", help="The agent's Knowledge Base: tags and files; with --tag/--query/--all, the matching files' text")
    s.add_argument("paths", nargs="*", help="Agency folder, the Knowledge Base folder, or attached files")
    s.add_argument("--tag", action="append", help="A tag to load, e.g. DisneyPolicy (repeat for more; case and accents ignored)")
    s.add_argument("--query", help="Words that must all appear in the file")
    s.add_argument("--all", action="store_true", help="Every file's text")
    s.set_defaults(fn=cmd_kb)
    s = sub.add_parser("kb-note", help="Add, change or remove a rule in a Knowledge Base Word file (only when the agent asks)")
    s.add_argument("path", help="Agency folder, the Knowledge Base folder, or the .docx itself")
    s.add_argument("--doc", help="File name (new or existing); default: the file that has --tags")
    s.add_argument("--tags", nargs="+", help="Tags for the new text, e.g. DisneyPolicy Payments. Without --doc, the file with the first tag")
    s.add_argument("--add", help="Text to add at the end (one paragraph per line; '- ' for bullets)")
    s.add_argument("--replace", help="Exact text of the paragraph to change"); s.add_argument("--with", dest="with_text")
    s.add_argument("--remove", help="Exact text of the paragraph to delete")
    s.set_defaults(fn=cmd_kb_note)

    s = sub.add_parser("dashboard", help="Interactive HTML dashboard: next dates and pending tasks for every client and the agent")
    s.add_argument("paths", nargs="*", help="Agency folder, or Trip Sheets / My Tasks / Providers workbooks")
    s.add_argument("--out", help="HTML file to write (default: Dashboard.html in the agency folder)")
    s.add_argument("--lang", choices=schema.LANGS); s.add_argument("--today")
    s.set_defaults(fn=cmd_dashboard)

    args = p.parse_args()
    try:
        args.fn(args)
    except (FileOpenError, ValueError, RuntimeError) as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
