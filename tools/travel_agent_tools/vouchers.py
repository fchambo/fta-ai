"""Find the vouchers and confirmations saved in a trip's "4 - Bookings & Vouchers" folder.

Each file is linked to the Trip Sheet booking it belongs to, by the booking's confirmation number,
ID or product appearing in the file name, so the agent can ask for "the Pop Century voucher" or
"the Pérez flight" and get the right file. Bookings with no file are listed too, so missing
vouchers show up.
"""
import os
import subprocess
import sys
from datetime import datetime

from . import schema, workbooks
from .clients import norm

VOUCHERS_FOLDER = next(names for names in schema.TRIP_FOLDERS if names[0].startswith("4 - "))
SKIP_FILES = (".DS_Store", "Thumbs.db", "desktop.ini")
# Extensions agents save vouchers and confirmations as; anything else in the folder is still listed.
DOCUMENT_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".heic", ".webp", ".docx", ".doc", ".xlsx", ".eml", ".msg", ".txt", ".html")


def vouchers_dir(trip_dir):
    """The trip's vouchers folder in either language, or None if it doesn't exist."""
    for name in VOUCHERS_FOLDER:
        path = os.path.join(trip_dir, name)
        if os.path.isdir(path):
            return path
    return None


def list_files(folder):
    found = []
    for root, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(names):
            if name.startswith((".", "~$")) or name in SKIP_FILES:
                continue
            path = os.path.join(root, name)
            stat = os.stat(path)
            found.append({"name": name, "path": path, "subfolder": os.path.relpath(root, folder) if root != folder else "",
                          "size_kb": round(stat.st_size / 1024, 1),
                          "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                          "document": os.path.splitext(name)[1].lower() in DOCUMENT_EXTENSIONS})
    return found


def _compact(text):
    return norm(text).replace(" ", "")


def _booking_keys(booking):
    """Strings that, found in a file name, tie the file to this booking (strongest first)."""
    keys = []
    for field, minimum in (("confirmation", 4), ("id", 3), ("product", 4)):
        value = _compact(booking.get(field))
        if len(value) >= minimum:
            keys.append((field, value))
    return keys


def link(files, bookings):
    """Mark each file with the bookings its name matches, and each booking with its files."""
    for f in files:
        name = _compact(os.path.splitext(f["name"])[0] + " " + f["subfolder"])
        f["bookings"] = []
        for b in bookings:
            for field, key in _booking_keys(b):
                if key in name:
                    f["bookings"].append({"id": b.get("id"), "matched_on": field})
                    break
    for b in bookings:
        b["files"] = [f["name"] for f in files if any(m["id"] == b.get("id") for m in f["bookings"])]
    return files, bookings


def _haystack(*parts):
    return " ".join(norm(p) for p in parts if p not in (None, ""))


def matches(query_words, text):
    return all(w in text for w in query_words)


def trip(sheet_path, query=None):
    """Vouchers of one trip. With a query, only the files and bookings it matches (all words, any order,
    accents and case ignored); the client, destination and trip ID also count as part of every item."""
    data = workbooks.read(sheet_path, schema.TRIP_WORKBOOK)
    info = data["trip"]
    trip_dir = os.path.dirname(sheet_path)
    folder = vouchers_dir(trip_dir)
    files = list_files(folder) if folder else []
    bookings = [{k: b.get(k) for k in ("id", "type", "provider", "product", "confirmation", "start", "end", "details")}
                for b in data["bookings"] if any(b.get(k) for k in ("id", "product", "confirmation"))]
    files, bookings = link(files, bookings)
    by_id = {b.get("id"): b for b in bookings}
    trip_text = _haystack(info.get("client_name"), info.get("destinations"), info.get("trip_id"),
                          os.path.basename(trip_dir), os.path.basename(os.path.dirname(trip_dir)))
    words = norm(query).split() if query else []
    if words:
        def booking_text(b):
            return _haystack(*(b.get(k) for k in ("id", "type", "provider", "product", "confirmation", "details")),
                             schema.choice_label("booking_type", b.get("type"), "en"),
                             schema.choice_label("booking_type", b.get("type"), "es"))
        files = [f for f in files if matches(words, " ".join(
            [trip_text, _haystack(f["name"], f["subfolder"])] + [booking_text(by_id[m["id"]]) for m in f["bookings"] if m["id"] in by_id]))]
        bookings = [b for b in bookings if matches(words, trip_text + " " + booking_text(b))]
    return {"client": info.get("client_name"), "destinations": info.get("destinations"), "status": info.get("status"),
            "start_date": info.get("start_date"), "end_date": info.get("end_date"),
            "trip_sheet": sheet_path, "vouchers_dir": folder, "lang": data.get("_lang"),
            "files": files, "bookings": bookings,
            "bookings_without_file": [b.get("id") for b in bookings if not b["files"]],
            "files_without_booking": [f["name"] for f in files if not f["bookings"] and f["document"]]}


def open_file(path):
    """Open a file with the computer's default app (Preview, Acrobat, Word…)."""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise ValueError(f"File not found: {path}")
    if sys.platform == "darwin":
        subprocess.run(["open", path], check=True)
    elif os.name == "nt":
        os.startfile(path)  # noqa: S606 (Windows only)
    else:
        if subprocess.call(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            raise RuntimeError("No app to open files here (no desktop?). Give the agent the file's location instead.")
    return path
