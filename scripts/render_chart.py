#!/usr/bin/env python3
"""
Render a D1 (Rasi) or D9 (Navamsa) chart from astro_calc.py's JSON output as
an ASCII grid, in either North Indian (house-fixed) or South Indian
(sign-fixed) style. Both use the same straight-box grid layout for rendering
robustness - North Indian keeps house 1 fixed to the top-left cell with
signs rotating around it per the Ascendant; South Indian keeps each sign
fixed to its cell with houses rotating instead.

This does no astrology math of its own - it only lays out planets/signs that
astro_calc.py already computed.
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


# ---------- North Indian (house-fixed block grid) ----------
# A true North Indian chart is a diamond, but diagonal ASCII art breaks under
# almost any font/width mismatch (verified: it kept rendering wrong across
# multiple attempts). This keeps the actual North Indian semantic - house
# number is fixed to a grid position, the sign rotates around it based on
# the Ascendant - but draws it with the same robust straight-box style as
# the South Indian grid. House 1 starts at the top-left cell and houses run
# clockwise around the ring, same traversal order as SOUTH_GRID.
NORTH_GRID = [
    [1, 2, 3, 4],
    [12, None, None, 5],
    [11, None, None, 6],
    [10, 9, 8, 7],
]


def render_north(chart, divisional, title):
    lagna_sign, houses, house_key, sign_key = build_house_contents(chart, divisional)

    cellw = 13
    lines = [title, '']
    border = '+' + ('-' * cellw + '+') * 4
    lines.append(border)
    for row in NORTH_GRID:
        line1 = '|'
        line2 = '|'
        for h in row:
            if h is None:
                line1 += ' ' * cellw + '|'
                line2 += ' ' * cellw + '|'
                continue
            sign = sign_for_house(lagna_sign, h)
            marker = ' ASC' if h == 1 else ''
            top = f" H{h} {SIGN3[sign]}{marker}"
            planets = ','.join(houses[h])
            line1 += top.ljust(cellw) + '|'
            line2 += (' ' + planets).ljust(cellw) + '|'
        lines.append(line1)
        lines.append(line2)
        lines.append(border)
    return '\n'.join(lines)


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
