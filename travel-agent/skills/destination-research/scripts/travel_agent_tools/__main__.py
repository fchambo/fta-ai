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
    out({"base": base, "lang": lang, "providers_workbook": providers, "providers_created": created,
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

    for name, layout in (("trip", schema.TRIP_WORKBOOK), ("providers", schema.PROVIDERS_WORKBOOK)):
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

    args = p.parse_args()
    try:
        args.fn(args)
    except (FileOpenError, ValueError, RuntimeError) as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
