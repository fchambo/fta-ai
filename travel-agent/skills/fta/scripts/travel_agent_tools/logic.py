"""Timeline and commission calculations on data read from the workbooks."""
from datetime import date, timedelta

from . import i18n, schema
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
    info, lang = trip.get("trip") or {}, trip.get("_lang", "en")
    events = []

    def add(when, kind, label, done=False, **extra):
        when = parse_date(when)
        if when is None:
            return
        if done is None:
            done = when <= today
        events.append({"date": when.isoformat(), "kind": kind, "label": label,
                       "status": _status(when, today, done), "days_from_today": (when - today).days, **extra})

    add(info.get("start_date"), "travel", i18n.t(lang, "departure"), done=None)
    add(info.get("end_date"), "travel", i18n.t(lang, "return"), done=None)

    for b in trip.get("bookings") or []:
        kind = schema.choice_label("booking_type", b.get("type"), lang) if b.get("type") else None
        name = " ".join(str(x) for x in (kind, b.get("provider"), b.get("product")) if x)
        add(b.get("start"), "booking", i18n.t(lang, "booking_starts", name=name), done=None, booking=b.get("id"))
        add(b.get("cancellation_deadline"), "deadline", i18n.t(lang, "free_cancel_ends", name=name), booking=b.get("id"))

    totals = {}
    for p in trip.get("payments") or []:
        paid = bool(p.get("paid_date"))
        cur = p.get("currency") or "USD"
        bucket = totals.setdefault(cur, {"paid": 0, "pending": 0, "overdue": 0})
        amount = _num(p.get("amount")) or 0
        due = parse_date(p.get("due_date"))
        bucket["paid" if paid else "overdue" if due and due < today else "pending"] += amount
        payer = schema.choice_label("payer", p.get("payer") or "client", lang)
        who = f"{payer} → {p.get('payee')}" if p.get("payee") else payer
        add(p.get("due_date"), "payment", f"{p.get('description') or i18n.t(lang, 'payment')} ({who})",
            done=paid, amount=amount, currency=cur, payer=p.get("payer") or "client", booking=p.get("booking"))

    for d in trip.get("deadlines") or []:
        add(d.get("date"), "deadline", d.get("what") or i18n.t(lang, "deadline"), done=d.get("done") == "yes")

    events.sort(key=lambda e: e["date"])
    return {"today": today.isoformat(), "trip": info, "events": events,
            "payment_totals": totals, "checks": data_checks(trip), "lang": lang}


def data_checks(trip):
    info, issues, lang = trip.get("trip") or {}, [], trip.get("_lang", "en")
    end = parse_date(info.get("end_date"))
    start = parse_date(info.get("start_date"))
    for b in trip.get("bookings") or []:
        if not b.get("confirmation") and b.get("id"):
            issues.append(i18n.t(lang, "no_confirmation", id=b["id"]))
    for p in trip.get("payments") or []:
        if not p.get("due_date"):
            issues.append(i18n.t(lang, "payment_no_due", desc=p.get("description")))
        elif start and p.get("payer", "client") == "client" and parse_date(p["due_date"]) > start:
            issues.append(i18n.t(lang, "payment_after_departure", desc=p.get("description")))
    for traveler in trip.get("travelers") or []:
        exp = parse_date(traveler.get("passport_expiry"))
        if exp and end and exp < end + timedelta(days=183):
            issues.append(i18n.t(lang, "passport_expiry", name=traveler.get("name"), date=i18n.date_text(exp, lang)))
    gross = sum(_num(b.get("gross_amount")) or 0 for b in trip.get("bookings") or [])
    billed = sum(_num(p.get("amount")) or 0 for p in trip.get("payments") or [] if (p.get("payer") or "client") == "client")
    if gross and billed and abs(gross - billed) > 0.01:
        issues.append(i18n.t(lang, "payments_mismatch", billed=i18n.money(billed, lang), gross=i18n.money(gross, lang)))
    return issues


# --- commissions -----------------------------------------------------------------------

def _rule(row):
    return {k: row.get(k) for k in ("rule_type", "rate_pct", "base", "fixed_amount", "fixed_per", "markup_pct")}


def _base(b, base, warnings, ref, lang):
    gross = _num(b.get("gross_amount")) or 0
    if base == "gross_ex_taxes":
        taxes = _num(b.get("taxes_amount"))
        if taxes is None:
            warnings.append(i18n.t(lang, "no_taxes", ref=ref))
            return gross
        return gross - taxes
    return gross


def _compute(rule, b, warnings, ref, lang):
    kind = rule.get("rule_type")
    if kind == "percentage":
        return _base(b, rule.get("base") or "gross", warnings, ref, lang) * (_num(rule.get("rate_pct")) or 0) / 100
    if kind == "net_markup":
        gross, net = _num(b.get("gross_amount")), _num(b.get("net_amount"))
        if gross is None or net is None:
            warnings.append(i18n.t(lang, "net_needs_amounts", ref=ref))
            return 0.0
        target = _num(rule.get("markup_pct"))
        if target is not None and net and (gross - net) / net * 100 < target:
            warnings.append(i18n.t(lang, "markup_below", ref=ref, actual=i18n.number(round((gross - net) / net * 100, 1), lang),
                                  target=i18n.number(target, lang)))
        return gross - net
    if kind == "fixed":
        per = rule.get("fixed_per") or "booking"
        units = 1 if per == "booking" else _num(b.get("pax" if per == "pax" else "nights"))
        if units is None:
            warnings.append(i18n.t(lang, "fixed_no_units_pax" if per == "pax" else "fixed_no_units_night", ref=ref))
            units = 1
        return (_num(rule.get("fixed_amount")) or 0) * units
    warnings.append(i18n.t(lang, "no_rule", ref=ref))
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
    settings, lang = cfg.get("settings") or {}, cfg.get("_lang", "en")
    withholding = _num(settings.get("withholding_pct")) or 0
    vat = _num(settings.get("tax_on_commission_pct")) or 0
    providers = {str(p["id"]).lower(): p for p in cfg.get("providers") or [] if p.get("id")}
    products = {(str(p.get("provider_id")).lower(), str(p.get("product_id")).lower()): p
                for p in cfg.get("products") or []}

    rows, warnings, volume = [], [], {}
    if not settings.get("withholding_pct") and not settings.get("tax_on_commission_pct"):
        warnings.append(i18n.t(lang, "no_taxes_settings"))
    for p in providers.values():
        exp = parse_date(p.get("contract_expires"))
        if exp and exp < today:
            warnings.append(i18n.t(lang, "contract_expired", id=p["id"], date=i18n.date_text(exp, lang)))

    for trip in trips:
        info = trip.get("trip") or {}
        if info.get("status") == "cancelled":
            continue
        for b in trip.get("bookings") or []:
            ref = f"{info.get('client_name')} / {b.get('id')}"
            provider = providers.get(str(b.get("provider") or "").lower())
            if not provider:
                warnings.append(i18n.t(lang, "unknown_provider", ref=ref, provider=b.get("provider")))
                continue
            if b.get("currency") and provider.get("currency") and b["currency"] != provider["currency"]:
                warnings.append(i18n.t(lang, "currency_mismatch", ref=ref, booking=b["currency"], provider=provider["currency"]))
            product = products.get((str(provider["id"]).lower(), str(b.get("product") or "").lower()))
            rule, source = (_rule(product), "product") if product and product.get("rule_type") else (_rule(provider), "provider default")
            amount = round(_compute(rule, b, warnings, ref, lang), 2)
            method = provider.get("payout_method")
            due = _expected(provider, b, trip)
            rows.append({
                "client": info.get("client_name"), "trip": info.get("trip_id"), "booking": b.get("id"),
                "provider": provider["id"], "product": b.get("product"),
                "rule": f"{rule.get('rule_type')} ({source})",
                "rule_label": (f"{i18n.r(lang, rule['rule_type'])} ({i18n.r(lang, 'product_rule' if source == 'product' else 'provider_default')})"
                               if rule.get("rule_type") in ("percentage", "net_markup", "fixed") else "-"),
                "gross": _num(b.get("gross_amount")),
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
    for tier in cfg.get("incentives") or []:
        tiers_by_provider.setdefault(str(tier.get("provider_id")).lower(), []).append(tier)
    for (pid, year), vol in sorted(volume.items()):
        tiers = sorted(tiers_by_provider.get(pid.lower(), []), key=lambda tier: _num(tier.get("from_volume")) or 0)
        if not tiers:
            continue
        reached = [tier for tier in tiers if vol >= (_num(tier.get("from_volume")) or 0)]
        nxt = next((tier for tier in tiers if vol < (_num(tier.get("from_volume")) or 0)), None)
        rate = (_num(reached[-1].get("rate_pct")) or 0) if reached else 0
        incentives.append({
            "provider": pid, "year": year, "volume": round(vol, 2), "current_extra_pct": rate,
            "bonus_estimate": round(vol * rate / 100, 2),
            "next_tier": {"from": nxt.get("from_volume"), "extra_pct": nxt.get("rate_pct"),
                          "missing": round(_num(nxt.get("from_volume")) - vol, 2)} if nxt else None,
        })

    return {"today": today.isoformat(), "lang": lang, "bookings": rows, "by_provider": by_provider,
            "by_currency": by_currency, "incentives": incentives, "warnings": warnings}
