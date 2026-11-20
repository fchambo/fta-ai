"""Client workspaces: find a client (accent/case-insensitive), summarize their past trips, keep a profile.

The profile is a Markdown file the agent never needs to open: Claude reads it at the start of every
new request ("what we remember") and adds what it learned at the end.
"""
import os
import re
import unicodedata
from datetime import date

from . import schema, workbooks

PROFILE = ("Client Profile.md", "Perfil del Cliente.md")

TEMPLATE = {
    "en": """# {client}

_Client since {today}. Claude reads this file before every new request and adds what it learns._

## Contact
- Email:
- Phone / WhatsApp:
- Preferred contact:
- Language with the client:

## Travelers (usual group)
<!-- One line each: name, birth date, relationship. Kids: height in cm and the date it was measured. -->

## Preferences
<!-- Hotels, airlines, seats, pace, budget range, food, what they loved or disliked. -->

## Health & accessibility
<!-- Mobility, wheelchair/ECV, fears (claustrophobia, motion sickness), allergies, DAS/AAP. -->

## Past trips
<!-- One line per trip: YYYY-MM destination, what was sold, how it went. -->

## Agent notes
""",
    "es": """# {client}

_Cliente desde {today}. Claude lee este archivo antes de cada nueva consulta y agrega lo que aprende._

## Contacto
- Email:
- Teléfono / WhatsApp:
- Contacto preferido:
- Idioma con el cliente:

## Pasajeros (grupo habitual)
<!-- Una línea por persona: nombre, fecha de nacimiento, parentesco. Chicos: altura en cm y fecha en que se midió. -->

## Preferencias
<!-- Hoteles, aerolíneas, asientos, ritmo, rango de presupuesto, comidas, qué les gustó o no. -->

## Salud y accesibilidad
<!-- Movilidad, silla de ruedas/scooter, miedos (claustrofobia, mareos), alergias, DAS/AAP. -->

## Viajes anteriores
<!-- Una línea por viaje: AAAA-MM destino, qué se vendió, cómo salió. -->

## Notas del agente
""",
}


def norm(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def match_score(query, candidate):
    """3 exact, 2 every query word is in the candidate, 1 some word matches, 0 none."""
    q, c = norm(query), norm(candidate)
    if not q or not c:
        return 0
    if q == c:
        return 3
    qw, cw = q.split(), set(c.split())
    if all(any(w == x or (len(w) >= 3 and x.startswith(w)) for x in cw) for w in qw):
        return 2
    surnames = [w for w in qw if len(w) >= 3]
    return 1 if any(w in cw for w in surnames) else 0


def age_on(birth, when):
    birth = workbooks.parse_date(birth)
    if not birth:
        return None
    return when.year - birth.year - ((when.month, when.day) < (birth.month, birth.day))


def trip_summary(path, today):
    data = workbooks.read(path, schema.TRIP_WORKBOOK)
    info = data["trip"]
    start = workbooks.parse_date(info.get("start_date"))
    travelers = []
    for t in data["travelers"]:
        travelers.append({k: v for k, v in {
            "name": t.get("name"), "birth_date": t.get("birth_date"),
            "age_now": age_on(t.get("birth_date"), today),
            "age_on_trip": age_on(t.get("birth_date"), start) if start else None,
            "notes": t.get("notes")}.items() if v not in (None, "")})
    bookings = [{k: v for k, v in {
        "type": b.get("type"), "provider": b.get("provider"), "product": b.get("product"),
        "start": b.get("start"), "end": b.get("end"), "details": b.get("details"),
        "gross": b.get("gross_amount"), "currency": b.get("currency")}.items() if v not in (None, "")}
        for b in data["bookings"]]
    return {
        "path": path, "trip_dir": os.path.dirname(path), "trip_id": info.get("trip_id"), "status": info.get("status"),
        "destinations": info.get("destinations"), "start_date": info.get("start_date"), "end_date": info.get("end_date"),
        "purpose": info.get("purpose"), "client_language": info.get("client_language"),
        "budget": " ".join(str(x) for x in (info.get("budget_amount"), info.get("budget_currency"), info.get("budget_per")) if x) or None,
        "notes": info.get("notes"), "travelers": travelers, "bookings": bookings,
    }


def find(base, query, trip_sheets, today=None):
    """Candidates for `query` among client folders and Trip Sheet client names, best first."""
    today = today or date.today()
    candidates = {}
    clients_root = None
    for names in [schema.ROOT_FOLDERS["clients"]]:
        for n in names:
            if os.path.isdir(os.path.join(base, n)):
                clients_root = os.path.join(base, n)
    if clients_root:
        for name in sorted(os.listdir(clients_root)):
            d = os.path.join(clients_root, name)
            if os.path.isdir(d) and not name.startswith("."):
                candidates.setdefault(d, {"client": name, "client_dir": d, "names": {name}, "trip_paths": []})
    for path in trip_sheets:
        d = os.path.dirname(os.path.dirname(path))
        entry = candidates.setdefault(d, {"client": os.path.basename(d), "client_dir": d, "names": {os.path.basename(d)}, "trip_paths": []})
        entry["trip_paths"].append(path)
        try:
            name = workbooks.read(path, schema.TRIP_WORKBOOK)["trip"].get("client_name")
        except Exception:
            name = None
        if name:
            entry["names"].add(name)
    scored = []
    for entry in candidates.values():
        score = max(match_score(query, n) for n in entry["names"])
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda x: (-x[0], x[1]["client"]))
    return [{**e, "names": sorted(e["names"]), "score": s} for s, e in scored]


def profile_path(client_dir, lang):
    for name in PROFILE:
        p = os.path.join(client_dir, name)
        if os.path.exists(p):
            return p
    return os.path.join(client_dir, PROFILE[schema.LANGS.index(lang)])


def load(entry, lang, today=None):
    today = today or date.today()
    path = profile_path(entry["client_dir"], lang)
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    trips = []
    for p in entry["trip_paths"]:
        try:
            trips.append(trip_summary(p, today))
        except Exception as e:  # a damaged or foreign workbook shouldn't hide the others
            trips.append({"path": p, "error": str(e)})
    trips.sort(key=lambda t: t.get("start_date") or t.get("trip_id") or "", reverse=True)
    return {"client": entry["client"], "client_dir": entry["client_dir"], "profile_path": path,
            "profile_exists": text is not None, "profile": text, "trips": trips}


def create(clients_root, client, lang, safe_name, today=None):
    today = today or date.today()
    d = os.path.join(clients_root, safe_name(client))
    os.makedirs(d, exist_ok=True)
    path = profile_path(d, lang)
    created = False
    if not os.path.exists(path):
        stamp = today.strftime("%d/%m/%Y") if lang == "es" else today.isoformat()
        with open(path, "w", encoding="utf-8") as f:
            f.write(TEMPLATE[lang].format(client=client, today=stamp))
        created = True
    return {"client": client, "client_dir": d, "profile_path": path, "profile_created": created,
            "profile": open(path, encoding="utf-8").read(), "trips": []}
