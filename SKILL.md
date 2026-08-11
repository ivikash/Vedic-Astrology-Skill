---
name: astrology-skill
description: Compute a real sidereal (Lahiri) Vedic astrology chart from a date of birth, time, and place - natal chart, navamsa, Vimshottari dasha down to Pratyantardasha, Jaimini karakas, Panchang, Sade Sati status, current transits, monthly Moon calendar, and a multi-year transit scan - then interpret it honestly and recommend upaya/mantra with classical reasoning. Use when the user gives birth details and wants a chart, a life-events audit, dasha/transit timing, a daily/monthly reading, or remedies.
---

# Vedic Astrology Skill

This skill separates **calculation** from **interpretation**. `scripts/astro_calc.py`
does real ephemeris math (Swiss Ephemeris, sidereal Lahiri ayanamsha) and emits
JSON. You (Claude) read that JSON and write the interpretation. Never invent a
degree, placement, yoga, dasha, or transit that isn't in the script's output -
if something isn't there, say so and, if needed, extend the script rather than
guessing.

## Step 1 - Collect birth details

Ask only for what's needed, and only if not already given:
1. First name or initials (optional)
2. Date of birth, DD/MM/YYYY
3. Exact local birth time with AM/PM
4. Birthplace: city, state/region, country
5. Whether the birth time is exact, approximate, or unknown
6. Preferred pronouns (optional)

Do not ask about career, money, relationships, family, or past events up front -
that biases the audit. Wait for the chart before discussing any of that.

If birth time is approximate or unknown: still compute the chart, but flag the
Ascendant, D9, and house placements as lower-confidence, and skip minute-sensitive
claims (exact house cusps, D10). Dasha timing from the Moon's nakshatra is
unaffected by an inexact birth time as long as the date is right - only the
Ascendant/houses degrade.

## Step 2 - Resolve place to lat/lon/UTC offset

The script takes numeric `--lat`, `--lon`, `--utc-offset` - it does no geocoding.
Resolve these yourself using your own knowledge (or WebFetch/search if unsure):
- Latitude/longitude of the city (a few decimal places is enough).
- The **historical** UTC offset actually in effect on that date - not today's
  offset. Check for since-changed timezone boundaries, and for DST/War Time
  rules that applied historically (e.g. US pre-1966 patchwork DST, USSR/Russia's
  multiple offset changes, India's brief 1941-45 offset). State the resolved
  offset and DST status explicitly before calculating.

## Step 3 - Run the calculator

```bash
cd ~/workspace/astrology-skill
pip install -r requirements.txt   # first time only: installs pyswisseph
python3 scripts/astro_calc.py \
  --name "..." --date YYYY-MM-DD --time HH:MM --utc-offset 5.5 \
  --lat 28.6139 --lon 77.2090 --place "City, Region, Country" \
  --forward-years 8 --out /tmp/chart.json
```

`--time` is 24-hour local clock time at birth. `--utc-offset` is hours east of
UTC (negative for west, e.g. `-7` for Pacific Daylight Time - remember to use
the offset that was actually in effect, including DST, on that historical date).
`--forward-years` controls how far the Jupiter/Saturn/Rahu/Ketu house-transit
scan looks ahead (default 8; raise it if the user asks about a distant window).
Add `--now YYYY-MM-DDTHH:MM` (UTC) only to reproduce a past reading for a fixed
date - omit it to use the real current moment.

Add `--dasha-lookup YYYY-MM-DDTHH:MM` (UTC) whenever a question is about a
specific past or future period rather than "now" - it resolves the full
Mahadasha/Antardasha/Pratyantardasha stack for that instant independently of
`--now`, so you don't have to hand-derive antardasha windows for eras like a
future Venus Mahadasha the way earlier readings in this project had to.

Then read the JSON (`Read` the `--out` file, or capture stdout if you omit
`--out`). Its top-level sections:

- `panchang_at_birth` - Tithi, Karana, Nitya Yoga, and Vara (weekday) at
  birth, from local calendar date (not sunrise-based - a simplification).
- `natal_chart` - ascendant, `house_lords` (sign lord of each house), and all
  9 grahas with sign/degree/nakshatra/pada/house (Whole Sign)/`rules_houses`/
  retrograde/dignity/combustion/navamsa sign/**navamsa dignity**/
  **vargottama flag**/navamsa house. Vargottama (D1 sign == D9 sign) is a real
  strength signal - check it for every planet, not just the ones that seem
  obviously placed.
- `jaimini_chara_karakas` - Atmakaraka through Darakaraka, ranked by degree
  among the 7 classical grahas.
- `vimshottari_dasha_timeline` - every Mahadasha from birth for one full
  120-year cycle, each with its exact dates **and its 9 Antardashas already
  attached** - no need to compute antardashas separately for any era.
- `current_dasha` - Mahadasha, Antardasha, *and* Pratyantardasha active as of
  now (or `--now`), plus every Pratyantardasha of the current Antardasha.
- `dasha_lookup` - same MD/AD/PD structure, for whatever instant you passed to
  `--dasha-lookup`.
- `sade_sati_status` - whether transiting Saturn is currently in the
  Sade Sati window (12th/1st/2nd from natal Moon) or Ashtama Shani (8th from
  natal Moon), computed from real current Saturn position.
- `current_transits` - where every planet is right now, and which natal house
  (from the Lagna) that falls in.
- `this_month_moon_calendar` / `this_month_fast_planets` - Moon's sign-by-sign
  path this month, and Sun/Mercury/Venus/Mars sign changes this month.
- `forward_<N>yr_house_transit_scan` - every future sign-ingress date for
  Jupiter, Saturn, Rahu, Ketu, each tagged with the natal house it lands in.

If a question needs something not in this JSON (e.g. a future year outside
`--forward-years` - just rerun with a bigger value - or a D10/D7/D12 chart,
planetary aspects, or yoga detection, none of which are implemented), say so
and extend `astro_calc.py` with a new function rather than estimating by hand.

## Step 4 - Interpret, honestly

These rules held throughout this whole line of work and apply to every reading
you produce from this skill's output:

- **Never invent.** Every claim must trace to a specific field in the JSON
  (a sign, a degree, a dasha date, a transit). If you can't point to the field,
  don't make the claim.
- **Rate confidence per claim**: Strong (classical, well-attested placement,
  e.g. a planet in its own sign or a dignified karaka in a relevant house),
  Moderate (directionally solid but the window is wide or the reading layers
  interpretation on top of a real placement), Speculative (fine antardasha-level
  timing, folk techniques, anything resting on a single weak signal).
- **Past-claim audits get a review control.** When producing testable claims
  about the past, give each one a Yes/Partly/No control the user can answer
  honestly - don't let the claim be rewritten to fit whatever they say.
- **Dasha gives eras, transit gives sharper windows - use both.** Mahadasha/
  Antardasha tell you which multi-year theme is active; the forward
  house-transit scan tells you which specific years within that era carry
  the matching planetary weight. State both layers and where they do/don't
  overlap.
- **Daily and monthly readings are the lowest-confidence layer.** Ground them
  in the actual Moon-sign-of-the-day/week and any fast-planet sign changes in
  `this_month_*`, framed as thematic texture - not as concrete event
  predictions ("you'll get a call", "avoid signing X").
- **Know what the chart cannot resolve.** House/sign astrology speaks in
  themes (foreign land, home, career, partnership), not in named cities,
  specific people, or guaranteed dates. If a question asks for a resolution
  the technique doesn't support (e.g. choosing between two similar cities),
  say so directly rather than forcing a false-precision answer.
- **Treat astrology as an interpretive tradition, not a proven predictive
  science**, and say so when giving readings, especially remedies (upay).

## Step 5 - Remedies (Upaya), mantra, and why

`references/remedies.md` is the remedy knowledge base - Read it rather than
generating upaya/mantra from memory. For each of the 9 grahas plus a
Sade Sati/Ashtama Shani protocol, it gives: when the remedy is actually
relevant, the upaya itself (donation items, day, deity, practice), a mantra,
and a **why** - the classical reasoning connecting the remedy to the planet's
signification, not just the remedy in isolation.

Selection rule (also stated in that file, worth repeating): don't hand the
user all nine grahas' remedies. Pick 2-4, prioritized by (1) the current
Mahadasha/Antardasha lord, (2) any planet that's debilitated, combust, or in
the 6th/8th/12th, (3) an active `sade_sati_status`, (4) whatever the user's
actual question is about. Always restate the file's disclaimer in your own
words - traditional practice, not a guaranteed fix, not a substitute for
medical/legal/financial/mental-health care - and never generate a specific
gemstone recommendation; point to an in-person practitioner for that.

## Troubleshooting and robustness

- **Before running the script, echo back your resolved inputs** - date, time,
  UTC offset (with DST reasoning if relevant), lat/lon - and let the user
  correct them. A wrong timezone resolution is the single most likely source
  of a wrong chart, and it fails silently (the script has no way to know your
  offset is wrong).
- **`pip install -r requirements.txt` failing**: try `pip3 install` or
  `python3 -m pip install --user pyswisseph`; if the environment is
  externally managed, use a venv (`python3 -m venv .venv && source
  .venv/bin/activate && pip install -r requirements.txt`).
- **`--dasha-lookup` or a transit question falls outside the computed
  120-year Vimshottari cycle from birth** (very early/late in life, or a date
  before birth): `dasha_lookup`/`current_dasha` will be `null` in the JSON.
  Say so rather than guessing what dasha would apply.
- **Ambiguous or historical place names/borders** (cities that changed
  country, renamed regions, pre-independence place names): resolve to the
  coordinates and the *de facto* civil timezone at the time, state your
  reasoning, and flag lower confidence if genuinely uncertain rather than
  picking silently.
- **Malformed `--date`/`--time` input** (e.g. 12-hour time without conversion,
  wrong separators): convert explicitly before calling the script - it expects
  strict `YYYY-MM-DD` and 24-hour `HH:MM`.
- **A question needs a field the script doesn't compute** (D10, aspects,
  yogas - see Step 3's note on gaps): say explicitly that this isn't
  implemented yet rather than approximating it by hand.

## Notes on method

- Ayanamsha: Lahiri. Houses: Whole Sign. Dasha: Vimshottari (Moon-nakshatra
  based). D9 (Navamsa) is computed exactly from the D1 degree - no D10 is
  computed by this script; if career timing needs D10, that would require
  adding a Dasamsa function (odd/even-sign counting rule) rather than
  estimating it.
- Rahu is the mean node; Ketu is derived as exactly 180° from Rahu.
- Chara karakas use the standard 7-graha scheme (Sun through Saturn), ranked by
  degree-in-sign, not the 8-karaka variant that includes Rahu.
- Combustion orbs are approximate classical values (see `COMBUSTION_ORB` in the
  script) and don't distinguish direct/retrograde orb narrowing.
- The script needs no external ephemeris files - pyswisseph's built-in Moshier
  model is used automatically when Swiss Ephemeris data files aren't found, and
  it's accurate to arc-seconds for the 20th-21st century date range this skill
  is meant for.
