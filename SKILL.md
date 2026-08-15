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
1. Date of birth, DD/MM/YYYY
2. Exact local birth time with AM/PM
3. Birthplace: city, state/region, country

Do not ask about career, money, relationships, family, or past events up front -
that biases the audit. Wait for the chart before discussing any of that.

If the user volunteers that the birth time is approximate or unknown (even
though it's no longer asked by default): still compute the chart, but flag
the Ascendant, D9, and house placements as lower-confidence, and skip
minute-sensitive claims (exact house cusps, D10). Dasha timing from the
Moon's nakshatra is unaffected by an inexact birth time as long as the date
is right - only the Ascendant/houses degrade.

## Step 2 - Chart style preference

Default to **North Indian** style (house-fixed diamond) for every chart you
print, without asking - most users don't have a preference and North Indian
is the more common default. Only switch to **South Indian** style
(sign-fixed grid) if the user asks for it, mentions it by name, or says
North Indian is hard to read. Once a user states a preference in a
conversation, keep using it for the rest of that conversation without
re-asking.

## Step 3 - Resolve place to lat/lon/UTC offset

The script takes numeric `--lat`, `--lon`, `--utc-offset` - it does no geocoding.
Resolve these yourself using your own knowledge (or WebFetch/search if unsure):
- Latitude/longitude of the city (a few decimal places is enough).
- The **historical** UTC offset actually in effect on that date - not today's
  offset. Check for since-changed timezone boundaries, and for DST/War Time
  rules that applied historically (e.g. US pre-1966 patchwork DST, USSR/Russia's
  multiple offset changes, India's brief 1941-45 offset). State the resolved
  offset and DST status explicitly before calculating.

## Step 4 - Run the calculator

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
- `avkahada_chakra` - the standard birth-details summary panel (the same
  fields AstroSage-style kundli software calls "Avkahada Chakra"): Paya,
  Varna, Yoni, Gana, Vasya, Nadi (nakshatra/rashi classifications used in
  guna-milan matching), Dasa Balance at birth (Y/M/D), Lagna + Lagna Lord,
  Rasi + Rasi Lord, Nakshatra-Pada, Nakshatra Lord, Julian Day, SunSign
  (Indian sidereal vs Western tropical), Ayanamsha value, Obliquity, and
  Sidereal Time at birth. `ghatak_malefics` is deliberately `null` - that
  technique isn't implemented (don't guess at it; say so if asked).
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

## Step 5 - Always print the standard summary before interpreting

**Before giving any interpretation, prediction, or answer to the user's
actual question**, always print this summary block, in this order, for
every fresh chart run (not just the first time in a conversation - repeat it
whenever you recompute or re-derive the chart with different inputs):

1. **Basic details** - name (if given), date, time, UTC offset, place,
   lat/lon - i.e. the resolved inputs from Steps 1-3.
2. **Tithi** (and the rest of `panchang_at_birth` - Karana, Nitya Yoga, Vara).
3. **Avkahada Chakra** table - every field from the `avkahada_chakra` JSON
   section, labeled the way that section's comment describes. Explicitly
   note that `Ghatak (Malefics)` is not implemented rather than omitting it
   silently.
4. **The D1 chart and the D9 (Navamsa) chart**, both - rendered with:
   ```bash
   python3 scripts/render_chart.py --chart /tmp/chart.json --style north --divisional d1
   python3 scripts/render_chart.py --chart /tmp/chart.json --style north --divisional d9
   ```
   (`--style south` if that's the user's stated preference per Step 2).
5. **The Dasha** - the full Mahadasha timeline (table form is fine) and the
   `current_dasha` (Mahadasha/Antardasha/Pratyantardasha), clearly marked as
   "current."
6. **Current Dasha theme** - run the current Mahadasha-Antardasha-
   Pratyantardasha stack through Step 6's **Life-area coverage checklist**
   (health, wealth, money/income, job, business, relationship, legal
   settlement, big purchases, relocation). This is genuine interpretation, so
   it follows Step 6's rules in full - **Moderate** confidence at the
   Mahadasha/Antardasha level, **Speculative** at Pratyantardasha - and every
   claim must trace to a real placement (`rules_houses`, dignity,
   `house_from_lagna`), not a generic "this planet means X" statement.
7. **This month** - a short thematic read of `this_month_moon_calendar` and
   `this_month_fast_planets` (which signs/houses the Moon and any fast
   planets move through this month). Per Step 6, this is the **lowest**-
   confidence layer - texture, not events.
8. **Today** - the single most specific layer: today's date's position in
   `this_month_moon_calendar` (which sign/house the Moon is in today) plus
   `current_transits` for any planet that changed sign today per
   `this_month_fast_planets`. Frame as thematic texture for the day, same
   confidence caveat as monthly, one level more specific.

**Format items 6-8 as one short paragraph per life-area (or per notable
transit for items 7-8), not a table.** Each paragraph leads with the finding
first, then the reasoning that supports it - the update, then why, in that
order, every time. Write the finding as a plain claim ("no dasha lord touches
the 7th house" is itself a finding, not a gap to apologize for), then back it
with the specific field it traces to.

Hold every paragraph to this writing bar, no exceptions:
- **Active voice, clear actor.** "Mars rules the 6th house" not "the 6th
  house is ruled by Mars."
- **No em-dash characters.** Use a period, comma, or a spaced hyphen " - ".
- **No hedging or superlative words** (should, might, could, generally,
  significant, robust, comprehensive, seamless, etc.) - state the finding or
  state that there's no finding; don't soften either one.
- **Quantify what the data gives you** - exact dates, house numbers, degrees
  - instead of vague words like "narrow window" or "some transits."
- **Cut fluff.** A tight two-sentence paragraph beats a padded five-sentence
  one. If a life-area genuinely has nothing behind it, one sentence saying so
  is the whole paragraph.

Only after all eight are printed should you move on to answering whatever
else the user actually asked (a life-events audit, a specific question,
remedies, etc.) per Step 6. If the user asks a narrow follow-up in an
existing conversation where this summary was already printed for the same
chart, you don't need to reprint it - only reprint after a genuinely
new/changed calculator run. If asked again later in the same day for
"today's" reading specifically, items 6-8 are the ones that can go stale
fastest (dasha almost never within a conversation, but "today" the moment
the date rolls over) - recompute with a fresh `--now`-less run if there's
any doubt the data is still current.

## Step 6 - Interpret, honestly

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

### Life-area coverage checklist

When asked for an elaborate reading (or whenever doing the Step 5 item 6-8
predictions in full), walk through every relevant area below rather than
writing one generic paragraph. For each area: identify its house(s)/karaka,
then check whether the *current* dasha lords (Mahadasha/Antardasha/
Pratyantardasha) occupy or rule that house, and whether `current_transits`
currently touches it - state the finding either way, including **"no strong
signal from the current dasha/transits for this area"** when that's true.
Silence on an area someone asked about reads as "I forgot it"; an explicit
no-signal statement is the honest version of covering it.

| Life area | Houses / karakas |
|---|---|
| Health | 6th house (disease), 8th house (chronic/longevity), Lagna + Lagna lord (vitality), Moon (mind) |
| Wealth / savings | 2nd house (accumulated wealth, family resources), its lord |
| Money / income flow | 11th house (gains, income), its lord |
| Job / employment | 10th house (career, status), 6th house (service specifically), 10th lord |
| Business | 7th house (trade/partnership) with 10th (career) and 3rd (self-effort); 11th for gains |
| Relationship / marriage | 7th house, Venus, Jaimini Darakaraka, 7th lord |
| Legal settlement / disputes | 6th (litigation), 8th (complications), 12th (losses/settlement), 7th (the other party in a contract) |
| New purchases (vehicle, big-ticket) | 4th house (property/vehicle/comfort), 11th (fulfillment of desire funding it) |
| Relocation / travel | 3rd (short travel), 4th (change of residence), 9th (long-distance), 12th (foreign land/settling abroad) |

This checklist is classical significations, not a new calculation - every
finding still has to trace to a real field (`rules_houses`, `house_from_lagna`,
`current_transits`, dignity) per the Never Invent rule above. If the natal
chart or current dasha genuinely has nothing to say about an area (e.g. no
dasha lord touches the 7th and no transit is there either), that's the
honest answer for that area - don't manufacture a generic Venus-means-love
line just to fill the section.

## Step 7 - Remedies (Upaya), mantra, and why

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
  yogas, Ghatak Malefics - see Step 4's note on gaps): say explicitly that
  this isn't implemented yet rather than approximating it by hand.
- **`render_chart.py` labels look cramped or cut off**: chart cells are
  small by design (12 houses in a fixed diagram) - the script already drops
  the combust `(c)` tag from in-chart labels and reports it in a footer line
  instead; if you hit a similar overflow with a new label type, extend the
  script's footer pattern rather than hand-editing its ASCII output.

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
- `avkahada_chakra`'s Varna/Vasya/Yoni/Gana/Nadi/Paya are standard classical
  nakshatra/rashi lookup tables (the same ones guna-milan/Ashtakoot matching
  uses) - cross-checked against a real AstroSage Avkahada Chakra panel for
  one birth chart and matched on every field. Vasya's classical treatment
  splits Sagittarius and Capricorn by degree (0-15/15-30); the script
  implements that split but doesn't attempt finer sub-degree splits some
  sources apply elsewhere. Ayanamsha and Sidereal Time can differ from other
  software by a couple of arc-seconds/seconds (apparent-vs-mean sidereal time
  and slightly different Lahiri epoch conventions) - expected cross-software
  variance, not an error.
