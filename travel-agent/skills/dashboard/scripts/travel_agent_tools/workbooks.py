"""Create, read and update the agent-facing Excel workbooks."""
import os
import re
from datetime import date, datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from . import schema

HEADER_FILL = PatternFill("solid", fgColor="0F766E")
HEADER_FONT = Font(bold=True, color="FFFFFF")
LABEL_FONT = Font(bold=True)
DATE_FORMAT = {"en": "yyyy-mm-dd", "es": "dd/mm/yyyy"}
VALIDATION_ROWS = 500


class FileOpenError(Exception):
    pass


# --- value conversion ----------------------------------------------------------

def parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):  # agents in LatAm/Europe write day first
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date: {value!r} (use YYYY-MM-DD or DD/MM/YYYY)")


def to_cell(kind, value, lang):
    if value in (None, ""):
        return None
    if kind == "date":
        return parse_date(value)
    if kind == "number":
        return float(value) if not isinstance(value, (int, float)) else value
    if kind.startswith("choice:"):
        return schema.choice_label(kind.split(":", 1)[1], schema.choice_code(kind.split(":", 1)[1], value), lang)
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return value


def from_cell(kind, value):
    if value in (None, ""):
        return None
    if kind == "date":
        d = parse_date(value)
        return d.isoformat() if d else None
    if kind == "number":
        try:
            n = float(value)
        except (TypeError, ValueError):
            return None
        return int(n) if n.is_integer() else n
    if kind.startswith("choice:"):
        return schema.choice_code(kind.split(":", 1)[1], value)
    return str(value).strip() if isinstance(value, str) else value


def set_cell(ws, row, column, value):
    """Write a value, never as a formula: text comes from clients, PDFs and chats (formula injection)."""
    cell = ws.cell(row=row, column=column, value=value)
    if isinstance(value, str) and cell.data_type == "f":
        cell.data_type = "s"
    return cell


# --- file safety ------------------------------------------------------------------

def ensure_closed(path):
    """Excel and Word write a ~$ lock file while a document is open; saving then loses edits."""
    folder, name = os.path.split(os.path.abspath(path))
    for candidate in ("~$" + name, "~$" + name[2:]):
        if os.path.exists(os.path.join(folder, candidate)):
            raise FileOpenError(f"'{name}' is open in Excel or Word. Close it first so no edits are lost.")


# --- writing ------------------------------------------------------------------------

def _add_choice_validation(ws, kind, cell_range, lang):
    options = schema.choice_labels(kind.split(":", 1)[1], lang)
    dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
    dv.error = "Choose a value from the list"
    ws.add_data_validation(dv)
    dv.add(cell_range)


def _write_kv(ws, fields, values, lang):
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 48
    for row, (key, *_rest) in enumerate(fields, start=1):
        kind = _rest[-1]
        ws.cell(row=row, column=1, value=schema.label((key, *_rest), lang)).font = LABEL_FONT
        cell = set_cell(ws, row, 2, to_cell(kind, values.get(key), lang))
        if kind == "date":
            cell.number_format = DATE_FORMAT[lang]
        if kind.startswith("choice:"):
            _add_choice_validation(ws, kind, f"B{row}", lang)


def _write_table(ws, fields, rows, lang, fresh):
    if fresh:
        for col, field in enumerate(fields, start=1):
            cell = ws.cell(row=1, column=col, value=schema.label(field, lang))
            cell.fill, cell.font = HEADER_FILL, HEADER_FONT
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            ws.column_dimensions[get_column_letter(col)].width = max(12, min(32, len(cell.value) + 4))
            kind = field[-1]
            letter = get_column_letter(col)
            if kind.startswith("choice:"):
                _add_choice_validation(ws, kind, f"{letter}2:{letter}{VALIDATION_ROWS}", lang)
        ws.freeze_panes = "A2"
    elif ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)
    for r, row in enumerate(rows, start=2):
        for col, (key, *_rest) in enumerate(fields, start=1):
            kind = _rest[-1]
            cell = set_cell(ws, r, col, to_cell(kind, row.get(key), lang))
            if kind == "date":
                cell.number_format = DATE_FORMAT[lang]
    if fresh:
        for col, (_key, *_rest) in enumerate(fields, start=1):
            if _rest[-1] == "date":
                for r in range(2, VALIDATION_ROWS):
                    ws.cell(row=r, column=col).number_format = DATE_FORMAT[lang]


def create(path, layout, data, lang):
    wb = Workbook()
    wb.remove(wb.active)
    for key, (en, es, fields, kind) in layout.items():
        ws = wb.create_sheet(en if lang == "en" else es)
        if kind == "kv":
            _write_kv(ws, fields, data.get(key) or {}, lang)
        else:
            _write_table(ws, fields, data.get(key) or [], lang, fresh=True)
    wb.save(path)


# --- reading ------------------------------------------------------------------------

def _find_sheet(wb, en, es):
    for name in (en, es):
        if name in wb.sheetnames:
            return wb[name]
    lowered = {n.lower(): n for n in wb.sheetnames}
    for name in (en, es):
        if name.lower() in lowered:
            return wb[lowered[name.lower()]]
    return None


def _label_map(fields):
    mapping = {}
    for key, en, es, kind in fields:
        for lbl in (key, en, es):
            mapping[lbl.strip().lower()] = (key, kind)
    return mapping


def _read_kv(ws, fields):
    mapping, out = _label_map(fields), {}
    for row in ws.iter_rows(min_row=1, max_col=2, values_only=True):
        if row[0] is None:
            continue
        hit = mapping.get(str(row[0]).strip().lower())
        if hit:
            out[hit[0]] = from_cell(hit[1], row[1])
    return out


def _read_table(ws, fields):
    mapping = _label_map(fields)
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    columns = [mapping.get(str(h).strip().lower()) if h is not None else None for h in rows[0]]
    unknown = [str(h) for h, c in zip(rows[0], columns) if h is not None and c is None]
    out = []
    for raw in rows[1:]:
        if all(v in (None, "") for v in raw):
            continue
        item = {}
        for col, value in zip(columns, raw):
            if col:
                item[col[0]] = from_cell(col[1], value)
        out.append(item)
    return out, unknown


def detect_lang(wb, layout):
    first_en, first_es = next(iter(layout.values()))[:2]
    return "es" if first_es in wb.sheetnames and first_en not in wb.sheetnames else "en"


def read(path, layout):
    wb = load_workbook(path, data_only=True)
    data, warnings = {"_lang": detect_lang(wb, layout)}, []
    for key, (en, es, fields, kind) in layout.items():
        ws = _find_sheet(wb, en, es)
        if ws is None:
            warnings.append(f"Sheet '{en}' / '{es}' not found")
            data[key] = {} if kind == "kv" else []
            continue
        if kind == "kv":
            data[key] = _read_kv(ws, fields)
        else:
            data[key], unknown = _read_table(ws, fields)
            if unknown:
                warnings.append(f"Sheet '{ws.title}': ignored unknown columns {unknown}")
    data["_warnings"] = warnings
    return data


def is_layout(path, layout):
    try:
        wb = load_workbook(path, read_only=True)
    except Exception:
        return False
    en, es = next(iter(layout.values()))[:2]
    return en in wb.sheetnames or es in wb.sheetnames


# --- updating -----------------------------------------------------------------------

UPSERT_KEYS = {
    "travelers": ("name",),
    "bookings": ("id",),
    "payments": ("booking", "description"),
    "deadlines": ("date", "what"),
    "providers": ("id",),
    "products": ("provider_id", "product_id"),
    "incentives": ("provider_id", "period", "from_volume"),
    "tasks": ("task",),
    "lessons": ("skill", "lesson"),
}


def _norm(v):
    return str(v).strip().lower() if v not in (None, "") else ""


def merge_rows(current, incoming, keys, replace=False):
    if replace:
        return incoming
    result = [dict(r) for r in current]
    for new in incoming:
        k = tuple(_norm(new.get(f)) for f in keys)
        match = next((r for r in result if tuple(_norm(r.get(f)) for f in keys) == k), None)
        if match is not None:
            match.update({f: v for f, v in new.items() if v is not None and f not in keys})
        else:
            result.append(new)
    return result


def update(path, layout, changes, replace=()):
    """Merge `changes` ({sheet_key: dict | list}) into the workbook, keeping its formatting."""
    ensure_closed(path)
    current = read(path, layout)
    lang = current["_lang"]
    wb = load_workbook(path)
    for key, value in changes.items():
        if key not in layout:
            raise ValueError(f"Unknown section '{key}'. Valid: {', '.join(layout)}")
        en, es, fields, kind = layout[key]
        ws = _find_sheet(wb, en, es)
        if kind == "kv":
            merged = {**current[key], **{k: v for k, v in value.items() if v is not None}}
            for row in range(1, ws.max_row + 1):
                ws.cell(row=row, column=2).value = None
            _write_kv(ws, fields, merged, lang)
        else:
            merged = merge_rows(current[key], value, UPSERT_KEYS[key], replace=key in replace)
            _write_table(ws, fields, merged, lang, fresh=False)
    wb.save(path)
    return read(path, layout)


# --- generic tables (reports, content calendars) -------------------------------------

def write_tables(path, sheets):
    """sheets: [{name, columns: [str], rows: [[...]] or [{col: val}]}] -> styled xlsx."""
    wb = Workbook()
    wb.remove(wb.active)
    for sheet in sheets:
        ws = wb.create_sheet(re.sub(r"[\\/*?:\[\]]", "-", str(sheet["name"]))[:31] or "Sheet")
        cols = sheet["columns"]
        for c, name in enumerate(cols, start=1):
            cell = set_cell(ws, 1, c, name)
            cell.fill, cell.font = HEADER_FILL, HEADER_FONT
            ws.column_dimensions[get_column_letter(c)].width = max(12, min(48, len(str(name)) + 4))
        for r, row in enumerate(sheet.get("rows") or [], start=2):
            values = [row.get(c) for c in cols] if isinstance(row, dict) else row
            for c, v in enumerate(values, start=1):
                if isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-":
                    try:
                        v = date.fromisoformat(v)
                    except ValueError:
                        pass
                cell = set_cell(ws, r, c, v)
                if isinstance(v, date):
                    cell.number_format = "yyyy-mm-dd"
                if isinstance(v, str) and len(v) > 40:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
                    ws.column_dimensions[get_column_letter(c)].width = 48
        ws.freeze_panes = "A2"
    wb.save(path)
