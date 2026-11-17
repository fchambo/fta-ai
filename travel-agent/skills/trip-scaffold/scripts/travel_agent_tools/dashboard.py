"""The agent's dashboard: next important dates and pending tasks for every client and for the agent.

`collect()` gathers the items from the Trip Sheets, the My Tasks workbook and (optionally) the
Providers & Commissions workbook. `render()` writes one self-contained HTML file (no internet needed)
that filters, groups and counts down in the browser, so it stays right for a few days after it's built.
"""
import hashlib
import json
import os
from datetime import date

from . import logic, schema, workbooks
from .workbooks import parse_date

LABELS = {
    "en": {
        "title": "Dashboard", "updated": "Data from", "stale": "This data is {n} days old. Ask the assistant to rebuild the dashboard.",
        "overdue": "Overdue", "today": "Today", "week": "Next 7 days", "soon": "8–14 days", "later": "Later", "nodate": "No date",
        "k_overdue": "Overdue", "k_week": "Due in 7 days", "k_trips": "Trips in 30 days", "k_owed": "Clients owe",
        "k_comm": "Commissions to collect", "k_tasks": "My open tasks",
        "all": "Everything", "me": "My tasks", "client": "Client to-dos", "info": "Key dates",
        "all_clients": "All clients", "no_client": "Me (no client)", "range": "Show", "r7": "Next 7 days", "r14": "Next 14 days",
        "r30": "Next 30 days", "r90": "Next 90 days", "rall": "Everything", "search": "Search…",
        "hide_amounts": "Hide amounts", "show_done": "Show done", "agenda": "Agenda", "clients": "Clients",
        "empty": "Nothing here. Enjoy the calm.", "in_days": "in {n} d", "days_ago": "{n} d ago", "today_short": "today",
        "departs": "Departs", "traveling": "Traveling now", "back": "Back", "next": "Next", "balance": "Balance due",
        "nothing_pending": "Nothing pending", "mark_done": "Mark as done here", "copy": "Copy done items for the assistant",
        "copied": "Copied. Paste it to the assistant so it updates your Excel files.",
        "copy_header": "Please mark these as done in my files:", "done_note": "Ticks are saved in this browser only. Your Excel files change when the assistant updates them.",
        "checks": "To fix in the Trip Sheet", "clear": "Clear filter",
        "who_me": "Me", "who_client": "Client", "who_info": "Date",
        "kind": {"travel": "Trip", "booking": "Booking", "payment_in": "Client payment", "payment_out": "Pay provider",
                 "cancellation": "Free cancellation", "deadline": "Deadline", "commission": "Commission",
                 "task": "Task", "check": "Check"},
        "status": {"inquiry": "Inquiry", "quoting": "Quoting", "booked": "Booked", "paid": "Paid",
                   "traveling": "Traveling", "closed": "Closed", "cancelled": "Cancelled"},
        "priority": {"high": "High", "normal": "", "low": "Low"},
    },
    "es": {
        "title": "Tablero", "updated": "Datos del", "stale": "Estos datos tienen {n} días. Pedile al asistente que actualice el tablero.",
        "overdue": "Vencido", "today": "Hoy", "week": "Próximos 7 días", "soon": "8 a 14 días", "later": "Más adelante", "nodate": "Sin fecha",
        "k_overdue": "Vencidos", "k_week": "Vencen en 7 días", "k_trips": "Viajes en 30 días", "k_owed": "Te deben los clientes",
        "k_comm": "Comisiones a cobrar", "k_tasks": "Mis tareas abiertas",
        "all": "Todo", "me": "Mis tareas", "client": "Pendientes del cliente", "info": "Fechas clave",
        "all_clients": "Todos los clientes", "no_client": "Yo (sin cliente)", "range": "Mostrar", "r7": "Próximos 7 días",
        "r14": "Próximos 14 días", "r30": "Próximos 30 días", "r90": "Próximos 90 días", "rall": "Todo", "search": "Buscar…",
        "hide_amounts": "Ocultar montos", "show_done": "Ver hechos", "agenda": "Agenda", "clients": "Clientes",
        "empty": "Nada por acá. Disfrutá la calma.", "in_days": "en {n} d", "days_ago": "hace {n} d", "today_short": "hoy",
        "departs": "Sale", "traveling": "Viajando ahora", "back": "Vuelve", "next": "Próximo", "balance": "Saldo a cobrar",
        "nothing_pending": "Nada pendiente", "mark_done": "Marcar como hecho acá", "copy": "Copiar hechos para el asistente",
        "copied": "Copiado. Pegáselo al asistente para que actualice tus Excel.",
        "copy_header": "Marcá esto como hecho en mis archivos:", "done_note": "Las tildes se guardan solo en este navegador. Tus Excel cambian cuando el asistente los actualiza.",
        "checks": "A corregir en la Ficha del Viaje", "clear": "Quitar filtro",
        "who_me": "Yo", "who_client": "Cliente", "who_info": "Fecha",
        "kind": {"travel": "Viaje", "booking": "Reserva", "payment_in": "Pago del cliente", "payment_out": "Pagar al proveedor",
                 "cancellation": "Cancelación sin cargo", "deadline": "Vencimiento", "commission": "Comisión",
                 "task": "Tarea", "check": "Revisar"},
        "status": {"inquiry": "Consulta", "quoting": "Cotizando", "booked": "Reservado", "paid": "Pagado",
                   "traveling": "Viajando", "closed": "Cerrado", "cancelled": "Cancelado"},
        "priority": {"high": "Alta", "normal": "", "low": "Baja"},
    },
}

INACTIVE = ("closed", "cancelled")


def _id(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]


def _item(source, kind, who, title, when=None, client=None, trip=None, **extra):
    when = parse_date(when)
    return {"id": _id(source, kind, when, title, client), "date": when.isoformat() if when else None,
            "kind": kind, "who": who, "title": title, "client": client, "trip": trip, **extra}


def classify(paths):
    """Sort .xlsx paths into Trip Sheets, My Tasks and Providers workbooks; folders are searched."""
    found = {"trips": [], "tasks": [], "providers": []}
    files = []
    for path in paths:
        if os.path.isdir(path):
            for folder, dirs, names in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                files += [os.path.join(folder, n) for n in sorted(names) if n.endswith(".xlsx") and not n.startswith("~$")]
        else:
            files.append(path)
    for path in files:
        for key, layout in (("trips", schema.TRIP_WORKBOOK), ("tasks", schema.TASKS_WORKBOOK),
                            ("providers", schema.PROVIDERS_WORKBOOK)):
            if workbooks.is_layout(path, layout):
                found[key].append(os.path.abspath(path))
                break
    return found


def _trip_items(trip, path, today):
    info = trip.get("trip") or {}
    client, lang = info.get("client_name") or "?", trip.get("_lang", "en")
    ref = info.get("trip_id") or os.path.basename(path)
    trip_label = " · ".join(str(x) for x in (info.get("destinations"), info.get("start_date")) if x)
    src = os.path.basename(path)
    tl = logic.timeline(trip, today)
    items = []
    for e in tl["events"]:
        if e["status"] == "done":
            continue
        if e["kind"] == "travel":
            kind, who = "travel", "info"
        elif e["kind"] == "booking":
            kind, who = "booking", "info"
        elif e["kind"] == "payment":
            kind, who = ("payment_in", "client") if e.get("payer") == "client" else ("payment_out", "me")
        elif e["label"].startswith(("Free cancellation", "Fin de cancelación")):
            kind, who = "cancellation", "me"
        else:
            kind, who = "deadline", "me"
        title = e["label"]
        if e["kind"] == "payment":
            title = e.get("description") or title
            if kind == "payment_out" and e.get("payee"):
                title = f"{title} → {e['payee']}"
        items.append(_item(src, kind, who, title, e["date"], client, trip_label,
                           amount=e.get("amount"), currency=e.get("currency")))
    for check in tl["checks"]:
        items.append(_item(src, "check", "me", check, None, client, trip_label))

    owed = {}
    for p in trip.get("payments") or []:
        if (p.get("payer") or "client") == "client" and not p.get("paid_date") and p.get("amount") not in (None, ""):
            cur = p.get("currency") or "USD"
            owed[cur] = round(owed.get(cur, 0) + float(p["amount"]), 2)
    card = {"client": client, "trip": ref, "destinations": info.get("destinations"), "status": info.get("status"),
            "start": info.get("start_date"), "end": info.get("end_date"), "travelers": len(trip.get("travelers") or []),
            "owed": owed, "file": src, "lang": lang}
    return items, card


def _task_items(tasks_wb, path):
    items, src = [], os.path.basename(path)
    for t in tasks_wb.get("tasks") or []:
        if not t.get("task") or t.get("done") == "yes":
            continue
        items.append(_item(src, "task", "me", t["task"], t.get("due"), t.get("client") or None, None,
                           priority=t.get("priority") or "normal", notes=t.get("notes")))
    return items


def _commission_items(cfg, trips, today):
    result = logic.commissions(cfg, trips, today)
    items = []
    for r in result["bookings"]:
        if r["status"] not in ("pending", "overdue") or not r["commission"]:
            continue
        title = f"{r['provider']} · {r['booking']}" + (f" · {r['product']}" if r.get("product") else "")
        items.append(_item("commissions", "commission", "me", title, r.get("expected_date"), r["client"], r.get("trip"),
                           amount=round(r["commission"] - r["withholding"], 2), currency=r.get("currency")))
    return items, cfg.get("settings") or {}


def collect(paths, today=None, lang=None):
    today = today or date.today()
    found = classify(paths)
    items, cards, langs, warnings = [], [], [], []
    trips_all = []
    for path in found["trips"]:
        try:
            trip = workbooks.read(path, schema.TRIP_WORKBOOK)
        except Exception as e:  # one broken file must not hide the rest
            warnings.append(f"{os.path.basename(path)}: {e}")
            continue
        trips_all.append(trip)
        langs.append(trip.get("_lang", "en"))
        if (trip.get("trip") or {}).get("status") in INACTIVE:
            continue
        trip_items, card = _trip_items(trip, path, today)
        items += trip_items
        cards.append(card)
    for path in found["tasks"]:
        wb = workbooks.read(path, schema.TASKS_WORKBOOK)
        langs.append(wb.get("_lang", "en"))
        items += _task_items(wb, path)
    settings = {}
    if found["providers"]:
        cfg = workbooks.read(found["providers"][0], schema.PROVIDERS_WORKBOOK)
        langs.append(cfg.get("_lang", "en"))
        comm, settings = _commission_items(cfg, trips_all, today)
        items += comm
    lang = lang or (max(set(langs), key=langs.count) if langs else "en")
    items.sort(key=lambda i: (i["date"] is None, i["date"] or "", i["client"] or ""))
    cards.sort(key=lambda c: (c["start"] is None, c["start"] or "", c["client"]))
    return {"today": today.isoformat(), "lang": lang if lang in schema.LANGS else "en",
            "agency": settings.get("agency_name") or "", "palette": settings.get("brand_colors") or "",
            "items": items, "clients": cards, "sources": found, "warnings": warnings}


def summary(data):
    """Short JSON for the assistant: counts plus what needs attention first."""
    today = date.fromisoformat(data["today"])
    dated = [i for i in data["items"] if i["date"]]
    overdue = [i for i in dated if date.fromisoformat(i["date"]) < today and i["who"] != "info"]
    week = [i for i in dated if 0 <= (date.fromisoformat(i["date"]) - today).days <= 7]
    return {"clients": len(data["clients"]), "items": len(data["items"]), "overdue": len(overdue), "next_7_days": len(week),
            "checks": sum(1 for i in data["items"] if i["kind"] == "check"),
            "attention": [{k: i.get(k) for k in ("date", "who", "kind", "client", "title", "amount", "currency")}
                          for i in overdue + [w for w in week if w not in overdue]][:20]}


def _accent(palette):
    first = str(palette or "").replace(" ", "").split(",")[0].lstrip("#")
    return "#" + first if len(first) == 6 and all(c in "0123456789abcdefABCDEF" for c in first) else "#0F766E"


def render(data, out_path):
    lang = data["lang"]
    payload = {**data, "labels": LABELS[lang], "sources": None}
    blob = json.dumps(payload, ensure_ascii=False, default=str).replace("</", "<\\/")
    title = LABELS[lang]["title"] + (f" · {data['agency']}" if data["agency"] else "")
    html = (TEMPLATE.replace("__LANG__", lang).replace("__TITLE__", _esc(title))
            .replace("__ACCENT__", _accent(data["palette"])).replace("__DATA__", blob))
    workbooks.ensure_closed(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


TEMPLATE = r"""<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--accent:__ACCENT__;--bg:#f6f7f9;--card:#fff;--ink:#16181d;--muted:#5f6672;--line:#e3e6eb;
--red:#c62828;--red-bg:#fdecec;--amber:#a15c00;--amber-bg:#fff4e0;--blue:#1d5fbf;--blue-bg:#e8f0fd;--green:#2e7d32;--green-bg:#e8f5e9;--chip:#eef0f3}
@media (prefers-color-scheme:dark){:root{--bg:#111316;--card:#1a1d22;--ink:#eceef1;--muted:#a0a7b2;--line:#2c3038;
--red:#ff8a80;--red-bg:#3a1d1d;--amber:#ffc266;--amber-bg:#3a2c12;--blue:#8db8ff;--blue-bg:#1b2a42;--green:#8bd48f;--green-bg:#1b3320;--chip:#262a31}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{background:var(--card);border-bottom:1px solid var(--line);border-top:4px solid var(--accent);padding:16px}
.wrap{max-width:1200px;margin:0 auto}
h1{font-size:22px;margin:0}
.sub{color:var(--muted);font-size:13px;margin-top:2px}
.stale{background:var(--amber-bg);color:var(--amber);padding:8px 12px;border-radius:8px;margin-top:10px;font-size:14px}
main{padding:16px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:16px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;cursor:pointer;text-align:left;color:inherit;font:inherit}
.kpi:hover{border-color:var(--accent)}
.kpi .n{font-size:24px;font-weight:700;font-variant-numeric:tabular-nums}
.kpi .l{color:var(--muted);font-size:13px}
.kpi.red .n{color:var(--red)} .kpi.amber .n{color:var(--amber)}
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:14px}
.seg{display:flex;background:var(--chip);border-radius:10px;padding:3px;flex-wrap:wrap}
.seg button{border:0;background:transparent;color:var(--ink);padding:6px 10px;border-radius:8px;font:inherit;font-size:14px;cursor:pointer}
.seg button.on{background:var(--card);box-shadow:0 1px 2px rgba(0,0,0,.15);font-weight:600}
select,input[type=search]{font:inherit;font-size:14px;padding:7px 10px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);max-width:100%}
input[type=search]{flex:1;min-width:140px}
label.tog{font-size:14px;color:var(--muted);display:flex;gap:5px;align-items:center;cursor:pointer}
.grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:16px}
@media (max-width:860px){.grid{grid-template-columns:1fr}}
h2{font-size:16px;margin:0 0 8px}
.group{margin-bottom:14px}
.group h3{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 6px;display:flex;gap:6px;align-items:center}
.group.overdue h3{color:var(--red)}
.count{background:var(--chip);color:var(--muted);border-radius:10px;padding:0 7px;font-size:12px}
.item{display:grid;grid-template-columns:auto 76px minmax(0,1fr) auto;gap:10px;align-items:start;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 12px;margin-bottom:6px}
.item.done{opacity:.5}.item.done .t{text-decoration:line-through}
.item input{margin-top:3px;width:17px;height:17px;accent-color:var(--accent)}
.d{font-size:13px;font-variant-numeric:tabular-nums}
.d .rel{display:block;color:var(--muted);font-size:12px}
.d .rel.red{color:var(--red);font-weight:600}.d .rel.amber{color:var(--amber);font-weight:600}
.t{font-weight:500;overflow-wrap:anywhere}
.meta{color:var(--muted);font-size:13px;margin-top:2px;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center}
.meta a{color:inherit;cursor:pointer;text-decoration:underline dotted}
.pill{font-size:11px;font-weight:600;border-radius:999px;padding:1px 8px;white-space:nowrap}
.p-me{background:var(--blue-bg);color:var(--blue)}.p-client{background:var(--amber-bg);color:var(--amber)}.p-info{background:var(--chip);color:var(--muted)}
.p-high{background:var(--red-bg);color:var(--red)}
.amt{font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap;text-align:right}
.hide .amt,.hide .money{filter:blur(6px)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:10px;cursor:pointer}
.card:hover,.card.sel{border-color:var(--accent)}
.card .top{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.card .name{font-weight:700;overflow-wrap:anywhere}
.card .dest{color:var(--muted);font-size:13px}
.cd{font-size:13px;margin-top:6px}
.cd b{font-variant-numeric:tabular-nums}
.card ul{margin:8px 0 0;padding:0;list-style:none;font-size:13px}
.card li{display:flex;gap:8px;padding:3px 0;border-top:1px dashed var(--line)}
.card li span:first-child{color:var(--muted);min-width:70px;font-variant-numeric:tabular-nums}
.card li.red span:first-child{color:var(--red);font-weight:600}
.empty{color:var(--muted);padding:20px;text-align:center;background:var(--card);border:1px dashed var(--line);border-radius:10px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:8px;font-size:13px;color:var(--muted)}
.btn{font:inherit;font-size:14px;padding:7px 12px;border-radius:10px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--line)}
.btn[disabled]{opacity:.5;cursor:default}
@media (max-width:520px){.kpi .n{font-size:19px;overflow-wrap:anywhere}.item{grid-template-columns:auto 62px minmax(0,1fr)}.item .amt{grid-column:3;text-align:left}}
</style>
</head>
<body>
<header><div class="wrap"><h1 id="title"></h1><div class="sub" id="sub"></div><div id="stale"></div></div></header>
<main class="wrap">
  <section class="kpis" id="kpis"></section>
  <section class="controls">
    <div class="seg" id="who"></div>
    <select id="client" aria-label="client"></select>
    <select id="range" aria-label="range"></select>
    <input type="search" id="q">
    <label class="tog"><input type="checkbox" id="hide"> <span id="hideL"></span></label>
    <label class="tog"><input type="checkbox" id="showdone"> <span id="doneL"></span></label>
  </section>
  <div class="grid">
    <section><h2 id="agendaH"></h2><div id="agenda"></div>
      <div class="bar"><button class="btn" id="copy" disabled></button><span id="copyMsg"></span></div>
      <div class="bar" id="doneNote"></div></section>
    <aside><h2 id="clientsH"></h2><div id="cards"></div></aside>
  </div>
</main>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
const D=JSON.parse(document.getElementById('data').textContent), L=D.labels, lang=D.lang;
const loc=lang==='es'?'es-AR':'en-US';
const $=id=>document.getElementById(id);
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e;};
const store={get(k,d){try{const v=localStorage.getItem('ta-dash-'+k);return v==null?d:JSON.parse(v);}catch(e){return d;}},
  set(k,v){try{localStorage.setItem('ta-dash-'+k,JSON.stringify(v));}catch(e){}}};
const now=new Date(), todayUTC=Date.UTC(now.getFullYear(),now.getMonth(),now.getDate());
const days=iso=>{if(!iso)return null;const [y,m,d]=iso.split('-').map(Number);return Math.round((Date.UTC(y,m-1,d)-todayUTC)/864e5);};
const fmtDate=iso=>{const [y,m,d]=iso.split('-').map(Number);return new Intl.DateTimeFormat(loc,{weekday:'short',day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(Date.UTC(y,m-1,d)));};
const money=(a,c)=>{try{return new Intl.NumberFormat(loc,{style:'currency',currency:c||'USD',maximumFractionDigits:2}).format(a);}catch(e){return (c||'')+' '+a;}};
const rel=n=>n===0?L.today_short:n>0?L.in_days.replace('{n}',n):L.days_ago.replace('{n}',-n);
const bucket=n=>n==null?'nodate':n<0?'overdue':n===0?'today':n<=7?'week':n<=14?'soon':'later';
let done=store.get('done',{});
const state={who:store.get('who','all'),client:'',range:store.get('range','30'),q:'',hide:store.get('hide',false),showdone:false};

$('title').textContent=L.title+(D.agency?' · '+D.agency:'');
document.title=$('title').textContent;
$('sub').textContent=L.updated+' '+fmtDate(D.today);
const age=-days(D.today);
if(age>=2){$('stale').appendChild(el('div','stale',L.stale.replace('{n}',age)));}
$('agendaH').textContent=L.agenda;$('clientsH').textContent=L.clients;
$('hideL').textContent=L.hide_amounts;$('doneL').textContent=L.show_done;
$('q').placeholder=L.search;$('copy').textContent=L.copy;$('doneNote').textContent=L.done_note;

[['all',L.all],['me',L.me],['client',L.client],['info',L.info]].forEach(([k,t])=>{
  const b=el('button',null,t);b.dataset.k=k;b.onclick=()=>{state.who=k;store.set('who',k);draw();};$('who').appendChild(b);});
const names=[...new Set(D.items.map(i=>i.client).filter(Boolean).concat(D.clients.map(c=>c.client)))].sort((a,b)=>a.localeCompare(b,loc));
[['',L.all_clients],['__none',L.no_client]].concat(names.map(n=>[n,n])).forEach(([v,t])=>{const o=el('option',null,t);o.value=v;$('client').appendChild(o);});
[['7',L.r7],['14',L.r14],['30',L.r30],['90',L.r90],['all',L.rall]].forEach(([v,t])=>{const o=el('option',null,t);o.value=v;$('range').appendChild(o);});
$('client').onchange=e=>{state.client=e.target.value;draw();};
$('range').value=state.range;$('range').onchange=e=>{state.range=e.target.value;store.set('range',state.range);draw();};
$('q').oninput=e=>{state.q=e.target.value.toLowerCase();draw();};
$('hide').checked=state.hide;$('hide').onchange=e=>{state.hide=e.target.checked;store.set('hide',state.hide);draw();};
$('showdone').onchange=e=>{state.showdone=e.target.checked;draw();};
$('copy').onclick=()=>{
  const lines=D.items.filter(i=>done[i.id]).map(i=>'- '+(i.date?i.date+' · ':'')+(i.client?i.client+' · ':'')+L.kind[i.kind]+': '+i.title);
  const text=L.copy_header+'\n'+lines.join('\n');
  const ok=()=>{$('copyMsg').textContent=L.copied;};
  if(navigator.clipboard){navigator.clipboard.writeText(text).then(ok,()=>prompt('',text));}else{prompt('',text);}
};

function visible(i){
  if(state.who!=='all'&&i.who!==state.who)return false;
  if(state.client==='__none'&&i.client)return false;
  if(state.client&&state.client!=='__none'&&i.client!==state.client)return false;
  if(!state.showdone&&done[i.id])return false;
  const n=days(i.date);
  if(state.range!=='all'&&n!=null&&n>Number(state.range))return false;
  if(n!=null&&n<0&&i.who==='info')return false;
  if(state.q){const h=[i.title,i.client,i.trip,L.kind[i.kind],i.notes].join(' ').toLowerCase();if(!h.includes(state.q))return false;}
  return true;
}

function kpis(){
  const open=D.items.filter(i=>!done[i.id]);
  const overdue=open.filter(i=>i.who!=='info'&&days(i.date)!=null&&days(i.date)<0).length;
  const week=open.filter(i=>{const n=days(i.date);return n!=null&&n>=0&&n<=7&&i.who!=='info';}).length;
  const trips=D.clients.filter(c=>{const n=days(c.start);return n!=null&&n>=0&&n<=30;}).length;
  const owed={},comm={};
  D.clients.forEach(c=>Object.entries(c.owed||{}).forEach(([k,v])=>owed[k]=(owed[k]||0)+v));
  open.filter(i=>i.kind==='commission').forEach(i=>comm[i.currency||'USD']=(comm[i.currency||'USD']||0)+(i.amount||0));
  const sum=o=>Object.keys(o).length?Object.entries(o).map(([k,v])=>money(v,k)).join(' · '):'—';
  const tasks=open.filter(i=>i.kind==='task').length;
  const box=$('kpis');box.textContent='';
  [[overdue,L.k_overdue,overdue?'red':'',()=>{state.range='all';state.who='all';}],
   [week,L.k_week,week?'amber':'',()=>{state.range='7';state.who='all';}],
   [trips,L.k_trips,'',()=>{state.range='30';state.who='info';}],
   [sum(owed),L.k_owed,'money',()=>{state.who='client';state.range='all';}],
   [sum(comm),L.k_comm,'money',()=>{state.who='me';state.range='all';state.q=L.kind.commission.toLowerCase();$('q').value=state.q;}],
   [tasks,L.k_tasks,'',()=>{state.who='me';state.range='all';state.q=L.kind.task.toLowerCase();$('q').value=state.q;}]
  ].forEach(([n,l,cls,act])=>{
    const b=el('button','kpi '+(cls==='money'?'':cls||''));const nn=el('div','n'+(cls==='money'?' money':''),String(n));
    b.appendChild(nn);b.appendChild(el('div','l',l));
    b.onclick=()=>{act();$('range').value=state.range;draw();window.scrollTo({top:$('agendaH').offsetTop-10,behavior:'smooth'});};
    box.appendChild(b);});
}

function itemRow(i){
  const row=el('div','item'+(done[i.id]?' done':''));
  const cb=el('input');cb.type='checkbox';cb.checked=!!done[i.id];cb.title=L.mark_done;cb.setAttribute('aria-label',L.mark_done);
  cb.onchange=()=>{if(cb.checked)done[i.id]=1;else delete done[i.id];store.set('done',done);draw();};
  row.appendChild(cb);
  const d=el('div','d');const n=days(i.date);
  if(i.date){d.appendChild(document.createTextNode(fmtDate(i.date)));
    d.appendChild(el('span','rel'+(n<0&&i.who!=='info'?' red':n<=7?' amber':''),rel(n)));}
  else d.textContent='—';
  row.appendChild(d);
  const body=el('div');body.appendChild(el('div','t',i.title));
  const m=el('div','meta');
  m.appendChild(el('span','pill p-'+i.who,L['who_'+i.who]));
  if(i.priority==='high')m.appendChild(el('span','pill p-high',L.priority.high));
  m.appendChild(el('span',null,L.kind[i.kind]));
  if(i.client){const a=el('a',null,i.client);a.onclick=()=>{state.client=i.client;$('client').value=i.client;draw();};m.appendChild(a);}
  if(i.trip)m.appendChild(el('span',null,i.trip));
  if(i.notes)m.appendChild(el('span',null,'· '+i.notes));
  body.appendChild(m);row.appendChild(body);
  row.appendChild(el('div','amt',i.amount!=null&&i.amount!==''?money(i.amount,i.currency):''));
  return row;
}

function agenda(){
  const box=$('agenda');box.textContent='';
  const list=D.items.filter(visible);
  const doneCount=D.items.filter(i=>done[i.id]).length;
  $('copy').disabled=!doneCount;$('copy').textContent=L.copy+(doneCount?' ('+doneCount+')':'');
  if(!list.length){box.appendChild(el('div','empty',L.empty));return;}
  const order=['overdue','today','week','soon','later','nodate'],groups={};
  list.forEach(i=>{const b=i.kind==='check'?'checks':bucket(days(i.date));(groups[b]=groups[b]||[]).push(i);});
  order.concat(['checks']).forEach(k=>{if(!groups[k])return;
    const g=el('div','group '+k);const h=el('h3',null,k==='checks'?L.checks:L[k]);h.appendChild(el('span','count',String(groups[k].length)));
    g.appendChild(h);groups[k].forEach(i=>g.appendChild(itemRow(i)));box.appendChild(g);});
}

function cards(){
  const box=$('cards');box.textContent='';
  const list=D.clients.filter(c=>!state.client||state.client===c.client);
  if(!list.length){box.appendChild(el('div','empty',L.nothing_pending));return;}
  if(state.client){const b=el('button','btn ghost',L.clear);b.style.marginBottom='8px';b.onclick=()=>{state.client='';$('client').value='';draw();};box.appendChild(b);}
  list.forEach(c=>{
    const card=el('div','card'+(state.client===c.client?' sel':''));
    card.onclick=()=>{state.client=state.client===c.client?'':c.client;$('client').value=state.client;draw();};
    const top=el('div','top');top.appendChild(el('div','name',c.client));
    if(c.status)top.appendChild(el('span','pill p-info',L.status[c.status]||c.status));card.appendChild(top);
    card.appendChild(el('div','dest',[c.destinations,c.travelers?c.travelers+' pax':''].filter(Boolean).join(' · ')));
    const s=days(c.start),e=days(c.end),cd=el('div','cd');
    if(s!=null&&s>0){cd.appendChild(document.createTextNode(L.departs+' '+fmtDate(c.start)+' · '));cd.appendChild(el('b',null,rel(s)));}
    else if(s!=null&&e!=null&&s<=0&&e>=0){cd.appendChild(el('b',null,L.traveling+' · '+L.back+' '+fmtDate(c.end)));}
    else if(s===0){cd.appendChild(el('b',null,L.departs+' '+L.today_short));}
    if(cd.childNodes.length)card.appendChild(cd);
    const owed=Object.entries(c.owed||{}).filter(([k,v])=>v);
    if(owed.length){const o=el('div','cd');o.appendChild(document.createTextNode(L.balance+': '));o.appendChild(el('b','money',owed.map(([k,v])=>money(v,k)).join(' · ')));card.appendChild(o);}
    const next=D.items.filter(i=>i.client===c.client&&!done[i.id]&&i.date&&(i.who!=='info'||days(i.date)>=0)).slice(0,4);
    const ul=el('ul');
    next.forEach(i=>{const n=days(i.date);const li=el('li',n<0?'red':'');li.appendChild(el('span',null,rel(n)));li.appendChild(el('span',null,L.kind[i.kind]+': '+i.title));ul.appendChild(li);});
    if(!next.length){const li=el('li');li.appendChild(el('span',null,L.nothing_pending));ul.appendChild(li);}
    card.appendChild(ul);box.appendChild(card);});
}

function draw(){
  document.body.classList.toggle('hide',state.hide);
  [...$('who').children].forEach(b=>b.classList.toggle('on',b.dataset.k===state.who));
  kpis();agenda();cards();
}
draw();
})();
</script>
</body>
</html>
"""
