"""Theme-park day planner (Disney World and Universal Orlando).

Park data lives in the park-itinerary skill (scripts/parks/*.json). The planner is
deterministic: Claude gathers the party's needs, writes a request, reads the plan,
adjusts the request and re-runs. Waits are estimates from typical crowd patterns,
never live data.
"""
import glob
import json
import math
import os
import re
import unicodedata
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_CANDIDATES = [
    os.path.join(os.path.dirname(HERE), "parks"),  # <skill>/scripts/parks
    os.path.join(os.path.dirname(os.path.dirname(HERE)), "travel-agent", "skills", "park-itinerary", "scripts", "parks"),
]

# Traveler flags: what each one rules out.
FLAGS = {
    "claustrophobic": {"tags": {"enclosed"}},
    "motion_sickness": {"tags": {"sim", "spin"}},
    "fear_dark": {"tags": {"dark"}},
    "fear_heights": {"tags": {"heights", "drops"}},
    "scared_easily": {"tags": {"scary"}},
    "no_coasters": {"tags": {"coaster"}},
    "no_wet": {"tags": {"wet"}},
    "sensory": {"tags": {"loud", "fire"}},
    "mild_only": {"max_thrill": 1},
    "no_thrill": {"max_thrill": 0},
    "pregnant": {"max_thrill": 1, "tags": {"coaster", "sim", "drops", "spin", "bumpy", "launch"}},
    "back_neck": {"max_thrill": 1, "tags": {"coaster", "bumpy", "launch"}},
    "wheelchair": {"access": 1},        # uses a wheelchair/ECV, can transfer to a ride seat
    "no_transfer": {"access": 0},       # must stay in the wheelchair
    "limited_walking": {"access": 1, "slow": True},
    "das": {},                          # Disney DAS / Universal AAP candidate: affects tips and waits
}
ACCESS = {"wheelchair": 0, "transfer": 1, "ambulatory": 2}
CROWD = {"low": 0.65, "moderate": 1.0, "high": 1.35, "peak": 1.7}
WEIGHT = {"must": 3.0, "nice": 1.2, "extra": 0.35}
TIMED_ONLY = {"parade", "fireworks"}
LL_LANES = {"multi", "t1", "t2"}
TIERED_LIMITS = {"t1": 1, "t2": 2}


# --- helpers ----------------------------------------------------------------------

def norm(text):
    text = str(text).replace("'", "").replace("\u2019", "")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def hm(value):
    """'09:30' or '9:30 pm' -> minutes after midnight."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value)
    m = re.fullmatch(r"\s*(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?\s*", str(value).lower())
    if not m:
        raise ValueError(f"Time must look like 09:30 or 9:30 pm, got: {value}")
    h, mnt, ampm = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ampm and ampm.startswith("p") and h < 12:
        h += 12
    if ampm and ampm.startswith("a") and h == 12:
        h = 0
    return h * 60 + mnt


def clock(minutes):
    minutes = int(round(minutes))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def round5(x):
    return int(5 * round(x / 5))


# --- data -------------------------------------------------------------------------

def data_dir():
    env = os.environ.get("TA_PARKS_DIR")
    for path in ([env] if env else []) + DATA_CANDIDATES:
        if path and os.path.isdir(path):
            return path
    raise RuntimeError("Park data not found: use the park-itinerary skill's scripts/ta.py, or set TA_PARKS_DIR.")


def load_parks():
    parks = {}
    for path in sorted(glob.glob(os.path.join(data_dir(), "*.json"))):
        with open(path, encoding="utf-8") as f:
            park = json.load(f)
        parks[park["id"]] = park
    return parks


def find_park(parks, key):
    k = norm(key)
    for park in parks.values():
        if k in (park["id"], norm(park["name"])):
            return park
    hits = [p for p in parks.values() if k and k in norm(p["name"])]
    if len(hits) == 1:
        return hits[0]
    raise ValueError(f"Unknown park '{key}'. Known: {', '.join(f'{p['id']} ({p['name']})' for p in parks.values())}")


def find_attraction(park, key):
    k = norm(key)
    by_id = {a["id"]: a for a in park["attractions"]}
    if key in by_id:
        return by_id[key]
    for a in park["attractions"]:
        if k == norm(a["name"]) or k == norm(a["id"]):
            return a
    hits = [a for a in park["attractions"] if k and k in norm(a["name"])]
    if len(hits) == 1:
        return hits[0]
    words = set(k.split())
    scored = sorted(((len(words & set(norm(a["name"]).split())), a) for a in park["attractions"]), key=lambda s: -s[0])
    if scored and scored[0][0] and (len(scored) == 1 or scored[0][0] > scored[1][0]):
        return scored[0][1]
    return None


# --- the party --------------------------------------------------------------------

def prepare_party(party):
    people = []
    for i, p in enumerate(party):
        p = dict(p)
        p.setdefault("name", f"Traveler {i + 1}")
        if p.get("height_cm") not in (None, ""):
            p["_in"] = float(p["height_cm"]) / 2.54
        elif p.get("height_in") not in (None, ""):
            p["_in"] = float(p["height_in"])
        else:
            p["_in"] = None
        age = p.get("age")
        p["_adult"] = age in (None, "") or float(age) >= 14
        p["_child"] = not p["_adult"]
        p["_height_unknown"] = p["_in"] is None and age not in (None, "") and float(age) < 12
        flags = [f for f in p.get("flags", []) if f]
        unknown = [f for f in flags if f not in FLAGS]
        p["_avoid_tags"] = set(p.get("avoid", []))
        p["_max_thrill"] = 3
        p["_access"] = 2
        for f in flags:
            rule = FLAGS.get(f, {})
            p["_avoid_tags"] |= rule.get("tags", set())
            p["_max_thrill"] = min(p["_max_thrill"], rule.get("max_thrill", 3))
            p["_access"] = min(p["_access"], rule.get("access", 2))
        p["_unknown_flags"] = unknown
        people.append(p)
    return people


def can_ride(person, a, skip_ids):
    """None if the person can do it, else (reason code, detail)."""
    if a["id"] in skip_ids or a["id"] in person.get("skip", []):
        return ("skip", "")
    need = a.get("height_in")
    if need:
        if person["_height_unknown"]:
            return ("height_unknown", f'{need} in / {round(need * 2.54)} cm')
        if person["_in"] is not None and person["_in"] + 1e-6 < need:
            return ("too_short", f'{need} in / {round(need * 2.54)} cm')
    top = a.get("max_height_in")
    if top and person["_in"] is not None and person["_in"] > top and a.get("needs_child"):
        return ("needs_child", "")
    if a.get("thrill", 0) > person["_max_thrill"]:
        return ("too_intense", "")
    clash = sorted(set(a.get("tags", [])) & person["_avoid_tags"])
    if clash:
        return ("tags", ", ".join(clash))
    if ACCESS.get(a.get("access", "transfer"), 1) > person["_access"]:
        return ("access", a.get("access", ""))
    return None


def evaluate(a, people, skip_ids):
    riders, out = [], []
    for p in people:
        why = can_ride(p, a, skip_ids)
        if why:
            out.append({"name": p["name"], "reason": why[0], "detail": why[1]})
        else:
            riders.append(p)
    if a.get("needs_child") and riders:
        kids_ok = [p for p in riders if p["_in"] is not None and p["_in"] <= a.get("max_height_in", 999)]
        if not kids_ok:
            riders = []
    switch = False
    if riders and out:
        non_riding_kids = [o for o in out if next(p for p in people if p["name"] == o["name"])["_child"]]
        adults = [p for p in people if p["_adult"]]
        rider_adults = [p for p in riders if p["_adult"]]
        # A second adult stays with the kids who can't ride, then they swap.
        switch = bool(non_riding_kids) and len(adults) >= 2 and bool(rider_adults)
        if non_riding_kids and not switch and not any(p["_adult"] for p in people if p not in riders):
            riders = []  # nobody can stay with the kids
            out = out + [{"name": "*", "reason": "no_supervisor", "detail": ""}]
    return riders, out, switch


# --- waits and walking ------------------------------------------------------------

class Clock:
    def __init__(self, open_, close, crowd):
        self.open, self.close, self.crowd = open_, close, CROWD.get(crowd or "moderate", 1.0)

    def factor(self, t):
        if t < self.open:
            return 0.25  # early entry: only hotel guests are in the park
        h, rem = (t - self.open) / 60, (self.close - t) / 60
        f = 0.3 if h < 0.5 else 0.5 if h < 1 else 0.75 if h < 2 else 0.92 if h < 3 else 1.0
        if rem < 0.75:
            f = min(f, 0.5)
        elif rem < 1.5:
            f = min(f, 0.65)
        elif rem < 3:
            f = min(f, 0.85)
        return f

    def standby(self, a, t):
        kind = a.get("type")
        if kind == "walk":
            return 0
        if kind == "show":
            return min(20, round5(a.get("peak", 10) * self.crowd))
        peak = a.get("peak", 20) * self.crowd
        w = peak * self.factor(t)
        if a.get("rope") and self.open <= t < self.open + 30:
            w = max(w, peak * 0.4)  # everyone runs to the headliners at opening
        return max(5, round5(w))


class Walker:
    def __init__(self, park, slow):
        self.mpu = park.get("meters_per_unit", 9)
        self.speed = 52 if slow else 68  # meters per minute, including crowds

    def minutes(self, a, b):
        if a is None or b is None:
            return 0
        d = math.dist(a, b) * self.mpu * 1.3
        return 0 if d < 1 else max(3, round(d / self.speed + 1))


# --- planning ---------------------------------------------------------------------

def _pos(a):
    return (a["x"], a["y"])


def _resolve_list(park, keys, warnings, label):
    found = []
    for key in keys or []:
        a = find_attraction(park, key)
        if a is None:
            warnings.append({"code": "unknown_attraction", "what": key, "list": label})
        elif a not in found:
            found.append(a)
    return found


def _suggest_lightning(park, day, chosen, clock_, leave, breaks, booked, rope_first):
    """Suggested Lightning Lane return times when the party buys LL but hasn't booked yet."""
    mode = (day.get("ll") or "none").lower()
    if park["operator"] != "disney" or mode in ("none", "no", ""):
        return []
    out, taken = [], []
    want_multi = "multi" in mode or "premier" in mode
    want_single = "single" in mode or "premier" in mode
    pool = sorted((c for c in chosen.values() if c["a"]["id"] not in booked and c["a"]["id"] != rope_first),
                  key=lambda c: -(c["weight"] * c["a"].get("peak", 0)))

    def free_slot(t):
        """First time from t that avoids breaks, reservations and other suggested slots."""
        for _ in range(24):
            moved = False
            for b0, b1 in sorted(breaks):
                if b0 - 45 <= t < b1:
                    t, moved = b1 + 15, True
            clash = [x for x in taken if abs(t - x) < 45]
            if clash:
                t, moved = max(clash) + 45, True
            if not moved:
                return t
        return t

    if want_multi:
        limits = dict(TIERED_LIMITS) if park.get("ll_tiers") else {"multi": 3}
        picks = []
        for c in pool:
            lane = c["a"].get("lane")
            if lane not in LL_LANES or c["weight"] < WEIGHT["extra"] or c["a"].get("type") in TIMED_ONLY:
                continue
            bucket = lane if park.get("ll_tiers") else "multi"
            if limits.get(bucket, 0) > 0:
                limits[bucket] -= 1
                picks.append(c)
            if sum(limits.values()) == 0:
                break
        start = max(clock_.open, day["_arrive"]) + 90
        for i, c in enumerate(picks):
            t = free_slot(start + 75 * i)
            if t <= leave - 60:
                taken.append(t)
                out.append({"a": c["a"], "time": t, "kind": "multi", "suggested": True})
    if want_single:
        singles = [c for c in pool if c["a"].get("lane") == "single" and c["weight"] >= WEIGHT["nice"]]
        for c in singles[:2]:
            t = free_slot(max(clock_.open, day["_arrive"]) + 150)
            if t <= leave - 60:
                taken.append(t)
                out.append({"a": c["a"], "time": t, "kind": "single", "suggested": True})
    return out


def plan_day(park, day, people, prefs, warnings):
    clock_ = Clock(hm(day.get("open") or "09:00"), hm(day.get("close") or "21:00"), day.get("crowd") or prefs.get("crowd"))
    early = bool(day.get("early_entry"))
    default_arrive = clock_.open - (30 if early else 0) - (0 if early else 15)
    arrive = hm(day.get("arrive")) if day.get("arrive") else default_arrive
    day["_arrive"] = arrive
    leave = hm(day.get("leave")) if day.get("leave") else clock_.close
    youngest = min([float(p["age"]) for p in people if p.get("age") not in (None, "")] or [99])
    slow = prefs.get("stroller") or youngest < 6 or prefs.get("pace") == "relaxed" or any(
        FLAGS.get(f, {}).get("slow") or f in ("wheelchair", "no_transfer") for p in people for f in p.get("flags", []))
    walker = Walker(park, slow)
    entrance = tuple(park["entrance"])
    start_pos = entrance
    if day.get("start_at"):
        spot = find_attraction(park, day["start_at"])
        if spot is None:
            warnings.append({"code": "unknown_place", "what": day["start_at"], "park": park["id"]})
        else:
            start_pos = _pos(spot)
    express = (day.get("express") or "").lower() if park["operator"] == "universal" else ""
    single_rider_ok = bool(prefs.get("single_rider_ok"))
    split_ok = prefs.get("split_ok", True)
    extras = day.get("extras", prefs.get("extras", True))
    day_warnings = []

    closed = {a["id"] for a in _resolve_list(park, day.get("closed"), day_warnings, "closed")}
    reopened = {a["id"] for a in _resolve_list(park, day.get("open_anyway"), day_warnings, "open_anyway")}
    skip = {a["id"] for a in _resolve_list(park, day.get("skip"), day_warnings, "skip")}
    must = _resolve_list(park, day.get("must"), day_warnings, "must")
    nice = [a for a in _resolve_list(park, day.get("nice"), day_warnings, "nice") if a not in must]

    chosen, excluded = {}, []
    for a in park["attractions"]:
        status = a.get("status", "open")
        level = "must" if a in must else "nice" if a in nice else "extra"
        if a["id"] in closed or (status == "closed" and a["id"] not in reopened):
            if level != "extra":
                excluded.append({"id": a["id"], "name": a["name"], "reason": "closed", "note": a.get("status_note", "")})
            continue
        if a.get("requires") == "park-to-park" and (level == "extra" or not day.get("park_to_park")):
            if level != "extra":
                day_warnings.append({"code": "needs_park_to_park", "what": a["name"]})
            continue
        riders, out, switch = evaluate(a, people, skip)
        if a["id"] in skip:
            continue
        if not riders:
            if level != "extra" or a.get("peak", 0) >= 30:
                excluded.append({"id": a["id"], "name": a["name"], "reason": "nobody", "who": out,
                                 "requested": level != "extra"})
            continue
        if level == "extra":
            if not extras or a.get("type") in TIMED_ONLY:
                continue
            kids_out = [o for o in out if next((p for p in people if p["name"] == o["name"]), {}).get("_child")]
            if kids_out and not (split_ok and switch and a.get("thrill", 0) >= 2):
                continue  # don't split the family for a gentle ride, or without a second adult
            if out and not kids_out and len(riders) < 2:
                continue  # an adult sitting out is fine, but not for one rider alone
        if out and not switch and len(riders) < len(people) and level != "extra":
            day_warnings.append({"code": "partial_group", "what": a["name"], "who": [o["name"] for o in out]})
        weight = WEIGHT[level] * (1 if not out else 0.8)
        if a.get("status") == "verify":
            day_warnings.append({"code": "verify_status", "what": a["name"], "note": a.get("status_note", "")})
        if a.get("verify"):
            day_warnings.append({"code": "verify_data", "what": a["name"], "fields": a["verify"]})
        chosen[a["id"]] = {"a": a, "riders": riders, "out": out, "switch": switch, "weight": weight, "level": level}

    for p in people:
        if p["_height_unknown"]:
            day_warnings.append({"code": "height_unknown", "who": p["name"]})
        for f in p["_unknown_flags"]:
            day_warnings.append({"code": "unknown_flag", "who": p["name"], "what": f})

    # --- fixed appointments
    appts = []
    breaks = []
    if day.get("break"):
        b0, b1 = hm(day["break"]["start"]), hm(day["break"]["end"])
        breaks.append((b0, b1))
        appts.append({"kind": "break", "start": b0, "end": b1, "pos": entrance, "name": day["break"].get("name")})
    booked = set()
    for item in day.get("lightning", []):
        a = find_attraction(park, item.get("attraction", ""))
        if a is None:
            day_warnings.append({"code": "unknown_attraction", "what": item.get("attraction"), "list": "lightning"})
            continue
        booked.add(a["id"])
        if a["id"] not in chosen:
            riders, out, switch = evaluate(a, people, set())
            if not riders:
                day_warnings.append({"code": "ll_nobody", "what": a["name"]})
                continue
            chosen[a["id"]] = {"a": a, "riders": riders, "out": out, "switch": switch, "weight": WEIGHT["nice"], "level": "nice"}
        kind = "single" if a.get("lane") == "single" else ("express" if park["operator"] == "universal" else "multi")
        appts.append({"kind": "ll", "lane": kind, "a": a, "start": hm(item["time"]),
                      "window": int(item.get("window", 60)), "pos": _pos(a), "suggested": False})
    for item in day.get("fixed", []):
        a = find_attraction(park, item["attraction"]) if item.get("attraction") else None
        at = item.get("at")
        pos = _pos(a) if a else None
        if pos is None and at:
            spot = find_attraction(park, at)
            mark = park.get("landmark") or {}
            land = next((l for l in park["lands"] if norm(at) in norm(l["name"])), None)
            if mark and norm(at) and norm(at) in norm(mark.get("name", "")):
                pos = (mark["x"], mark["y"])
            else:
                pos = _pos(spot) if spot else (land["x"] + land["w"] / 2, land["y"] + land["h"] / 2) if land else None
            if pos is None:
                day_warnings.append({"code": "unknown_place", "what": at})
        if item.get("time") in (None, ""):
            day_warnings.append({"code": "needs_time", "what": item.get("name") or (a or {}).get("name")})
            continue
        minutes = int(item.get("minutes") or (a or {}).get("min") or 45)
        early_by = int(item.get("arrive_early", 20 if a and a.get("type") in TIMED_ONLY else 0))
        start = hm(item["time"])
        appts.append({"kind": item.get("kind") or ("show" if a else "meal"), "a": a, "start": start - early_by,
                      "show_time": start, "end": start + minutes, "pos": pos,
                      "name": item.get("name") or (a or {}).get("name"), "note": item.get("note", "")})
        if a:
            chosen.pop(a["id"], None)
    for a in must + nice:
        if a.get("type") in TIMED_ONLY and not any(x.get("a") is a for x in appts):
            day_warnings.append({"code": "needs_time", "what": a["name"]})
            chosen.pop(a["id"], None)

    rope_candidates = sorted((c for c in chosen.values() if c["a"].get("rope") and c["a"]["id"] not in booked),
                             key=lambda c: -(c["weight"] * c["a"].get("peak", 0)))
    rope_first = rope_candidates[0]["a"]["id"] if rope_candidates and arrive <= clock_.open + 15 else None
    # suggested return times must also avoid dining reservations and shows
    blocked = breaks + [(x["start"], x.get("end", x["start"] + 30)) for x in appts if x["kind"] not in ("ll", "break")]
    for s in _suggest_lightning(park, day, chosen, clock_, leave, blocked, booked, rope_first):
        booked.add(s["a"]["id"])
        appts.append({"kind": "ll", "lane": s["kind"], "a": s["a"], "start": s["time"], "window": 60,
                      "pos": _pos(s["a"]), "suggested": True})
    appts.sort(key=lambda x: x["start"])
    remaining = {k: v for k, v in chosen.items() if k not in booked}

    has_lunch = any(x["kind"] == "meal" and hm("11:00") <= x.get("show_time", x["start"]) <= hm("14:30") for x in appts)
    has_dinner = any(x["kind"] == "meal" and x.get("show_time", x["start"]) >= hm("17:00") for x in appts)
    has_rest = bool(breaks) or not (prefs.get("pace") == "relaxed" or youngest < 6)
    meal_len = 60 if prefs.get("pace") == "relaxed" else 45

    def lane_wait(c, t):
        a = c["a"]
        w = clock_.standby(a, t)
        lane = "standby"
        if express and a.get("lane") == "express" and a.get("type") != "walk":
            w, lane = max(5, round5(w * 0.25)), "express"
        elif (single_rider_ok and a.get("single_rider") and not c["switch"]
              and all(p["_adult"] or float(p.get("age") or 99) >= 10 for p in c["riders"])):
            sr = max(5, round5(w * 0.45))
            if sr < w:
                w, lane = sr, "single_rider"
        if "das" in {f for p in people for f in p.get("flags", [])} and a.get("type") == "ride":
            lane = lane if lane != "standby" else "standby_das"
        return w, lane

    def ride_minutes(c):
        return c["a"].get("min", 5) + ((c["a"].get("min", 5) + 5) if c["switch"] else 0)

    # a train to the other park ends this park's segment: keep it for last
    finale = [c for c in remaining.values() if c["a"].get("requires") == "park-to-park"]
    for c in finale:
        remaining.pop(c["a"]["id"])
    finale_min = sum(walker.minutes(entrance, _pos(c["a"])) + clock_.standby(c["a"], leave) + c["a"].get("min", 6)
                     for c in finale[:1])
    leave -= finale_min

    steps, t, pos = [], arrive, start_pos
    steps.append({"kind": "arrive", "start": arrive, "end": arrive, "early_entry": early and arrive < clock_.open,
                  "pos": start_pos})

    def add(step):
        steps.append(step)

    def do_appt(x, t, pos):
        walk = walker.minutes(pos, x["pos"]) if x["pos"] else 0
        arrive_at = t + walk
        if x["kind"] == "ll":
            begin = max(arrive_at, x["start"])
            if begin - t - walk >= 15:
                add({"kind": "free", "start": t, "end": begin - walk, "pos": pos})
            c = chosen.get(x["a"]["id"]) or {"a": x["a"], "riders": people, "out": [], "switch": False}
            wait = max(5, round5(10 * clock_.crowd))
            end = begin + wait + ride_minutes(c)
            add({"kind": "ride", "a": x["a"], "start": begin, "end": end, "walk": walk, "wait": wait,
                 "lane": "ll_" + x["lane"], "fixed": True, "window": [x["start"], x["start"] + x["window"]],
                 "suggested": x.get("suggested", False), "late": begin > x["start"] + x["window"],
                 "riders": [p["name"] for p in c["riders"]], "out": c["out"], "switch": c["switch"], "pos": x["pos"]})
            remaining.pop(x["a"]["id"], None)
            return end, x["pos"]
        begin = max(arrive_at, x["start"])
        if x["start"] - (t + walk) >= 15:
            add({"kind": "free", "start": t, "end": x["start"] - walk, "pos": pos})
        end = x["end"]
        if x["kind"] == "break":
            add({"kind": "break", "start": begin - walk, "end": end, "walk": walk, "fixed": True, "pos": entrance,
                 "name": x.get("name")})
            return end, entrance
        add({"kind": x["kind"], "a": x.get("a"), "name": x.get("name"), "start": begin, "end": end,
             "show_time": x.get("show_time"), "walk": walk, "fixed": True, "pos": x["pos"] or pos,
             "note": x.get("note", ""), "late": begin > x.get("show_time", x["start"])})
        return end, (x["pos"] or pos)

    guard = 0
    while t < leave and guard < 400:
        guard += 1
        nxt = next((x for x in appts if not x.get("done")), None)
        # meals and rest, at the current spot
        def fits(minutes):
            if t + minutes > leave:
                return False
            return nxt is None or t + minutes + walker.minutes(pos, nxt["pos"]) <= nxt["start"] + (30 if nxt["kind"] == "ll" else 0)
        if not has_lunch and hm("11:45") <= t <= hm("14:00") and fits(meal_len):
            add({"kind": "meal", "meal": "lunch", "start": t, "end": t + meal_len, "pos": pos, "auto": True})
            t, has_lunch = t + meal_len, True
            continue
        if not has_dinner and leave >= hm("19:30") and hm("17:45") <= t <= hm("19:30") and fits(meal_len):
            add({"kind": "meal", "meal": "dinner", "start": t, "end": t + meal_len, "pos": pos, "auto": True})
            t, has_dinner = t + meal_len, True
            continue
        if not has_rest and hm("15:00") <= t <= hm("16:30") and fits(20):
            add({"kind": "rest", "start": t, "end": t + 20, "pos": pos, "auto": True})
            t, has_rest = t + 20, True
            continue
        if nxt:
            latest = nxt["start"] + (min(30, nxt.get("window", 60) - 15) if nxt["kind"] == "ll" else 0)
            deadline = latest
        else:
            deadline = leave
        best, best_score = None, 0
        late_day = (leave - t) < 150
        for key, c in remaining.items():
            a = c["a"]
            walk = walker.minutes(pos, _pos(a))
            wait, lane = lane_wait(c, t + walk)
            dur = ride_minutes(c)
            finish = t + walk + wait + dur
            onward = walker.minutes(_pos(a), nxt["pos"]) if nxt and nxt["pos"] else 0
            if finish + onward > deadline:
                continue
            later = [lane_wait(c, x)[0] for x in range(int(finish), int(leave), 45)] or [wait]
            saving = max(0, sum(later) / len(later) - wait)
            weight = c["weight"] * (3 if late_day and c["level"] == "must" else 1)
            # walking counts extra: crisscrossing the park tires kids and eats the day
            score = weight * (1 + saving / 20) / (1.8 * walk + wait + dur + 0.5 * onward)
            if score > best_score:
                best, best_score = (key, c, walk, wait, lane, dur), score
        if best:
            key, c, walk, wait, lane, dur = best
            start = t + walk
            add({"kind": c["a"].get("type", "ride"), "a": c["a"], "start": start, "end": start + wait + dur, "walk": walk,
                 "wait": wait, "lane": lane, "fixed": False, "riders": [p["name"] for p in c["riders"]],
                 "out": c["out"], "switch": c["switch"], "pos": _pos(c["a"]), "level": c["level"]})
            t, pos = start + wait + dur, _pos(c["a"])
            remaining.pop(key)
            continue
        if nxt:
            t, pos = do_appt(nxt, t, pos)
            nxt["done"] = True
            if nxt.get("a") is not None and nxt["a"].get("type") == "fireworks" and not day.get("after_fireworks"):
                leave = min(leave, t)  # the nighttime show ends the day
            continue
        break
    for x in appts:  # appointments past the planned leave time
        if not x.get("done") and x["start"] < hm("23:59"):
            t, pos = do_appt(x, t, pos)
            x["done"] = True
    end_t = max(t, steps[-1]["end"])
    if finale:
        c = finale[0]
        walk = walker.minutes(pos, _pos(c["a"]))
        wait = clock_.standby(c["a"], end_t + walk)
        if leave - end_t >= 45:
            steps.append({"kind": "free", "start": end_t, "end": leave, "pos": pos, "repeat": True})
            day_warnings.append({"code": "day_ends_early", "free_min": leave - end_t})
            end_t = leave
            walk = walker.minutes(pos, _pos(c["a"]))
        start = end_t + walk
        end = start + wait + c["a"].get("min", 6)
        steps.append({"kind": "ride", "a": c["a"], "start": start, "end": end, "walk": walk, "wait": wait,
                      "lane": "standby", "fixed": False, "riders": [p["name"] for p in c["riders"]], "out": c["out"],
                      "switch": False, "pos": _pos(c["a"]), "level": c["level"], "transfer": True})
        steps.append({"kind": "leave", "start": end, "end": end, "pos": _pos(c["a"]), "transfer": True})
        leave = end
        end_t = None
    if end_t is not None and leave - end_t >= 45:
        steps.append({"kind": "free", "start": end_t, "end": leave, "pos": pos, "repeat": True})
        day_warnings.append({"code": "day_ends_early", "free_min": leave - end_t})
        end_t = leave
    if end_t is not None:
        steps.append({"kind": "leave", "start": end_t, "end": end_t, "pos": entrance,
                      "walk": walker.minutes(pos, entrance)})

    unmet = [{"id": c["a"]["id"], "name": c["a"]["name"], "level": c["level"],
              "lane": c["a"].get("lane"), "peak": c["a"].get("peak")}
             for c in remaining.values() if c["level"] in ("must", "nice")]
    for u in unmet:
        if u["level"] == "must":
            day_warnings.append({"code": "must_unmet", "what": u["name"], "lane": u["lane"]})
    for c in chosen.values():
        a = c["a"]
        if (c["level"] == "must" and a.get("lane") == "single" and a["id"] not in booked and a["id"] != rope_first
                and park["operator"] == "disney"):
            day_warnings.append({"code": "consider_single_pass", "what": a["name"]})
        if c["level"] == "must" and a.get("lane") is None and park["operator"] == "universal" and a.get("rope") and a["id"] != rope_first:
            day_warnings.append({"code": "no_express_rope_drop", "what": a["name"]})

    # number the stops and add a baseline for comparison
    n = 0
    for s in steps:
        if s["kind"] in ("arrive", "leave", "free"):
            continue
        n += 1
        s["n"] = n
    done = [s for s in steps if s.get("a") is not None and s["kind"] not in TIMED_ONLY]
    total_wait = sum(s.get("wait", 0) for s in steps)
    total_walk = sum(s.get("walk", 0) for s in steps)
    baseline = sum(round5(s["a"].get("peak", 0) * clock_.crowd) for s in done if s["a"].get("type") not in ("walk", "show"))
    baseline += sum(min(20, s["a"].get("peak", 0)) for s in done if s["a"].get("type") == "show")
    for w in day_warnings:
        w.setdefault("park", park["id"])
    warnings.extend(day_warnings)
    return {
        "date": day.get("date"), "park": park["id"], "park_name": park["name"], "resort": park["resort"],
        "operator": park["operator"], "open": clock(clock_.open), "close": clock(clock_.close),
        "arrive": clock(arrive), "leave": clock(leave), "early_entry": early, "crowd": day.get("crowd") or prefs.get("crowd") or "moderate",
        "ll": day.get("ll"), "express": express or None,
        "steps": [_public_step(s) for s in steps],
        "excluded": [{**e, "who": [o for o in e.get("who", []) if o["name"] != "*"] if e.get("who") else []} for e in excluded],
        "unmet": unmet,
        "warnings": day_warnings,
        "notes": day.get("notes") or {},
        "tips": day.get("tips") or [],
        "totals": {"attractions": len(done), "wait_min": total_wait, "walk_min": total_walk,
                   "typical_wait_min": baseline, "saved_min": max(0, baseline - total_wait)},
    }


def _public_step(s):
    out = {k: v for k, v in s.items() if k not in ("a", "pos")}
    for k in ("start", "end", "show_time"):
        if out.get(k) is not None:
            out[k] = clock(out[k])
    if out.get("window"):
        out["window"] = [clock(x) for x in out["window"]]
    if s.get("a") is not None:
        a = s["a"]
        out.update({"id": a["id"], "name": a["name"], "short": a.get("short", a["name"]), "land": a["land"], "type": a.get("type"),
                    "height_in": a.get("height_in"), "note": out.get("note") or a.get("status_note", "")})
    if s.get("pos") is not None:
        out["x"], out["y"] = round(s["pos"][0], 1), round(s["pos"][1], 1)
    if out.get("out"):
        out["out"] = [o for o in out["out"] if o["name"] != "*"]
    return out


# --- trip level -------------------------------------------------------------------

def booking_calendar(request, days):
    """Dates when reservations open, relative to the park days."""
    events = []
    disney_days = [d for d in days if d["operator"] == "disney" and d.get("date")]
    universal_days = [d for d in days if d["operator"] == "universal" and d.get("date")]
    flags = {f for p in request.get("party", []) for f in p.get("flags", [])}
    if disney_days:
        first = date.fromisoformat(disney_days[0]["date"])
        checkin = date.fromisoformat(request["checkin"]) if request.get("checkin") else first
        events.append({"date": (checkin - timedelta(days=60)).isoformat(), "time": "06:00", "what": "dining",
                       "verify": True})
        uses_ll = [d for d in disney_days if (d.get("ll") or "none").lower() not in ("none", "no", "")
                   or any(s.get("lane", "").startswith("ll_") for s in d["steps"])]
        if uses_ll:
            if request.get("disney_resort"):
                events.append({"date": (checkin - timedelta(days=7)).isoformat(), "time": "07:00", "what": "ll_resort",
                               "verify": True})
            else:
                for d in uses_ll:
                    events.append({"date": (date.fromisoformat(d["date"]) - timedelta(days=3)).isoformat(),
                                   "time": "07:00", "what": "ll_offsite", "park": d["park_name"], "verify": True})
        if "das" in flags:
            events.append({"date": (first - timedelta(days=30)).isoformat(), "time": "", "what": "das", "verify": True})
    if universal_days:
        first = date.fromisoformat(universal_days[0]["date"])
        if any(d.get("express") for d in universal_days):
            events.append({"date": "", "time": "", "what": "express_buy", "verify": True})
        if "das" in flags:
            events.append({"date": (first - timedelta(days=14)).isoformat(), "time": "", "what": "iac", "verify": True})
    today = date.today().isoformat()
    for e in events:
        if e["date"] and e["date"] <= today:
            e["open_now"] = True
    events.sort(key=lambda e: e["date"] or "0")
    return events


def plan(request):
    parks = load_parks()
    people = prepare_party(request.get("party", []))
    if not people:
        raise ValueError("The request needs a 'party' list (name, age, height_cm, flags).")
    prefs = {k: request.get(k) for k in ("pace", "crowd", "stroller", "single_rider_ok", "split_ok", "extras")}
    prefs = {k: v for k, v in prefs.items() if v is not None}
    warnings, days = [], []
    for day in request.get("days", []):
        park = find_park(parks, day["park"])
        days.append(plan_day(park, dict(day), people, prefs, warnings))
    return {
        "client": request.get("client", ""),
        "lang": request.get("lang", "en"),
        "created": date.today().isoformat(),
        "party": [{k: v for k, v in p.items() if not k.startswith("_")} for p in people],
        "prefs": prefs,
        "disney_resort": request.get("disney_resort"),
        "hotel": request.get("hotel", ""),
        "days": days,
        "bookings": booking_calendar(request, days),
        "warnings": warnings,
        "notes": request.get("notes", []),
    }


def park_info(park, people=None):
    """Compact attraction list for Claude, with who can ride when a party is given."""
    rows = []
    for a in park["attractions"]:
        row = {k: a.get(k) for k in ("id", "name", "land", "type", "height_in", "thrill", "tags", "lane", "peak",
                                     "rope", "single_rider", "access", "status", "status_note") if a.get(k) not in (None, [], "")}
        if people:
            riders, out, switch = evaluate(a, people, set())
            row["riders"] = [p["name"] for p in riders]
            if out:
                row["cannot"] = [o for o in out if o["name"] != "*"]
            if switch:
                row["rider_switch"] = True
        rows.append(row)
    return {"park": park["id"], "name": park["name"], "resort": park["resort"], "operator": park["operator"],
            "ll_tiers": park.get("ll_tiers", False), "data_checked": park.get("data_checked"),
            "tips": park.get("tips", []), "attractions": rows}
