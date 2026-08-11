# Astrology Skill

A Vedic (sidereal, Lahiri ayanamsha) astrology calculator, built as a Claude
Code skill. It computes a full chart from a date of birth, time, and place,
and separates that calculation from interpretation:

- `scripts/astro_calc.py` does real math against the Swiss Ephemeris and
  emits one JSON blob. It never guesses - if it doesn't know something
  precisely, it doesn't output it.
- `SKILL.md` tells Claude how to collect birth details, run the script,
  read its output, and interpret it honestly (confidence tiers, review
  controls for past-event claims, what the chart can and can't resolve).
- `references/remedies.md` is a per-planet upaya/mantra reference with the
  classical reasoning ("why") behind each remedy, used when a reading
  includes recommendations.

This exists because daily-horoscope-style astrology tools tend to blur "here
is a real planetary position" with "here is a vague, unfalsifiable
prediction." This skill keeps those two things in separate files.

## Requirements

- Python 3.9+
- `pyswisseph` (installed via `requirements.txt`)

No external ephemeris data files are required - `pyswisseph` falls back to
its built-in Moshier model when Swiss Ephemeris `.se1` files aren't found,
and that's accurate to arc-seconds for 20th-21st century dates, which is
what this skill is meant for. (Verified against an independently-known
chart: Moon position matched to the arc-second, Vimshottari dasha balance
matched to the day.)

## Setup

```bash
cd astrology-skill
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

## Usage

The script takes numeric birth inputs only - it does not geocode place names
or resolve historical timezones itself. That resolution step is intentionally
left to whoever calls it (a human, or Claude following `SKILL.md`), because
getting the *historical* UTC offset right (accounting for DST/timezone
changes that may no longer apply today) matters more than the ephemeris math
and shouldn't be silently automated.

```bash
python3 scripts/astro_calc.py \
  --name "Jane Doe" \
  --date 1990-01-01 \
  --time 00:00 \
  --utc-offset 5.5 \
  --lat 28.6139 --lon 77.2090 \
  --place "New Delhi, Delhi, India" \
  --forward-years 8 \
  --out chart.json
```

Optional flags:
- `--now YYYY-MM-DDTHH:MM` (UTC) - treat this instant as "now" instead of the
  real current time. Useful for reproducing a past reading.
- `--dasha-lookup YYYY-MM-DDTHH:MM` (UTC) - resolve the full
  Mahadasha/Antardasha/Pratyantardasha stack for any past or future instant,
  independent of `--now`.
- `--forward-years N` (default 8) - how far ahead the Jupiter/Saturn/Rahu/
  Ketu house-transit scan looks.

## Output structure

One JSON object with:

| Key | Contents |
|---|---|
| `panchang_at_birth` | Tithi, Karana, Nitya Yoga, Vara at birth |
| `natal_chart` | Ascendant, house lords, all 9 grahas (sign, degree, nakshatra, pada, house, dignity, combustion, retrograde, navamsa sign/dignity/vargottama, houses ruled) |
| `jaimini_chara_karakas` | Atmakaraka through Darakaraka |
| `vimshottari_dasha_timeline` | Every Mahadasha for one full 120-year cycle, each with its 9 Antardashas attached |
| `current_dasha` | Mahadasha/Antardasha/Pratyantardasha active right now (or at `--now`) |
| `dasha_lookup` | Same, for the instant passed to `--dasha-lookup` |
| `sade_sati_status` | Whether transiting Saturn is currently in Sade Sati or Ashtama Shani relative to natal Moon |
| `current_transits` | Live planetary positions and the natal house each falls in |
| `this_month_moon_calendar` / `this_month_fast_planets` | Moon's sign-by-sign path this month; Sun/Mercury/Venus/Mars sign changes this month |
| `forward_<N>yr_house_transit_scan` | Every future Jupiter/Saturn/Rahu/Ketu sign-ingress date, tagged with the natal house it lands in |

## What this does NOT compute

Known, deliberate gaps - ask for these to be added if you need them, rather
than assuming a reading covers them:

- D10 (Dasamsa/career), D7, D12, D60, or any divisional chart beyond D9
- Planetary aspects (drishti)
- Classical yoga detection (Gajakesari, Neecha-bhanga, Raja/Dhana yogas,
  Panch Mahapurusha, etc.)
- Shadbala (strength scoring) or Ashtakavarga
- Gemstone recommendations (deliberately excluded - see
  `references/remedies.md`; this needs an in-person practitioner)
- Geocoding of place names or historical timezone lookup (by design - see
  Usage above)

## Method notes

- Ayanamsha: Lahiri. Houses: Whole Sign. Dasha: Vimshottari (Moon-nakshatra
  based). Rahu is the mean node; Ketu is exactly 180° from Rahu.
- Chara karakas use the 7-graha scheme (Sun-Saturn), not the 8-karaka variant
  including Rahu.
- Combustion orbs are approximate classical values, not adjusted for
  direct/retrograde narrowing.
- Panchang's Vara (weekday) uses the local calendar date, not a sunrise-based
  day boundary - a simplification worth knowing about if you need
  sunrise-precise Panchang.

## Using this as a Claude Code skill

This lives at `~/workspace/astrology-skill/` rather than `.claude/skills/`,
so Claude Code won't auto-discover it as an invocable `/astrology-skill`
command. To make it discoverable, copy or symlink this directory into
`~/.claude/skills/astrology-skill` (global) or
`<project>/.claude/skills/astrology-skill` (project-scoped).
