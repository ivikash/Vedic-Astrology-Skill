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
# other 8 are corner triangles. Centroids below are the average of each
# region's vertices.
CENTROIDS = {
    1: (4, 8), 2: (1.33, 12), 3: (4, 14.67), 4: (8, 12), 5: (12, 14.67),
    6: (14.67, 12), 7: (12, 8), 8: (14.67, 4), 9: (12, 1.33), 10: (8, 4),
    11: (4, 1.33), 12: (1.33, 4),
}
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
        r, c = CENTROIDS[h]
        sign = sign_for_house(lagna_sign, h)
        lines = [SIGN3[sign]]
        if h == 1:
            lines.append('ASC')
        if houses[h]:
            lines.append(','.join(houses[h]))
        for i, line in enumerate(lines):
            place(line, r + (i - (len(lines) - 1) / 2) * 0.9, c)

    body = '\n'.join(''.join(row) for row in grid)
    return title + '\n\n' + body


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


if __name__ == '__main__':
    main()
