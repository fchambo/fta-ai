"""The agent's Knowledge Base: their own rules, policies and preferences, in Word (or PDF) files
tagged with hashtags (#DisneyPolicy, #Commissions…). Every skill reads the tags that fit its task."""
import os
import re
import unicodedata
from datetime import datetime

from . import docs, schema

READABLE = (".docx", ".pdf", ".xlsx", ".xlsm", ".txt", ".md")
WRITABLE = (".docx",)
# A tag starts with a letter: "#12" (room numbers) and "# Title" aren't tags.
TAG = re.compile(r"(?<![\w#&/])#([^\W\d_][\w-]*)")
SMALL_KB_CHARS = 20000  # below this, loading everything is cheaper than choosing


def tag_key(tag):
    """#Disney-Policy, #disneypolicy and #DisneyPolícy are the same tag."""
    text = unicodedata.normalize("NFKD", tag.lstrip("#"))
    return re.sub(r"[\W_]+", "", "".join(c for c in text if not unicodedata.combining(c))).casefold()


def _plain(text):
    text = unicodedata.normalize("NFKD", text)
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).casefold().split())


def find_tags(text):
    seen = {}
    for m in TAG.finditer(text or ""):
        tag = m.group(1).rstrip("-")
        if len(tag) > 1:
            seen.setdefault(tag_key(tag), "#" + tag)
    return seen


def folder_for(base):
    """The workspace's Knowledge Base folder: whichever language name exists, else the workspace language's."""
    for name in schema.ROOT_FOLDERS["knowledge"]:
        if os.path.isdir(os.path.join(base, name)):
            return os.path.join(base, name)
    return None


def files_in(path):
    if os.path.isfile(path):
        return [path]
    found = []
    for folder, dirs, names in os.walk(path):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(names):
            if name.lower().endswith(READABLE) and not name.startswith(("~$", ".")):
                found.append(os.path.join(folder, name))
    return found


def _pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages).strip() or None
    except Exception:
        return None


def read(path, root=None):
    ext = os.path.splitext(path)[1].lower()
    text = _pdf_text(path) if ext == ".pdf" else docs.read_text(path)
    name = os.path.relpath(path, root) if root else os.path.basename(path)
    tags = find_tags(os.path.splitext(os.path.basename(path))[0])  # tags in the file name count too
    for key, tag in find_tags(text).items():
        tags.setdefault(key, tag)
    entry = {"file": name, "path": path, "tags": list(tags.values()), "_keys": set(tags),
             "modified": datetime.fromtimestamp(os.path.getmtime(path)).date().isoformat(),
             "chars": len(text or ""), "text": text}
    if text is None:
        entry["read_yourself"] = True  # a PDF we couldn't extract: Claude reads it with its own file reading
    return entry


def index(paths, root=None):
    return [read(p, root) for path in paths for p in files_in(path)]


def summary(entries):
    tags = {}
    for e in entries:
        for tag in e["tags"]:
            item = tags.setdefault(tag_key(tag), {"tag": tag, "files": []})
            item["files"].append(e["file"])
    return sorted(tags.values(), key=lambda t: (-len(t["files"]), t["tag"].lower()))


def select(entries, tags=(), query=None):
    keys = {tag_key(t) for t in tags if tag_key(t)}
    words = _plain(query).split() if query else []
    picked = []
    for e in entries:
        haystack = _plain(e["file"] + " " + (e["text"] or ""))
        by_tag = bool(keys & e["_keys"])
        by_query = bool(words) and all(w in haystack for w in words)
        if by_tag or by_query:
            picked.append(dict(e, matched=sorted(t for t in e["tags"] if tag_key(t) in keys) or ["query"]))
    return picked


def public(entry, with_text):
    return {k: v for k, v in entry.items() if not k.startswith("_") and k != "path" and (with_text or k != "text")}


# --- writing (only when the agent asks) ------------------------------------------------

def _norm_ws(text):
    return " ".join(str(text).split())


def _matching_paragraphs(doc, old):
    target = _norm_ws(old)
    return [p for p in doc.paragraphs if target and target in _norm_ws(p.text)]


def _set_text(paragraph, text):
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for run in runs[1:]:
        run._element.getparent().remove(run._element)


def write(path, title=None, add=None, tags=(), replace=None, remove=None):
    """Create or edit one Knowledge Base Word file. Returns what changed."""
    from docx import Document
    created = not os.path.exists(path)
    doc = Document() if created else Document(path)
    wanted = {tag_key(t): "#" + t.lstrip("#") for t in tags if tag_key(t)}
    if created:
        doc.add_heading(title or os.path.splitext(os.path.basename(path))[0], level=1)
        if wanted:
            doc.add_paragraph(" ".join(wanted.values()))
            wanted = {}
    else:
        have = find_tags("\n".join(p.text for p in doc.paragraphs))
        wanted = {k: v for k, v in wanted.items() if k not in have}

    changed = []
    if replace is not None or remove is not None:
        old = replace if replace is not None else remove
        matches = _matching_paragraphs(doc, old)
        if not matches:
            raise ValueError(f"No paragraph contains: {old!r}")
        if len(matches) > 1:
            raise ValueError(f"{len(matches)} paragraphs contain {old!r}: quote more of the one to change")
        p = matches[0]
        if remove is not None:
            p._element.getparent().remove(p._element)
            changed.append({"removed": p.text})
        else:
            new = p.text.replace(old, add) if old in p.text else add
            changed.append({"replaced": p.text, "with": new})
            _set_text(p, new)
            add = None
    if add:
        lines = [line.strip() for line in str(add).splitlines() if line.strip()]
        if wanted and lines:
            lines[-1] += " " + " ".join(wanted.values())
            wanted = {}
        for line in lines:
            bullet = line[:2] in ("- ", "* ", "• ")
            try:
                doc.add_paragraph(line[2:] if bullet else line, style="List Bullet" if bullet else None)
            except KeyError:  # the agent's own document has no bullet style
                doc.add_paragraph("• " + line[2:] if bullet else line)
        changed.append({"added": lines})
    if wanted:  # tags with nothing else to attach them to
        doc.add_paragraph(" ".join(wanted.values()))
        changed.append({"tagged": list(wanted.values())})
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        doc.save(path)
    except PermissionError:
        raise PermissionError(f"Can't save {os.path.basename(path)}: close it in Word and try again.")
    return {"created": created, "changes": changed}
