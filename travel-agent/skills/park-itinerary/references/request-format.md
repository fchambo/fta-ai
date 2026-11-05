# Park plan request

`ta park-plan` takes one JSON file for the whole trip. Attractions can be given by `id` (from `ta park-info`) or by name ("seven dwarfs", "rise"). Times use 24 h (`"09:30"`) or `"9:30 pm"`.

```json
{
  "client": "Familia Pérez",
  "lang": "es",
  "disney_resort": true,
  "checkin": "2026-12-13",
  "pace": "normal",
  "crowd": "high",
  "stroller": true,
  "split_ok": true,
  "single_rider_ok": false,
  "extras": true,
  "notes": ["Lleven ponchos y una muda de ropa para los chicos."],
  "party": [
    {"name": "Juan", "age": 42},
    {"name": "María", "age": 40, "flags": ["claustrophobic", "motion_sickness"]},
    {"name": "Tomás", "age": 9, "height_cm": 132, "skip": ["tea-party"]},
    {"name": "Sofi", "age": 4, "height_cm": 102, "avoid": ["dark"]}
  ],
  "days": [
    {
      "date": "2026-12-14", "park": "mk", "open": "09:00", "close": "22:00",
      "early_entry": true, "arrive": "08:30", "leave": "22:00", "crowd": "high",
      "ll": "multi",
      "lightning": [{"attraction": "peter-pan", "time": "10:30"}],
      "must": ["7dmt", "tron", "space-mountain"],
      "nice": ["haunted-mansion", "pirates", "buzz"],
      "skip": ["speedway"],
      "closed": [],
      "fixed": [
        {"name": "Almuerzo en Be Our Guest", "time": "12:30", "minutes": 60, "at": "belle", "kind": "meal", "note": "Reserva #12345"},
        {"attraction": "happily-ever-after", "time": "21:00"}
      ],
      "break": {"start": "13:30", "end": "16:30"},
      "tips": ["Si llueve, PhilharMagic y Carousel of Progress son buenas opciones bajo techo."],
      "notes": {"tiana": "Se mojan: lleven ponchos."}
    }
  ]
}
```

## Trip fields

| Field | Meaning |
|---|---|
| `lang` | Client language for the PDF (`en` / `es`) |
| `disney_resort` | Staying at a Disney hotel: Lightning Lane booking opens 7 days before `checkin` for the whole stay (otherwise 3 days before each park day) |
| `pace` | `relaxed` (longer meals, an afternoon rest, slower walking), `normal`, `intense` |
| `crowd` | Default crowd level: `low`, `moderate`, `high`, `peak` (holidays, Christmas–New Year, spring break). A day can override it |
| `stroller` | Slower walking speed |
| `split_ok` | Let the adults do intense rides with Rider Switch / Child Swap while kids wait (default true) |
| `single_rider_ok` | Use single-rider lines when every rider is 10+ |
| `extras` | Fill free time with other rides the whole group can do (default true) |
| `notes` | Extra tips for the PDF cover, in the client's language |

## Travelers

`name`, `age` (leave it out for adults if unknown), `height_cm` or `height_in` (required for kids under 12), and optionally `flags`, `avoid` (attraction tags) and `skip` (attraction ids).

| Flag | Rules out |
|---|---|
| `claustrophobic` | `enclosed` (tight restraints, closed vehicles or rooms: Flight of Passage, Mission: SPACE, TRON, Rise of the Resistance) |
| `motion_sickness` | `sim` and `spin` (screens with motion, spinning rides) |
| `fear_dark` | `dark` |
| `fear_heights` | `heights`, `drops` |
| `scared_easily` | `scary` |
| `no_coasters` | `coaster` |
| `no_wet` | `wet` |
| `sensory` | `loud`, `fire` (noise-sensitive travelers) |
| `mild_only` / `no_thrill` | Thrill level above 1 / above 0 |
| `pregnant` | Thrill above 1, plus coasters, simulators, drops, spinning, bumpy rides and launches |
| `back_neck` | Thrill above 1, coasters, bumpy rides and launches |
| `wheelchair` | Uses a wheelchair or ECV but can transfer: skips rides that require walking or stairs |
| `no_transfer` | Must stay in the wheelchair: only wheelchair-accessible attractions |
| `limited_walking` | Like `wheelchair` for access, and slower walking |
| `das` | Candidate for Disney DAS or Universal AAP: adds the registration step to the booking calendar |

Attraction tags: `coaster`, `launch`, `drops`, `spin`, `sim`, `3d`, `dark`, `enclosed`, `heights`, `scary`, `loud`, `fire`, `wet`, `boat`, `bumpy`, `backwards`, `animals`, `interactive`, `stairs`, `standing`. Thrill: 0 calm, 1 mild, 2 moderate, 3 intense.

Kids under 14 who can't ride are covered by **Rider Switch / Child Swap** when there are at least two adults: the plan adds the second ride time and says who waits. With only one adult, rides that leave a child alone are excluded.

## Day fields

| Field | Meaning |
|---|---|
| `park` | `mk`, `epcot`, `hs`, `ak`, `usf`, `ioa`, `epic` |
| `open`, `close` | Official hours for that date (check them) |
| `early_entry` | Hotel-guest early entry: arrival defaults to 30 min before opening |
| `arrive`, `leave` | When the group gets there and leaves (defaults: 15 min before opening, closing time) |
| `ll` | Disney: `none`, `multi`, `single`, `multi+single`, `premier`. With `multi` and no `lightning`, the planner suggests 3 return times (tiers respected at EPCOT, HS and AK) |
| `lightning` | Booked return times: `{"attraction", "time", "window"}`, with a 60 min window by default |
| `express` | Universal: `unlimited` or `once` |
| `park_to_park` | Universal: allows the Hogwarts Express |
| `must`, `nice`, `skip` | Priorities for this day. Must-dos get scheduled first |
| `closed`, `open_anyway` | Overrides after checking refurbishments |
| `fixed` | Dining, shows and fireworks at a set time: `name` or `attraction`, `time`, `minutes`, `at` (an attraction or land, for the map), `kind` (`meal` / `show`), `note`, `arrive_early` |
| `break` | Leaves the park for a hotel break: `{"start", "end"}` |
| `after_fireworks` | Keep riding after the fireworks (default: the day ends with them) |
| `tips`, `notes` | Day tips and per-attraction notes for the PDF, in the client's language |

## Assigning parks to days

1. **Hard constraints first**: Magic Kingdom party nights (the park closes at 6 p.m. for day guests), refurbishments of a must-do, dining reservations already booked, Park Hopper / Park-to-Park rules, arrival and departure days.
2. **Busiest days are the worst for headliners**: Epic Universe, Magic Kingdom and Hollywood Studios go on the least crowded days available. Weekends and holidays are better for EPCOT (except during festivals) or Animal Kingdom.
3. **Alternate heavy and light days**: Epic Universe or MK, then a lighter or shorter park. After 3 park days in a row with kids under 8, suggest a pool or rest day.
4. **Early Entry and Early Park Admission** are worth most at MK (Fantasyland), HS (Slinky or Rise) and Epic Universe / IOA (Hagrid's). Use them on those days.
5. **Animal Kingdom** closes early: plan it as a morning park, and mornings are also best for the Safari.
6. **Universal with a Park-to-Park ticket**: one day across USF and IOA (rope drop Hagrid's, then the Hogwarts Express) beats two half days for families short on time.
7. **Group by Lightning Lane window**: off-site guests book 3 days ahead, so their first Disney day has the most competition. Put the park with the fewest must-dos there.
8. **Arrival day**: no headliner parks. Disney Springs or a short evening at EPCOT works well.
