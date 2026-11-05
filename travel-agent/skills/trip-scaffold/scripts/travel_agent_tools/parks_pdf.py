"""Client PDF for a park plan: cover, booking calendar, then one section per park day
with a map of the route (real park layout from OpenStreetMap when available), the fixed-time table and the full schedule."""
import math
from datetime import date
from xml.sax.saxutils import escape

from . import parks as P
from .docs import _pdf_font

L = {
    "title": ("Theme Park Plan", "Plan de Parques"),
    "for": ("Prepared for {client}", "Preparado para {client}"),
    "party": ("Who's going", "Quiénes viajan"),
    "name": ("Name", "Nombre"), "age": ("Age", "Edad"), "height": ("Height", "Altura"), "notes": ("Notes", "Notas"),
    "overview": ("Your park days", "Tus días de parque"),
    "day": ("Day", "Día"), "date": ("Date", "Fecha"), "park": ("Park", "Parque"), "hours": ("Park hours", "Horario"),
    "arrive": ("Arrive", "Llegada"), "highlights": ("Must-dos", "Imperdibles"),
    "bookings": ("Booking calendar", "Calendario de reservas"),
    "time_et": ("Time (Orlando)", "Hora (Orlando)"), "what": ("What", "Qué"),
    "asap": ("As soon as possible", "Lo antes posible"),
    "b_dining": ("Disney dining reservations open (60 days before; resort guests can book their whole stay)",
                 "Abren las reservas de restaurantes de Disney (60 días antes; huéspedes de hoteles Disney reservan toda la estadía)"),
    "b_ll_resort": ("Lightning Lane purchase and booking opens for Disney resort guests (7 days before check-in, for the whole stay)",
                    "Abre la compra y reserva de Lightning Lane para huéspedes de hoteles Disney (7 días antes del check-in, para toda la estadía)"),
    "b_ll_offsite": ("Lightning Lane purchase and booking opens for {park} (3 days before)",
                     "Abre la compra y reserva de Lightning Lane para {park} (3 días antes)"),
    "b_das": ("Register for Disney's Disability Access Service (DAS) by video chat, up to 30 days before",
              "Registrar el Disability Access Service (DAS) de Disney por videollamada, hasta 30 días antes"),
    "b_iac": ("Get the IBCCES Individual Accessibility Card (IAC), needed for Universal's Attraction Assistance Pass",
              "Tramitar la IBCCES Individual Accessibility Card (IAC), necesaria para el Attraction Assistance Pass de Universal"),
    "b_express_buy": ("Buy Universal Express: prices rise closer to the date and it can sell out",
                  "Comprar Universal Express: el precio sube cerca de la fecha y puede agotarse"),
    "how": ("How to use this plan", "Cómo usar este plan"),
    "how1": ("Follow the numbered stops in order: the order is what keeps lines short. If you fall behind, skip a flexible stop, never a fixed-time one.",
             "Seguí las paradas numeradas en orden: el orden es lo que acorta las filas. Si se atrasan, salteen una parada flexible, nunca una con horario fijo."),
    "how2": ("Waits are estimates for a typical day with the expected crowds. Check live waits in the official app on the day.",
             "Las esperas son estimadas para un día típico con la concurrencia prevista. El mismo día, miren las esperas en vivo en la app oficial."),
    "how3": ("Heights are measured at each ride's entrance with shoes on. Rules and hours can change: confirm in the official app before you go.",
             "Las alturas se miden en la entrada de cada atracción, con calzado. Reglas y horarios pueden cambiar: confirmen en la app oficial antes de ir."),
    "how_switch": ("Rider Switch (Disney) / Child Swap (Universal): the whole group queues once; one adult stays with the kids who can't ride, then the adults swap without queuing again.",
                   "Rider Switch (Disney) / Child Swap (Universal): todo el grupo hace la fila una vez; un adulto se queda con los chicos que no pueden subir y después cambian sin volver a hacer la fila."),
    "map": ("Your route", "Tu recorrido"),
    "fixed": ("At a fixed time", "Con horario fijo"),
    "fixed_none": ("No fixed times today: follow the route in order.", "Hoy no hay horarios fijos: sigan el recorrido en orden."),
    "schedule": ("Step by step", "Paso a paso"),
    "time": ("Time", "Hora"), "stop": ("Stop", "Parada"), "area": ("Area", "Zona"), "line": ("Line", "Fila"),
    "wait": ("Est. wait", "Espera est."), "why": ("Why", "Por qué"),
    "skipped": ("Not in today's plan", "Fuera del plan de hoy"),
    "tips": ("Tips for today", "Consejos para hoy"),
    "totals": ("Estimated time in lines: {wait}. About {saved} less than doing the same rides at a typical time of day.",
               "Tiempo estimado en filas: {wait}. Aproximadamente {saved} menos que haciendo las mismas atracciones en un horario típico."),
    "totals_plain": ("Estimated time in lines: {wait}.", "Tiempo estimado en filas: {wait}."),
    "legend_fixed": ("Fixed time", "Horario fijo"), "legend_flex": ("Flexible order", "Orden flexible"),
    "legend_route": ("Walking route", "Recorrido a pie"), "legend_entrance": ("Entrance", "Entrada"),
    "schematic": ("Schematic map, not to scale", "Mapa esquemático, no a escala"),
    "osm_credit": ("Map: © OpenStreetMap contributors", "Mapa: © colaboradores de OpenStreetMap"),
    "arrive_step": ("Arrive at the entrance", "Llegada a la entrada"),
    "arrive_early": ("Arrive at the entrance (Early Entry for hotel guests)", "Llegada a la entrada (Early Entry para huéspedes)"),
    "leave_step": ("Head to the exit", "Salida del parque"),
    "transfer_step": ("Arrive in the other park: the plan continues on the next page", "Llegan al otro parque: el plan sigue en la página siguiente"),
    "free": ("Free time: snacks, shops, photos", "Tiempo libre: snacks, tiendas, fotos"),
    "free_repeat": ("Free time: repeat your favorites (check live waits), shops, characters",
                    "Tiempo libre: repetir sus favoritas (miren las esperas en vivo), tiendas, personajes"),
    "open_now": ("Already open: book now", "Ya está abierto: reservar ahora"),
    "lunch": ("Lunch (quick service nearby)", "Almuerzo (comida rápida cerca)"),
    "dinner": ("Dinner (quick service nearby)", "Cena (comida rápida cerca)"),
    "rest": ("Rest and snack in the shade", "Descanso y merienda a la sombra"),
    "break": ("Break at the hotel", "Descanso en el hotel"),
    "why_ll": ("Lightning Lane return window {a}–{b}", "Ventana de regreso Lightning Lane {a}–{b}"),
    "why_ll_suggested": ("Book Lightning Lane for about {a} (take the closest time available)",
                         "Reservar Lightning Lane para las {a} aprox. (o el horario más cercano disponible)"),
    "why_show": ("Show at {a}: arrive a little early for a good spot", "Función a las {a}: lleguen un poco antes para buen lugar"),
    "why_meal": ("Reservation", "Reserva"),
    "why_break": ("Back at {a}", "Regreso a las {a}"),
    "switch": ("Rider Switch: {who} {verb} while the others ride, then the adults swap (no second queue)",
               "Rider Switch: {who} {verb} mientras los demás suben y después cambian los adultos (sin repetir la fila)"),
    "switch_u": ("Child Swap: {who} {verb} while the others ride, then the adults swap (no second queue)",
                 "Child Swap: {who} {verb} mientras los demás suben y después cambian los adultos (sin repetir la fila)"),
    "sits_out": ("{who} {verb} this one", "{who} no {verb}"),
    "v_wait": (("waits", "wait"), ("espera", "esperan")),
    "v_skip": (("skips", "skip"), ("sube", "suben")),
    "lane_standby": ("Standby", "Fila normal"), "lane_ll_multi": ("Lightning Lane", "Lightning Lane"),
    "lane_ll_single": ("LL Single Pass", "LL Single Pass"), "lane_express": ("Express", "Express"),
    "lane_ll_express": ("Express", "Express"),
    "lane_single_rider": ("Single rider", "Single rider"), "lane_standby_das": ("DAS return time", "Hora de regreso DAS"),
    "lane_standby_aap": ("AAP return time", "Hora de regreso AAP"),
    "r_closed": ("Closed or under refurbishment on your dates", "Cerrada o en remodelación en sus fechas"),
    "r_too_short": ("{who}: minimum height {detail}", "{who}: altura mínima {detail}"),
    "r_height_unknown": ("{who}: confirm height (minimum {detail})", "{who}: confirmar altura (mínimo {detail})"),
    "r_too_intense": ("{who}: too intense", "{who}: demasiado intensa"),
    "r_tags": ("{who}: {detail}", "{who}: {detail}"),
    "r_access": ("{who}: requires transferring from the wheelchair or walking", "{who}: requiere pasarse de la silla de ruedas o caminar"),
    "r_skip": ("{who}: not interested", "{who}: no le interesa"),
    "r_needs_child": ("{who}: only rides with a child", "{who}: solo sube acompañando a un chico"),
    "min": ("{m} min", "{m} min"), "hmin": ("{h} h {m} min", "{h} h {m} min"),
    "none": ("—", "—"),
}

TAG = {
    "enclosed": ("confined space", "espacio cerrado"), "dark": ("dark", "oscuridad"),
    "sim": ("motion simulator", "simulador de movimiento"), "spin": ("spinning", "giros"),
    "heights": ("heights", "altura"), "drops": ("drops", "caídas"), "scary": ("scary scenes", "escenas que asustan"),
    "coaster": ("roller coaster", "montaña rusa"), "wet": ("you get wet", "te mojás"), "loud": ("loud", "ruido fuerte"),
    "fire": ("fire effects", "efectos de fuego"), "bumpy": ("bumpy ride", "muchos saltos"), "launch": ("fast launch", "lanzamiento"),
    "backwards": ("goes backwards", "va hacia atrás"), "3d": ("3D", "3D"),
}

FLAG = {
    "claustrophobic": ("claustrophobia", "claustrofobia"), "motion_sickness": ("motion sickness", "se marea"),
    "fear_dark": ("afraid of the dark", "miedo a la oscuridad"), "fear_heights": ("afraid of heights", "miedo a las alturas"),
    "scared_easily": ("scares easily", "se asusta fácil"), "no_coasters": ("no roller coasters", "sin montañas rusas"),
    "no_wet": ("doesn't want to get wet", "no quiere mojarse"), "sensory": ("sensitive to noise", "sensible al ruido"),
    "mild_only": ("gentle rides only", "solo atracciones suaves"), "no_thrill": ("no rides with motion", "sin juegos con movimiento"),
    "pregnant": ("pregnant", "embarazada"), "back_neck": ("back or neck issues", "problemas de espalda o cuello"),
    "wheelchair": ("wheelchair / ECV", "silla de ruedas / scooter"), "no_transfer": ("stays in wheelchair", "no se pasa de la silla"),
    "limited_walking": ("limited walking", "camina poco"), "das": ("accessibility pass (DAS/AAP)", "pase de accesibilidad (DAS/AAP)"),
}

WEEKDAYS = (("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"), ("lun", "mar", "mié", "jue", "vie", "sáb", "dom"))
MONTHS_ES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")

FIXED_COLOR, FLEX_COLOR, ROUTE_COLOR = "#EA580C", "#0F766E", "#4150F7"
ARROW_COLOR = "#16A34A"
ROUTE_DOTS = [0.1, 4]


def tr(lang, key, **kw):
    en, es = L[key]
    return (es if lang == "es" else en).format(**kw)


def verb(key, count, lang):
    forms = L[key][1 if lang == "es" else 0]
    return forms[0] if count == 1 else forms[1]


def join_names(names, lang):
    if len(names) < 2:
        return "".join(names)
    return ", ".join(names[:-1]) + (" y " if lang == "es" else " and ") + names[-1]


def day_numbers(plan):
    seen, out = [], []
    for d in plan["days"]:
        key = d.get("date") or str(len(seen))
        if key not in seen:
            seen.append(key)
        out.append(seen.index(key) + 1)
    return out


def pick(table, key, lang):
    pair = table.get(key)
    return (pair[1] if lang == "es" else pair[0]) if pair else key


def day_text(iso, lang):
    if not iso:
        return ""
    d = date.fromisoformat(iso)
    wd = WEEKDAYS[1 if lang == "es" else 0][d.weekday()]
    return f"{wd} {d.day:02d}/{d.month:02d}/{d.year}" if lang == "es" else f"{wd} {d.day} {d.strftime('%b')} {d.year}"


def duration(minutes, lang):
    minutes = int(minutes)
    return tr(lang, "hmin", h=minutes // 60, m=minutes % 60) if minutes >= 60 else tr(lang, "min", m=minutes)


def short_land(name):
    if " – " not in name:
        return name
    head, tail = name.split(" – ", 1)
    return head if len(head.split()) == 1 else tail


def short_name(name, n=24):
    name = name.split(" (")[0].split(" – ")[0].split(":")[0] if len(name) > n else name
    return name if len(name) <= n else name[: n - 1] + "…"


def height_text(p):
    if p.get("height_cm"):
        cm = float(p["height_cm"])
        return f"{cm:g} cm / {cm / 2.54:.0f} in"
    if p.get("height_in"):
        i = float(p["height_in"])
        return f"{i * 2.54:.0f} cm / {i:g} in"
    return "—"


# --- map -------------------------------------------------------------------------

def _clip_poly(pts, x0, y0, x1, y1):
    """Sutherland-Hodgman: clip a polygon to a rectangle."""
    def cut(pts, inside, cross):
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        return out

    def at_x(x):
        return lambda p, q: (x, p[1] + (q[1] - p[1]) * (x - p[0]) / ((q[0] - p[0]) or 1e-9))

    def at_y(y):
        return lambda p, q: (p[0] + (q[0] - p[0]) * (y - p[1]) / ((q[1] - p[1]) or 1e-9), y)

    for inside, cross in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                          (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not pts:
            break
        pts = cut(pts, inside, cross)
    return pts


def _clip_line(pts, x0, y0, x1, y1):
    """Split a polyline into the pieces inside a rectangle (Liang-Barsky per segment)."""
    pieces, cur = [], []
    for p, q in zip(pts, pts[1:]):
        dx, dy = q[0] - p[0], q[1] - p[1]
        t0, t1, ok = 0.0, 1.0, True
        for pk, qk in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
            if pk == 0:
                if qk < 0:
                    ok = False
            else:
                r = qk / pk
                if pk < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
        if not ok or t0 > t1:
            if len(cur) > 1:
                pieces.append(cur)
            cur = []
            continue
        a = (p[0] + t0 * dx, p[1] + t0 * dy)
        b = (p[0] + t1 * dx, p[1] + t1 * dy)
        if not cur or cur[-1] != a:
            if len(cur) > 1:
                pieces.append(cur)
            cur = [a]
        cur.append(b)
        if t1 < 1:
            pieces.append(cur)
            cur = []
    if len(cur) > 1:
        pieces.append(cur)
    return pieces


def _osm_map(park, day, lang, font, width, net):
    """The park's real layout (OpenStreetMap) with the day's route along the walkways."""
    from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, PolyLine, Rect, String
    from reportlab.lib import colors
    from reportlab.pdfbase.pdfmetrics import stringWidth

    data = net.data
    stops = [s for s in day["steps"] if s.get("x") is not None and s["kind"] != "free"]
    # route along the walkways, stop to stop
    route = []
    for a, b in zip(stops, stops[1:]):
        seg = net.path((a["x"], a["y"]), (b["x"], b["y"]))
        route.extend(seg if not route else seg[1:])

    # frame: the guest area (every attraction and the entrance), widened to the map's aspect
    keep = [net.nodes[i] for i in data["places"].values()] + [net.nodes[data["entrance"]]] + route
    pad = 45
    x0, x1 = min(p[0] for p in keep) - pad, max(p[0] for p in keep) + pad
    y0, y1 = min(p[1] for p in keep) - pad, max(p[1] for p in keep) + pad
    ratio = min(1.0, max(0.62, (y1 - y0) / (x1 - x0)))
    height = width * ratio
    legend_h = 22
    if (y1 - y0) / (x1 - x0) < ratio:
        grow = (x1 - x0) * ratio - (y1 - y0)
        y0, y1 = y0 - grow / 2, y1 + grow / 2
    else:
        grow = (y1 - y0) / ratio - (x1 - x0)
        x0, x1 = x0 - grow / 2, x1 + grow / 2
    k = width / (x1 - x0)

    def xy(p):
        return (p[0] - x0) * k, legend_h + (p[1] - y0) * k

    d = Drawing(width, height + legend_h)
    d.add(Rect(0, legend_h, width, height, fillColor=colors.HexColor("#E4E9DA"), strokeColor=None))

    def area(pts, fill, stroke=None, sw=0.3):
        clipped = _clip_poly([tuple(p) for p in pts], x0, y0, x1, y1)
        if len(clipped) >= 3:
            d.add(Polygon([c for p in clipped for c in xy(p)], fillColor=colors.HexColor(fill),
                          strokeColor=colors.HexColor(stroke) if stroke else None, strokeWidth=sw))

    def line(pts, color, w, dash=None):
        for piece in _clip_line([tuple(p) for p in pts], x0, y0, x1, y1):
            d.add(PolyLine([c for p in piece for c in xy(p)], strokeColor=colors.HexColor(color), strokeWidth=w,
                           strokeLineCap=1, strokeLineJoin=1, strokeDashArray=dash))

    area(data["outline"], "#F5F1E8", "#C9C2B3", 0.5)
    for p in data["areas"]["green"]:
        area(p, "#D3E6C5")
    for p in data["areas"]["plaza"]:
        area(p, "#EFE9DC")
    for p in data["areas"]["water"]:
        area(p, "#B5DAF2", "#93C5E8", 0.3)
    for p in data["areas"]["building"]:
        area(p, "#DDD6CA")
    for p in data["attractions"]:
        area(p, "#F1D6A6", "#E2BC7E", 0.3)
    for p in data["paths"]:
        line(p, "#FFFFFF", max(1.0, 3.2 * k))

    # route: dotted line, green arrows every ~70 m
    accent = colors.HexColor(ROUTE_COLOR)
    if len(route) > 1:
        line(route, ROUTE_COLOR, 2.8, ROUTE_DOTS)
        walked = 0.0
        for p, q in zip(route, route[1:]):
            seg = math.dist(p, q)
            walked += seg
            if walked < 70 or seg < 6:
                continue
            walked = 0.0
            (px, py), (qx, qy) = xy(p), xy(q)
            length = math.hypot(qx - px, qy - py) or 1
            ux, uy = (qx - px) / length, (qy - py) / length
            mx, my = (px + qx) / 2, (py + qy) / 2
            d.add(Polygon([mx + ux * 5, my + uy * 5, mx - ux * 3.5 - uy * 3.6, my - uy * 3.5 + ux * 3.6,
                           mx - ux * 3.5 + uy * 3.6, my - uy * 3.5 - ux * 3.6], fillColor=colors.HexColor(ARROW_COLOR),
                          strokeColor=colors.white, strokeWidth=0.7, strokeLineJoin=1))
    ex, ey = xy(net.nodes[data["entrance"]])
    d.add(Rect(ex - 5, ey - 4, 10, 8, fillColor=colors.HexColor("#111827"), strokeColor=None))
    label = tr(lang, "legend_entrance")
    d.add(Rect(ex + 7, ey - 4, stringWidth(label, font, 6.4) + 4, 9, fillColor=colors.white, strokeColor=None))
    d.add(String(ex + 9, ey - 2, label, fontName=font, fontSize=6.4, fillColor=colors.HexColor("#111827")))

    # numbered pins, then labels placed where they don't cover another pin or label
    boxes = [(ex - 6, ey - 5, ex + 9 + stringWidth(label, font, 6.4) + 4, ey + 5)]
    pins = []
    for s in day["steps"]:
        if s.get("n") is None or s.get("x") is None or s.get("auto") or s["kind"] in ("break",):
            continue
        cx, cy = xy(net.nodes[net.node((s["x"], s["y"]))])
        while any(abs(cx - px) < 13 and abs(cy - py) < 13 for px, py, _ in pins):
            cy -= 14
        pins.append((cx, cy, s))
        boxes.append((cx - 7, cy - 7, cx + 7, cy + 7))

    def hits(box):
        return sum(1 for b in boxes if box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3])

    def free_spot(options):
        inside = [o for o in options if o[0] >= 1 and o[2] <= width - 1 and o[1] >= legend_h + 1 and o[3] <= legend_h + height - 1]
        return min(inside or options, key=hits)

    for cx, cy, s in pins:
        color = colors.HexColor(FIXED_COLOR if s.get("fixed") else FLEX_COLOR)
        label = short_name(s.get("short") or s.get("name") or "")
        if label:
            w = stringWidth(label, font, 6) + 4
            box = free_spot([(cx + 8, cy - 4.3, cx + 8 + w, cy + 4.3), (cx - 8 - w, cy - 4.3, cx - 8, cy + 4.3),
                             (cx - w / 2, cy + 8, cx + w / 2, cy + 16.6), (cx - w / 2, cy - 16.6, cx + w / 2, cy - 8),
                             (cx + 6, cy + 5, cx + 6 + w, cy + 13.6), (cx + 6, cy - 13.6, cx + 6 + w, cy - 5),
                             (cx - 6 - w, cy + 5, cx - 6, cy + 13.6), (cx - 6 - w, cy - 13.6, cx - 6, cy - 5)])
            boxes.append(box)
            d.add(Rect(box[0], box[1], w, 8.6, rx=2, ry=2, fillColor=colors.Color(1, 1, 1, alpha=0.9), strokeColor=None))
            d.add(String(box[0] + 2, box[1] + 2.2, label, fontName=font, fontSize=6, fillColor=colors.HexColor("#1F2937")))
        d.add(Circle(cx, cy, 6.5, fillColor=color, strokeColor=colors.white, strokeWidth=1.2))
        d.add(String(cx, cy - 2.6, str(s["n"]), fontName=font, fontSize=7, textAnchor="middle", fillColor=colors.white))

    # land names and the landmark, on top of the route but out of the way of pins and labels
    by_land = {}
    for a in park["attractions"]:
        if a["id"] in data["places"] and a.get("type") not in ("parade", "fireworks"):
            by_land.setdefault(a["land"], []).append(net.nodes[data["places"][a["id"]]])
    marks = [(short_land(land).upper(), (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)), 6.2, "#7C6F5B")
             for land, pts in by_land.items()]
    mark = park.get("landmark")
    if mark and data.get("landmark"):
        cx, cy = xy(data["landmark"])
        d.add(Polygon([cx, cy + 6, cx - 5, cy - 4, cx + 5, cy - 4], fillColor=colors.HexColor("#6B7280"), strokeColor=None))
        marks = [m for m in marks if m[0] != mark["name"].upper()]
        marks.insert(0, (mark["name"], data["landmark"], 6, "#374151"))
    for text, pt, size, ink in marks:
        cx, cy = xy(pt)
        w = stringWidth(text, font, size) + 4
        box = free_spot([(cx - w / 2 + dx, cy + dy, cx + w / 2 + dx, cy + dy + size + 2.4)
                         for dy in (-14, 8, -26, 20, -38, 32) for dx in (0, -w / 2, w / 2)])
        if hits(box) > 0:
            continue
        boxes.append(box)
        d.add(Rect(box[0], box[1], w, size + 2.4, rx=2, ry=2, fillColor=colors.Color(1, 1, 1, alpha=0.7), strokeColor=None))
        d.add(String(box[0] + 2, box[1] + 1.8, text, fontName=font, fontSize=size, fillColor=colors.HexColor(ink)))

    # scale bar and legend
    bar = 100 * k
    d.add(Line(width - 8 - bar, legend_h + 8, width - 8, legend_h + 8, strokeColor=colors.HexColor("#374151"), strokeWidth=1.2))
    d.add(String(width - 8 - bar / 2, legend_h + 11, "100 m", fontName=font, fontSize=6, textAnchor="middle",
                 fillColor=colors.HexColor("#374151")))
    d.add(Rect(0, legend_h, width, height, fillColor=None, strokeColor=colors.HexColor("#D4D4D4"), strokeWidth=0.6))
    y, x = 8, 4
    for color, key in ((FIXED_COLOR, "legend_fixed"), (FLEX_COLOR, "legend_flex")):
        d.add(Circle(x + 4, y + 2.5, 4, fillColor=colors.HexColor(color), strokeColor=None))
        d.add(String(x + 11, y, tr(lang, key), fontName=font, fontSize=7))
        x += 22 + len(tr(lang, key)) * 3.6
    d.add(Line(x, y + 2.5, x + 18, y + 2.5, strokeColor=accent, strokeWidth=2.8, strokeLineCap=1,
               strokeDashArray=ROUTE_DOTS))
    d.add(Polygon([x + 12, y + 2.5, x + 7, y + 5.5, x + 7, y - 0.5], fillColor=colors.HexColor(ARROW_COLOR), strokeColor=None))
    d.add(String(x + 22, y, tr(lang, "legend_route"), fontName=font, fontSize=7))
    d.add(String(width - 4, y, tr(lang, "osm_credit"), fontName=font, fontSize=6.5, textAnchor="end",
                 fillColor=colors.HexColor("#6B7280")))
    return d


def park_map(park, day, lang, font, width):
    net = P.walk_net(park)
    if net is not None:
        return _osm_map(park, day, lang, font, width, net)
    from reportlab.graphics.shapes import Circle, Drawing, Ellipse, Line, Polygon, PolyLine, Rect, String
    from reportlab.lib import colors

    height = width * 0.74
    legend_h, pad = 22, 8
    d = Drawing(width, height + legend_h)
    mw, mh = width - 2 * pad, height - 2 * pad

    def xy(x, y):
        return pad + x / 100 * mw, legend_h + pad + y / 100 * mh

    d.add(Rect(0, legend_h, width, height, rx=8, ry=8, fillColor=colors.HexColor("#F8FAF7"),
               strokeColor=colors.HexColor("#D4D4D4"), strokeWidth=0.6))
    for land in park["lands"]:
        x0, y0 = xy(land["x"], land["y"])
        x1, y1 = xy(land["x"] + land["w"], land["y"] + land["h"])
        d.add(Rect(x0, y0, x1 - x0, y1 - y0, rx=6, ry=6, fillColor=colors.HexColor(land.get("color", "#EEEEEE")),
                   strokeColor=colors.white, strokeWidth=1.5))
        d.add(String(x0 + 4, y1 - 9, short_land(land["name"]).upper(), fontName=font, fontSize=6,
                     fillColor=colors.HexColor("#374151")))
    for w in park.get("water", []):
        cx, cy = xy(w["x"], w["y"])
        d.add(Ellipse(cx, cy, w["rx"] / 100 * mw, w["ry"] / 100 * mh, fillColor=colors.HexColor("#BFDBFE"),
                      strokeColor=colors.HexColor("#93C5FD"), strokeWidth=0.5))
    mark = park.get("landmark")
    if mark:
        cx, cy = xy(mark["x"], mark["y"])
        d.add(Polygon([cx, cy + 6, cx - 5, cy - 4, cx + 5, cy - 4], fillColor=colors.HexColor("#6B7280"), strokeColor=None))
        d.add(String(cx, cy - 12, mark["name"], fontName=font, fontSize=5.5, textAnchor="middle",
                     fillColor=colors.HexColor("#4B5563")))
    visited = {s.get("id") for s in day["steps"]}
    for a in park["attractions"]:
        if a["id"] not in visited:
            cx, cy = xy(a["x"], a["y"])
            d.add(Circle(cx, cy, 1.6, fillColor=colors.HexColor("#9CA3AF"), strokeColor=None))

    # route
    pts = [s for s in day["steps"] if s.get("x") is not None and s["kind"] != "free"]
    route = []
    for s in pts:
        p = xy(s["x"], s["y"])
        if not route or (abs(route[-1][0] - p[0]) > 0.5 or abs(route[-1][1] - p[1]) > 0.5):
            route.append(p)
    accent = colors.HexColor(ROUTE_COLOR)
    if len(route) > 1:
        flat = [c for p in route for c in p]
        d.add(PolyLine(flat, strokeColor=accent, strokeWidth=1.4, strokeDashArray=[3, 2]))
        for (x0, y0), (x1, y1) in zip(route, route[1:]):
            length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            if length < 18:
                continue
            ux, uy = (x1 - x0) / length, (y1 - y0) / length
            mx, my = x0 + (x1 - x0) * 0.55, y0 + (y1 - y0) * 0.55
            d.add(Polygon([mx + ux * 4, my + uy * 4, mx - ux * 3 - uy * 3, my - uy * 3 + ux * 3,
                           mx - ux * 3 + uy * 3, my - uy * 3 - ux * 3], fillColor=accent, strokeColor=None))
    ex, ey = xy(*park["entrance"])
    d.add(Rect(ex - 5, ey - 4, 10, 8, fillColor=colors.HexColor("#111827"), strokeColor=None))
    d.add(String(ex + 8, ey - 2.5, tr(lang, "legend_entrance"), fontName=font, fontSize=6, fillColor=colors.HexColor("#111827")))

    # numbered pins (offset when two stops share a spot)
    placed = []
    for s in day["steps"]:
        if s.get("n") is None or s.get("x") is None or s.get("auto") or s["kind"] in ("break",):
            continue
        cx, cy = xy(s["x"], s["y"])
        while any(abs(cx - px) < 9 and abs(cy - py) < 9 for px, py in placed):
            cx, cy = cx + 9, cy + 5
        placed.append((cx, cy))
        color = colors.HexColor(FIXED_COLOR if s.get("fixed") else FLEX_COLOR)
        d.add(Circle(cx, cy, 6.5, fillColor=color, strokeColor=colors.white, strokeWidth=1))
        d.add(String(cx, cy - 2.6, str(s["n"]), fontName=font, fontSize=7, textAnchor="middle", fillColor=colors.white))
        label = short_name(s.get("short") or s.get("name") or "")
        if label:
            d.add(String(cx + 8.5, cy - 2.2, label, fontName=font, fontSize=5.6, fillColor=colors.HexColor("#1F2937")))

    # legend
    y = 8
    x = 4
    for color, key in ((FIXED_COLOR, "legend_fixed"), (FLEX_COLOR, "legend_flex")):
        d.add(Circle(x + 4, y + 2.5, 4, fillColor=colors.HexColor(color), strokeColor=None))
        d.add(String(x + 11, y, tr(lang, key), fontName=font, fontSize=7))
        x += 22 + len(tr(lang, key)) * 3.6
    d.add(Line(x, y + 2.5, x + 18, y + 2.5, strokeColor=accent, strokeWidth=1.4, strokeDashArray=[3, 2]))
    d.add(String(x + 22, y, tr(lang, "legend_route"), fontName=font, fontSize=7))
    d.add(String(width - 4, y, tr(lang, "schematic"), fontName=font, fontSize=6.5, textAnchor="end",
                 fillColor=colors.HexColor("#6B7280")))
    return d


# --- text helpers ----------------------------------------------------------------

def step_label(s, lang):
    kind = s["kind"]
    if kind == "arrive":
        return tr(lang, "arrive_early" if s.get("early_entry") else "arrive_step")
    if kind == "leave":
        return tr(lang, "transfer_step" if s.get("transfer") else "leave_step")
    if kind == "free":
        return tr(lang, "free_repeat" if s.get("repeat") else "free")
    if kind == "meal" and s.get("auto"):
        return tr(lang, s.get("meal", "lunch"))
    if kind == "rest":
        return tr(lang, "rest")
    if kind == "break":
        return s.get("name") or tr(lang, "break")
    return s.get("name") or ""


def lane_label(s, operator, lang):
    lane = s.get("lane")
    if not lane:
        return ""
    if lane == "standby_das" and operator == "universal":
        lane = "standby_aap"
    return tr(lang, f"lane_{lane}") if f"lane_{lane}" in L else lane


def why_fixed(s, lang):
    if s.get("lane", "").startswith("ll_"):
        if s.get("suggested"):
            return tr(lang, "why_ll_suggested", a=s["window"][0])
        return tr(lang, "why_ll", a=s["window"][0], b=s["window"][1])
    if s["kind"] == "break":
        return tr(lang, "why_break", a=s["end"])
    if s["kind"] in ("show", "parade", "fireworks") or s.get("type") in ("show", "parade", "fireworks"):
        return tr(lang, "why_show", a=s.get("show_time") or s["start"])
    return s.get("note") or tr(lang, "why_meal")


def step_notes(s, day, lang, plan):
    notes = []
    custom = (day.get("notes") or {}).get(s.get("id") or "")
    if custom:
        notes.append(custom)
    elif lang == "en" and s.get("note") and s["kind"] not in ("meal",):
        notes.append(s["note"])
    out = [o for o in s.get("out", []) if o.get("name") != "*"]
    if out:
        names = join_names([o["name"] for o in out], lang)
        if s.get("switch"):
            notes.append(tr(lang, "switch_u" if day["operator"] == "universal" else "switch", who=names,
                            verb=verb("v_wait", len(out), lang)))
        else:
            notes.append(tr(lang, "sits_out", who=names, verb=verb("v_skip", len(out), lang)))
    return " · ".join(notes)


def excluded_text(e, lang):
    if e["reason"] == "closed":
        return tr(lang, "r_closed")
    parts = []
    for o in e.get("who", []):
        reason = o["reason"]
        detail = o.get("detail", "")
        if reason == "tags":
            detail = ", ".join(pick(TAG, t.strip(), lang) for t in detail.split(","))
        key = f"r_{reason}"
        if key in L:
            parts.append(tr(lang, key, who=o["name"], detail=detail))
    return "; ".join(parts)


# --- document --------------------------------------------------------------------

def render(plan, out_path, footer=None, color="0F766E"):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (CondPageBreak, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)

    lang = plan.get("lang", "en") if plan.get("lang") in ("en", "es") else "en"
    font = _pdf_font()
    accent = colors.HexColor("#" + color.lstrip("#"))
    base = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=base["BodyText"], fontName=font, fontSize=9.5, leading=12.5)
    small = ParagraphStyle("s", parent=body, fontSize=8.2, leading=10.4)
    th = ParagraphStyle("th", parent=small, textColor=colors.white)
    h0 = ParagraphStyle("h0", parent=body, fontSize=22, leading=26, textColor=accent, spaceAfter=4)
    h1 = ParagraphStyle("h1", parent=body, fontSize=15, leading=19, textColor=accent, spaceBefore=4, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=body, fontSize=11.5, leading=15, textColor=accent, spaceBefore=8, spaceAfter=4)
    muted = ParagraphStyle("m", parent=body, textColor=colors.HexColor("#4B5563"))
    usable = A4[0] - 3.6 * cm
    parks = P.load_parks()

    def para(text, style=body):
        return Paragraph(escape(str(text if text is not None else "")), style)

    def table(header, rows, widths, highlight=None):
        data = [[para(h, th) for h in header]] + [[para(c, small) for c in r] for r in rows]
        t = Table(data, colWidths=[usable * w for w in widths], repeatRows=1, hAlign="LEFT")
        style = [("BACKGROUND", (0, 0), (-1, 0), accent), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                 ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
        for i in highlight or []:
            style.append(("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#FFEDD5")))
        t.setStyle(TableStyle(style))
        return t

    story = [para(tr(lang, "title"), h0)]
    if plan.get("client"):
        story.append(para(tr(lang, "for", client=plan["client"]), muted))
    story.append(Spacer(1, 8))

    story.append(para(tr(lang, "party"), h2))
    rows = []
    for p in plan["party"]:
        notes = [pick(FLAG, f, lang) for f in p.get("flags", [])]
        if p.get("note"):
            notes.append(p["note"])
        rows.append([p["name"], p.get("age", "") if p.get("age") not in (None, "") else "—", height_text(p), ", ".join(notes)])
    story.append(table([tr(lang, k) for k in ("name", "age", "height", "notes")], rows, [0.28, 0.1, 0.22, 0.4]))

    story.append(para(tr(lang, "overview"), h2))
    rows = []
    for i, d in zip(day_numbers(plan), plan["days"]):
        must = [s.get("short") or s["name"] for s in d["steps"]
                if s.get("level") == "must" or (s.get("lane", "").startswith("ll_"))]
        rows.append([str(i), day_text(d.get("date"), lang), d["park_name"], f'{d["open"]}–{d["close"]}', d["arrive"],
                     ", ".join(short_name(m, 30) for m in must[:6]) or "—"])
    story.append(table([tr(lang, k) for k in ("day", "date", "park", "hours", "arrive", "highlights")], rows,
                       [0.07, 0.16, 0.22, 0.13, 0.1, 0.32]))

    if plan.get("bookings"):
        story.append(para(tr(lang, "bookings"), h2))
        rows = []
        for b in plan["bookings"]:
            when = (tr(lang, "open_now") if b.get("open_now") else day_text(b["date"], lang)) if b.get("date") else tr(lang, "asap")
            rows.append([when, b.get("time") or "—", tr(lang, "b_" + b["what"], park=b.get("park", ""))])
        story.append(table([tr(lang, "date"), tr(lang, "time_et"), tr(lang, "what")], rows, [0.2, 0.14, 0.66]))

    story.append(para(tr(lang, "how"), h2))
    tips = [tr(lang, "how1"), tr(lang, "how2"), tr(lang, "how3")]
    if any(s.get("switch") for d in plan["days"] for s in d["steps"]):
        tips.append(tr(lang, "how_switch"))
    tips += [n for n in plan.get("notes", []) if n]
    for tip in tips:
        story.append(Paragraph("• " + escape(tip), body))

    for i, d in zip(day_numbers(plan), plan["days"]):
        park = parks[d["park"]]
        story.append(PageBreak())
        story.append(para(f'{tr(lang, "day")} {i} · {day_text(d.get("date"), lang)} · {d["park_name"]}', h1))
        story.append(para(f'{tr(lang, "hours")}: {d["open"]}–{d["close"]} · {tr(lang, "arrive")}: {d["arrive"]}', muted))
        story.append(Spacer(1, 4))
        story.append(park_map(park, d, lang, font, usable))

        fixed = [s for s in d["steps"] if s.get("fixed")]
        block = [para(tr(lang, "fixed"), h2)]
        if fixed:
            rows = [[s["start"] if not s.get("lane", "").startswith("ll_") else s["window"][0],
                     f'{s["n"]}. {step_label(s, lang)}', why_fixed(s, lang)] for s in fixed]
            block.append(table([tr(lang, "time"), tr(lang, "stop"), tr(lang, "why")], rows, [0.12, 0.42, 0.46],
                               highlight=range(len(rows))))
        else:
            block.append(para(tr(lang, "fixed_none"), muted))
        story.append(KeepTogether(block))

        story.append(CondPageBreak(4 * cm))
        story.append(para(tr(lang, "schedule"), h2))
        rows, hl = [], []
        for s in d["steps"]:
            if s["kind"] in ("arrive", "leave") or (s["kind"] == "free" and not s.get("repeat")):
                rows.append(["", s["start"], step_label(s, lang), "", "", "", ""])
                continue
            wait = s.get("wait")
            rows.append([str(s.get("n", "")), s["start"], step_label(s, lang),
                         short_land(s.get("land", "")) if s.get("land") else "",
                         lane_label(s, d["operator"], lang), duration(wait, lang) if wait else "",
                         step_notes(s, d, lang, plan)])
            if s.get("fixed"):
                hl.append(len(rows) - 1)
        story.append(table(["#", tr(lang, "time"), tr(lang, "stop"), tr(lang, "area"), tr(lang, "line"),
                            tr(lang, "wait"), tr(lang, "notes")], rows, [0.05, 0.08, 0.27, 0.15, 0.12, 0.09, 0.24],
                           highlight=hl))
        tot = d["totals"]
        key = "totals" if tot["saved_min"] >= 20 else "totals_plain"
        story.append(Spacer(1, 4))
        story.append(para(tr(lang, key, wait=duration(tot["wait_min"], lang), saved=duration(tot["saved_min"], lang)), muted))

        skipped = [e for e in d.get("excluded", []) if excluded_text(e, lang)]
        if skipped:
            story.append(para(tr(lang, "skipped"), h2))
            for e in skipped:
                story.append(Paragraph(f"• <b>{escape(e['name'])}</b>: {escape(excluded_text(e, lang))}", small))
        day_tips = d.get("tips") or (park.get("tips", []) if lang == "en" else [])
        if day_tips:
            story.append(para(tr(lang, "tips"), h2))
            for tip in day_tips:
                story.append(Paragraph("• " + escape(tip), small))

    def decorate(canvas, doc):
        canvas.setFont(font, 7.5)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        if footer:
            canvas.drawString(1.8 * cm, 1.1 * cm, footer)
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, str(doc.page))

    SimpleDocTemplate(out_path, pagesize=A4, title=tr(lang, "title"), leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                      topMargin=1.6 * cm, bottomMargin=1.8 * cm).build(story, onFirstPage=decorate, onLaterPages=decorate)
    return out_path
