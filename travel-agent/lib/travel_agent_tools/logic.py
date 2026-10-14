"""Timeline and commission calculations on data read from the workbooks."""
from datetime import date, timedelta

from .workbooks import parse_date

DUE_SOON_DAYS = 14


def _num(v):
    return float(v) if v not in (None, "") else None


# --- timeline ------------------------------------------------------------------------

def _status(when, today, done):
    if done:
        return "done"
    delta = (when - today).days
    return "overdue" if delta < 0 else "due_soon" if delta <= DUE_SOON_DAYS else "upcoming"


def timeline(trip, today):
    info = trip.get("trip") or {}
    events = []

    def add(when, kind, label, done=False, **extra):
        when = parse_date(when)
        if when is None:
            return
        if done is None:
            done = when <= today
        events.append({"date": when.isoformat(), "kind": kind, "label": label,
                       "status": _status(when, today, done), "days_from_today": (when - today).days, **extra})

    add(info.get("start_date"), "travel", "Departure", done=None)
    add(info.get("end_date"), "travel", "Return", done=None)

    for b in trip.get("bookings") or []:
        name = " ".join(str(x) for x in (b.get("type"), b.get("provider"), b.get("product")) if x)
        add(b.get("start"), "booking", f"{name} starts", done=None, booking=b.get("id"))
        add(b.get("cancellation_deadline"), "deadline", f"Free cancellation ends: {name}", booking=b.get("id"))

    totals = {}
    for p in trip.get("payments") or []:
        paid = bool(p.get("paid_date"))
        cur = p.get("currency") or "USD"
        bucket = totals.setdefault(cur, {"paid": 0, "pending": 0, "overdue": 0})
        amount = _num(p.get("amount")) or 0
        due = parse_date(p.get("due_date"))
        bucket["paid" if paid else "overdue" if due and due < today else "pending"] += amount
        who = f"{p.get('payer') or 'client'} → {p.get('payee')}" if p.get("payee") else (p.get("payer") or "client")
        add(p.get("due_date"), "payment", f"{p.get('description') or 'Payment'} ({who})",
            done=paid, amount=amount, currency=cur, payer=p.get("payer") or "client", booking=p.get("booking"))

    for d in trip.get("deadlines") or []:
        add(d.get("date"), "deadline", d.get("what") or "Deadline", done=d.get("done") == "yes")

    events.sort(key=lambda e: e["date"])
    return {"today": today.isoformat(), "trip": info, "events": events,
            "payment_totals": totals, "checks": data_checks(trip)}


def data_checks(trip):
    info, issues = trip.get("trip") or {}, []
    end = parse_date(info.get("end_date"))
    start = parse_date(info.get("start_date"))
    for b in trip.get("bookings") or []:
        if not b.get("confirmation") and b.get("id"):
            issues.append(f"Booking {b['id']} has no confirmation number")
    for p in trip.get("payments") or []:
        if not p.get("due_date"):
            issues.append(f"Payment '{p.get('description')}' has no due date")
        elif start and p.get("payer", "client") == "client" and parse_date(p["due_date"]) > start:
            issues.append(f"Client payment '{p.get('description')}' is due after departure")
    for t in trip.get("travelers") or []:
        exp = parse_date(t.get("passport_expiry"))
        if exp and end and exp < end + timedelta(days=183):
            issues.append(f"{t.get('name')}: passport expires {exp.isoformat()}, less than 6 months after return")
    gross = sum(_num(b.get("gross_amount")) or 0 for b in trip.get("bookings") or [])
    billed = sum(_num(p.get("amount")) or 0 for p in trip.get("payments") or [] if (p.get("payer") or "client") == "client")
    if gross and billed and abs(gross - billed) > 0.01:
        issues.append(f"Client payments ({billed:,.2f}) don't match booking prices ({gross:,.2f})")
    return issues


# --- commissions -----------------------------------------------------------------------

def _rule(row):
    return {k: row.get(k) for k in ("rule_type", "rate_pct", "base", "fixed_amount", "fixed_per", "markup_pct")}


def _base(b, base, warnings, ref):
    gross = _num(b.get("gross_amount")) or 0
    if base == "gross_ex_taxes":
        taxes = _num(b.get("taxes_amount"))
        if taxes is None:
            warnings.append(f"{ref}: no taxes amount, used the full price as base (commission may be overstated)")
            return gross
        return gross - taxes
    return gross


def _compute(rule, b, warnings, ref):
    kind = rule.get("rule_type")
    if kind == "percentage":
        return _base(b, rule.get("base") or "gross", warnings, ref) * (_num(rule.get("rate_pct")) or 0) / 100
    if kind == "net_markup":
        gross, net = _num(b.get("gross_amount")), _num(b.get("net_amount"))
        if gross is None or net is None:
            warnings.append(f"{ref}: net-rate rule needs both client price and net amount")
            return 0.0
        target = _num(rule.get("markup_pct"))
        if target is not None and net and (gross - net) / net * 100 < target:
            warnings.append(f"{ref}: markup {(gross - net) / net * 100:.1f}% is below the suggested {target:g}%")
        return gross - net
    if kind == "fixed":
        per = rule.get("fixed_per") or "booking"
        units = 1 if per == "booking" else _num(b.get("pax" if per == "pax" else "nights"))
        if units is None:
            warnings.append(f"{ref}: fixed amount per {per} but the booking has no {'passengers' if per == 'pax' else 'nights'}")
            units = 1
        return (_num(rule.get("fixed_amount")) or 0) * units
    warnings.append(f"{ref}: provider has no commission rule set")
    return 0.0


def _expected(provider, b, trip):
    days = int(_num(provider.get("days_after")) or 0)
    timing, anchor = provider.get("payout_timing"), None
    if timing == "on_booking":
        anchor = parse_date(b.get("booked_date")) or parse_date((trip.get("trip") or {}).get("created"))
    elif timing == "on_final_payment":
        dues = [parse_date(p["due_date"]) for p in trip.get("payments") or []
                if p.get("due_date") and str(p.get("booking") or "").upper() in (str(b.get("id")).upper(), "ALL")]
        anchor = max(dues) if dues else None
    elif timing == "after_travel":
        anchor = parse_date(b.get("end")) or parse_date((trip.get("trip") or {}).get("end_date"))
    return anchor + timedelta(days=days) if anchor else None


def _payout_status(method, received, due, today):
    if received:
        return "received"
    if due and due < today:
        # With "deduct" the agent keeps the margin when remitting the net: nothing to chase.
        return "retained" if method == "deduct" else "overdue"
    return "pending"


def commissions(cfg, trips, today):
    settings = cfg.get("settings") or {}
    withholding = _num(settings.get("withholding_pct")) or 0
    vat = _num(settings.get("tax_on_commission_pct")) or 0
    providers = {str(p["id"]).lower(): p for p in cfg.get("providers") or [] if p.get("id")}
    products = {(str(p.get("provider_id")).lower(), str(p.get("product_id")).lower()): p
                for p in cfg.get("products") or []}

    rows, warnings, volume = [], [], {}
    if not settings.get("withholding_pct") and not settings.get("tax_on_commission_pct"):
        warnings.append("VAT and withholding % are not set in Settings: amounts are before taxes")
    for p in providers.values():
        exp = parse_date(p.get("contract_expires"))
        if exp and exp < today:
            warnings.append(f"{p['id']}: contract expired on {exp.isoformat()}")

    for trip in trips:
        info = trip.get("trip") or {}
        if info.get("status") == "cancelled":
            continue
        for b in trip.get("bookings") or []:
            ref = f"{info.get('client_name')} / {b.get('id')}"
            provider = providers.get(str(b.get("provider") or "").lower())
            if not provider:
                warnings.append(f"{ref}: provider '{b.get('provider')}' is not in the Providers sheet")
                continue
            if b.get("currency") and provider.get("currency") and b["currency"] != provider["currency"]:
                warnings.append(f"{ref}: booking in {b['currency']} but provider pays in {provider['currency']}")
            product = products.get((str(provider["id"]).lower(), str(b.get("product") or "").lower()))
            rule, source = (_rule(product), "product") if product and product.get("rule_type") else (_rule(provider), "provider default")
            amount = round(_compute(rule, b, warnings, ref), 2)
            method = provider.get("payout_method")
            due = _expected(provider, b, trip)
            rows.append({
                "client": info.get("client_name"), "trip": info.get("trip_id"), "booking": b.get("id"),
                "provider": provider["id"], "product": b.get("product"),
                "rule": f"{rule.get('rule_type')} ({source})", "gross": _num(b.get("gross_amount")),
                "commission": amount, "withholding": round(amount * withholding / 100, 2),
                "vat_to_invoice": round(amount * vat / 100, 2) if method == "invoice" else 0,
                "currency": b.get("currency") or provider.get("currency"), "payout_method": method,
                "expected_date": due.isoformat() if due else None,
                "status": _payout_status(method, parse_date(b.get("commission_received_date")), due, today),
            })
            year = (parse_date(b.get("start")) or today).year
            volume[(provider["id"], year)] = volume.get((provider["id"], year), 0) + (_num(b.get("gross_amount")) or 0)

    by_provider, by_currency = {}, {}
    for r in rows:
        bp = by_provider.setdefault(r["provider"], {"bookings": 0, "gross": 0, "commission": 0, "currency": r["currency"]})
        bp["bookings"] += 1
        bp["gross"] += r["gross"] or 0
        bp["commission"] += r["commission"]
        bucket = by_currency.setdefault(r["currency"], {"received": 0, "retained": 0, "pending": 0, "overdue": 0})
        bucket[r["status"]] += r["commission"] - r["withholding"]

    incentives = []
    tiers_by_provider = {}
    for t in cfg.get("incentives") or []:
        tiers_by_provider.setdefault(str(t.get("provider_id")).lower(), []).append(t)
    for (pid, year), vol in sorted(volume.items()):
        tiers = sorted(tiers_by_provider.get(pid.lower(), []), key=lambda t: _num(t.get("from_volume")) or 0)
        if not tiers:
            continue
        reached = [t for t in tiers if vol >= (_num(t.get("from_volume")) or 0)]
        nxt = next((t for t in tiers if vol < (_num(t.get("from_volume")) or 0)), None)
        rate = (_num(reached[-1].get("rate_pct")) or 0) if reached else 0
        incentives.append({
            "provider": pid, "year": year, "volume": round(vol, 2), "current_extra_pct": rate,
            "bonus_estimate": round(vol * rate / 100, 2),
            "next_tier": {"from": nxt.get("from_volume"), "extra_pct": nxt.get("rate_pct"),
                          "missing": round(_num(nxt.get("from_volume")) - vol, 2)} if nxt else None,
        })

    return {"today": today.isoformat(), "bookings": rows, "by_provider": by_provider,
            "by_currency": by_currency, "incentives": incentives, "warnings": warnings}
