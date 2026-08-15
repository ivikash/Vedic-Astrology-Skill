#!/usr/bin/env python3
"""
Render a D1 (Rasi) or D9 (Navamsa) chart from astro_calc.py's JSON output as
an ASCII grid, in either North Indian (house-fixed) or South Indian
(sign-fixed) style. Both use the same straight-box grid layout for rendering
robustness - North Indian keeps house 1 fixed to the top-left cell with
signs rotating around it per the Ascendant; South Indian keeps each sign
fixed to its cell with houses rotating instead.

Cells show full sign names and full Hindi (English) planet names, one
planet per line, since abbreviations were hard to read - cell width and
row height are computed from the actual content, not hardcoded.

This does no astrology math of its own - it only lays out planets/signs that
astro_calc.py already computed.
"""
import argparse
import json

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
         'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
HINDI_NAME = {'Sun': 'Surya', 'Moon': 'Chandra', 'Mars': 'Mangal',
              'Mercury': 'Budh', 'Jupiter': 'Guru', 'Venus': 'Shukra',
              'Saturn': 'Shani', 'Rahu': 'Rahu', 'Ketu': 'Ketu'}
PLANET_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']


def planet_label(name, info, divisional):
    label = f"{HINDI_NAME[name]} ({name})"
    if divisional == 'd1' and info.get('retrograde'):
        label += ' (R)'
    if divisional == 'd1' and info.get('combust'):
        label += ' (Combust)'
    return label


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
    else:
        lagna_sign = natal['navamsa_ascendant_sign']
        house_key = 'navamsa_house_from_navamsa_lagna'

    houses = {h: [] for h in range(1, 13)}
    for name, info in natal['planets'].items():
        h = info[house_key]
        houses[h].append(planet_label(name, info, divisional))
    return lagna_sign, houses


def sign_for_house(lagna_sign, house_num):
    start = SIGNS.index(lagna_sign)
    return SIGNS[(start + house_num - 1) % 12]


def render_grid(title, grid_rows, cell_house_and_header, houses):
    """grid_rows: 4x4 list of cell keys (or None for the blank center).
    cell_house_and_header(key) -> (house_number, header_text)."""
    all_headers = []
    all_planet_lines = []
    resolved = []  # grid_rows but with (house, header) tuples, or None
    for row in grid_rows:
        resolved_row = []
        for key in row:
            if key is None:
                resolved_row.append(None)
                continue
            house, header = cell_house_and_header(key)
            resolved_row.append((house, header))
            all_headers.append(header)
            all_planet_lines.extend(houses[house])
        resolved.append(resolved_row)

    cellw = max([len(h) for h in all_headers] + [len(p) for p in all_planet_lines] + [11]) + 2
    border = '+' + ('-' * cellw + '+') * 4
    lines = [title, '', border]
    for row in resolved:
        row_height = max([len(houses[cell[0]]) for cell in row if cell is not None] + [0])
        text_rows = [[] for _ in range(1 + row_height)]
        for cell in row:
            if cell is None:
                for tr in text_rows:
                    tr.append(' ' * cellw)
                continue
            house, header = cell
            text_rows[0].append((' ' + header).ljust(cellw))
            planets = houses[house]
            for i in range(row_height):
                content = (' ' + planets[i]) if i < len(planets) else ''
                text_rows[i + 1].append(content.ljust(cellw))
        for tr in text_rows:
            lines.append('|' + '|'.join(tr) + '|')
        lines.append(border)
    return '\n'.join(lines)


# ---------- South Indian (sign-fixed grid) ----------

SOUTH_GRID = [
    ['Pisces', 'Aries', 'Taurus', 'Gemini'],
    ['Aquarius', None, None, 'Cancer'],
    ['Capricorn', None, None, 'Leo'],
    ['Sagittarius', 'Scorpio', 'Libra', 'Virgo'],
]


def render_south(chart, divisional, title):
    lagna_sign, houses = build_house_contents(chart, divisional)
    sign_to_house = {sign_for_house(lagna_sign, h): h for h in range(1, 13)}

    def house_and_header(sign):
        h = sign_to_house[sign]
        marker = ' ASC' if h == 1 else ''
        return h, f"{sign} H{h}{marker}"

    return render_grid(title, SOUTH_GRID, house_and_header, houses)


# ---------- North Indian (house-fixed grid) ----------
# A true North Indian chart is a diamond, but diagonal ASCII art breaks under
# almost any font/width mismatch (confirmed across multiple attempts). This
# keeps the actual North Indian semantic - house number is fixed to a grid
# position, the sign rotates around it based on the Ascendant - but draws it
# with the same robust straight-box style as the South Indian grid. House 1
# starts at the top-left cell and houses run clockwise around the ring.
NORTH_GRID = [
    [1, 2, 3, 4],
    [12, None, None, 5],
    [11, None, None, 6],
    [10, 9, 8, 7],
]


def render_north(chart, divisional, title):
    lagna_sign, houses = build_house_contents(chart, divisional)

    def house_and_header(h):
        sign = sign_for_house(lagna_sign, h)
        marker = ' ASC' if h == 1 else ''
        return h, f"H{h} {sign}{marker}"

    return render_grid(title, NORTH_GRID, house_and_header, houses)


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
    print(legend_table(chart, args.divisional))


if __name__ == '__main__':
    main()
