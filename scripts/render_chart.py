#!/usr/bin/env python3
"""
Render a D1 (Rasi) or D9 (Navamsa) chart from astro_calc.py's JSON output as
an ASCII diagram, in either North Indian (house-fixed diamond) or South
Indian (sign-fixed grid) style.

This does no astrology math of its own - it only lays out planets/signs that
astro_calc.py already computed, at positions derived from exact geometry (see
the North Indian vertex derivation in HOUSE_POLYGONS below), not hand-drawn
ASCII art.
"""
import argparse
import json

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
         'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
ABBR2 = {'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
         'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke'}
SIGN3 = {s: s[:3] for s in SIGNS}
HINDI_NAME = {'Sun': 'Surya', 'Moon': 'Chandra', 'Mars': 'Mangal',
              'Mercury': 'Budh', 'Jupiter': 'Guru', 'Venus': 'Shukra',
              'Saturn': 'Shani', 'Rahu': 'Rahu', 'Ketu': 'Ketu'}
PLANET_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']


def planet_label(name, info):
    # combustion is intentionally not tagged inline (labels are already tight
    # in small chart regions) - it's reported in the footer line instead.
    lab = ABBR2[name]
    if info.get('retrograde'):
        lab += '(R)'
    return lab


def combust_footer(chart):
    combust = [n for n, info in chart['natal_chart']['planets'].items() if info.get('combust')]
    if not combust:
        return ''
    return '\nCombust (too close to Sun): ' + ', '.join(combust)


def legend_table(chart, divisional):
    natal = chart['natal_chart']
    if divisional == 'd1':
        lagna_sign = natal['ascendant']['sign']
        house_key, sign_key = 'house_from_lagna', 'sign'
    else:
        lagna_sign = natal['navamsa_ascendant_sign']
        house_key, sign_key = 'navamsa_house_from_navamsa_lagna', 'navamsa_sign'

    lagna_label = "Lagna (Ascendant)"
    lines = ['', 'Legend:', f"  {lagna_label:<20s} House {1:<3d} {lagna_sign}"]
    for name in PLANET_ORDER:
        info = natal['planets'][name]
        h = info[house_key]
        sign = info[sign_key]
        flags = []
        if divisional == 'd1' and info.get('retrograde'):
            flags.append('Retrograde')
        if divisional == 'd1' and info.get('combust'):
            flags.append('Combust')
        flag_str = f"   [{', '.join(flags)}]" if flags else ''
        label = f"{HINDI_NAME[name]} ({name})"
        lines.append(f"  {label:<20s} House {h:<3d} {sign}{flag_str}")
    return '\n'.join(lines)


def build_house_contents(chart, divisional):
    """Returns (lagna_sign, {house_number: [label,...]}) for d1 or d9."""
    natal = chart['natal_chart']
    if divisional == 'd1':
        lagna_sign = natal['ascendant']['sign']
        house_key = 'house_from_lagna'
        sign_key = 'sign'
    else:
        lagna_sign = natal['navamsa_ascendant_sign']
        house_key = 'navamsa_house_from_navamsa_lagna'
        sign_key = 'navamsa_sign'

    houses = {h: [] for h in range(1, 13)}
    for name, info in natal['planets'].items():
        h = info[house_key]
        houses[h].append(planet_label(name, info) if divisional == 'd1' else ABBR2[name])
    return lagna_sign, houses, house_key, sign_key


def sign_for_house(lagna_sign, house_num):
    start = SIGNS.index(lagna_sign)
    return SIGNS[(start + house_num - 1) % 12]


# ---------- South Indian (sign-fixed grid) ----------

SOUTH_GRID = [
    ['Pisces', 'Aries', 'Taurus', 'Gemini'],
    ['Aquarius', None, None, 'Cancer'],
    ['Capricorn', None, None, 'Leo'],
    ['Sagittarius', 'Scorpio', 'Libra', 'Virgo'],
]


def render_south(chart, divisional, title):
    lagna_sign, houses, house_key, sign_key = build_house_contents(chart, divisional)
    sign_to_house = {sign_for_house(lagna_sign, h): h for h in range(1, 13)}

    cellw = 13
    lines = [title, '']
    border = '+' + ('-' * cellw + '+') * 4
    lines.append(border)
    for row in SOUTH_GRID:
        line1 = '|'
        line2 = '|'
        for sign in row:
            if sign is None:
                line1 += ' ' * cellw + '|'
                line2 += ' ' * cellw + '|'
                continue
            h = sign_to_house[sign]
            marker = ' ASC' if h == 1 else ''
            top = f" {SIGN3[sign]} H{h}{marker}"
            planets = ','.join(houses[h])
            line1 += top.ljust(cellw) + '|'
            line2 += (' ' + planets).ljust(cellw) + '|'
        lines.append(line1)
        lines.append(line2)
        lines.append(border)
    return '\n'.join(lines)


# ---------- North Indian (house-fixed diamond) ----------
# Exact geometry on a 16x16 unit square (see conversation derivation): 2 main
# diagonals + inner diamond (side-midpoint quadrilateral) split it into 12
# regions - houses 1/4/7/10 are 4-vertex kites at the cardinal points, the
# other 8 are corner triangles.
#
# Real North Indian charts (verified against an AstroSage panel) print the
# RASHI NUMBER (1=Aries..12=Pisces) of whichever sign occupies each house
# near the region's center-ward tip, and planet abbreviations further out
# toward its outer (square-border) edge - not both stacked at the centroid,
# and with no separate "ASC" text (house 1 is always the fixed top region by
# convention). OUTER_ANCHOR is each region's own border-touching vertex/
# vertices (a side-midpoint for the 4 kite houses; the average of a square
# corner + adjacent side-midpoint for the 8 triangle houses).
CENTER = (8, 8)
OUTER_ANCHOR = {
    1: (0, 8), 2: (0, 12), 3: (4, 16), 4: (8, 16), 5: (12, 16),
    6: (16, 12), 7: (16, 8), 8: (16, 4), 9: (12, 0), 10: (8, 0),
    11: (4, 0), 12: (0, 4),
}


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


NUMBER_POS = {h: _lerp(CENTER, OUTER_ANCHOR[h], 0.25) for h in range(1, 13)}
PLANET_POS = {h: _lerp(CENTER, OUTER_ANCHOR[h], 0.65) for h in range(1, 13)}
UNIT = 16
ROW_SCALE = 2
COL_SCALE = 4
ROWS = UNIT * ROW_SCALE + 1
COLS = UNIT * COL_SCALE + 1


def _fam_a(row, col):
    return row - col


def _fam_b(row, col):
    return row + col


_LINES = [
    (_fam_a, 0, '\\'), (_fam_a, -8, '\\'), (_fam_a, 8, '\\'),
    (_fam_b, 16, '/'), (_fam_b, 24, '/'), (_fam_b, 8, '/'),
]


def render_north(chart, divisional, title):
    lagna_sign, houses, house_key, sign_key = build_house_contents(chart, divisional)

    grid = [[' '] * COLS for _ in range(ROWS)]
    for R in range(ROWS):
        for C in range(COLS):
            row, col = R / ROW_SCALE, C / COL_SCALE
            if row <= 0.001 or row >= UNIT - 0.001 or col <= 0.001 or col >= UNIT - 0.001:
                is_corner = (row <= 0.001 or row >= UNIT - 0.001) and (col <= 0.001 or col >= UNIT - 0.001)
                if is_corner:
                    grid[R][C] = '+'
                elif row <= 0.001 or row >= UNIT - 0.001:
                    grid[R][C] = '-'
                else:
                    grid[R][C] = '|'
                continue
            best = None
            for f, target, ch in _LINES:
                d = abs(f(row, col) - target)
                if best is None or d < best[0]:
                    best = (d, ch)
            if best[0] < 0.13:
                grid[R][C] = best[1]

    def place(text, r, c):
        R = round(r * ROW_SCALE)
        C = round(c * COL_SCALE) - len(text) // 2
        for i, ch in enumerate(text):
            cc = C + i
            if 0 <= R < ROWS and 0 <= cc < COLS:
                grid[R][cc] = ch

    for h in range(1, 13):
        sign = sign_for_house(lagna_sign, h)
        nr, nc = NUMBER_POS[h]
        place(str(SIGNS.index(sign) + 1), nr, nc)
        if houses[h]:
            pr, pc = PLANET_POS[h]
            lines = [','.join(houses[h][i:i + 2]) for i in range(0, len(houses[h]), 2)]
            for i, line in enumerate(lines):
                place(line, pr + (i - (len(lines) - 1) / 2) * 0.9, pc)

    body = '\n'.join(''.join(row) for row in grid)
    lagna_line = f"House 1 (Lagna/Ascendant) = {lagna_sign} (rashi {SIGNS.index(lagna_sign) + 1})"
    return title + '\n' + lagna_line + '\n\n' + body


def main():
    ap = argparse.ArgumentParser(description='Render a D1/D9 chart from astro_calc.py JSON output')
    ap.add_argument('--chart', required=True, help='path to astro_calc.py --out JSON file')
    ap.add_argument('--style', choices=['north', 'south'], default='north')
    ap.add_argument('--divisional', choices=['d1', 'd9'], default='d1')
    args = ap.parse_args()

    with open(args.chart) as f:
        chart = json.load(f)

    label = 'D1 - Rasi (Birth) Chart' if args.divisional == 'd1' else 'D9 - Navamsa Chart'
    title = f"{label} ({'North' if args.style == 'north' else 'South'} Indian style)"

    if args.style == 'north':
        print(render_north(chart, args.divisional, title))
    else:
        print(render_south(chart, args.divisional, title))
    if args.divisional == 'd1':
        footer = combust_footer(chart)
        if footer:
            print(footer)
    print(legend_table(chart, args.divisional))


if __name__ == '__main__':
    main()
