#!/usr/bin/env python3
"""
Vedic (sidereal, Lahiri) astrology calculation engine.

Computes everything from a birth date/time/location using real Swiss
Ephemeris data: natal chart (D1) with house lordships, navamsa (D9) with
dignity/vargottama, full Vimshottari Mahadasha/Antardasha timeline plus
on-demand Pratyantardasha lookup for any date, Jaimini chara karakas,
birth Panchang (Tithi/Karana/Nitya Yoga/Vara), Sade Sati / Ashtama Shani
status, current transits, this month's Moon calendar, and a multi-year
Jupiter/Saturn/Rahu/Ketu house-transit scan.

This script only computes numbers. It does not interpret them -
interpretation (predictions, confidence tiers, remedies) is the job of
whoever reads its JSON output, guided by SKILL.md.
"""
import argparse
import json
from datetime import datetime, date

import swisseph as swe

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
         'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

NAKSHATRAS = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha',
    'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
    'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada',
    'Revati',
]

# Vimshottari dasha lord sequence (fixed cyclic order) and years
DASHA_SEQUENCE = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
                   'Saturn', 'Mercury']
DASHA_YEARS = {'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7,
                'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17}
NAKSHATRA_LORD = {}
for i, n in enumerate(NAKSHATRAS):
    NAKSHATRA_LORD[n] = DASHA_SEQUENCE[i % 9]

EXALTATION = {'Sun': 'Aries', 'Moon': 'Taurus', 'Mars': 'Capricorn',
              'Mercury': 'Virgo', 'Jupiter': 'Cancer', 'Venus': 'Pisces',
              'Saturn': 'Libra'}
DEBILITATION = {'Sun': 'Libra', 'Moon': 'Scorpio', 'Mars': 'Cancer',
                 'Mercury': 'Pisces', 'Jupiter': 'Capricorn', 'Venus': 'Virgo',
                 'Saturn': 'Aries'}
OWN_SIGNS = {'Sun': ['Leo'], 'Moon': ['Cancer'], 'Mars': ['Aries', 'Scorpio'],
             'Mercury': ['Gemini', 'Virgo'], 'Jupiter': ['Sagittarius', 'Pisces'],
             'Venus': ['Taurus', 'Libra'], 'Saturn': ['Capricorn', 'Aquarius']}
SIGN_LORD = {'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury',
             'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury',
             'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter',
             'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'}
# Approximate classical combustion orbs (degrees from Sun)
COMBUSTION_ORB = {'Moon': 12, 'Mars': 17, 'Mercury': 14, 'Jupiter': 11,
                   'Venus': 10, 'Saturn': 15}

PLANET_IDS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
    'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS,
    'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE,
}
CLASSICAL_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

FLAG = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED

CHARA_KARAKA_NAMES = ['Atmakaraka', 'Amatyakaraka', 'Bhratrikaraka',
                       'Matrikaraka', 'Putrakaraka', 'Gnatikaraka', 'Darakaraka']

TITHI_NAMES_1_14 = ['Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
                     'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
                     'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi']
KARANA_MOVABLE = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Garija', 'Vanija', 'Vishti']
NITYA_YOGA_NAMES = ['Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana',
                      'Atiganda', 'Sukarma', 'Dhriti', 'Shoola', 'Ganda', 'Vridhi',
                      'Dhruva', 'Vyaghata', 'Harshana', 'Vajra', 'Siddhi',
                      'Vyatipata', 'Variyana', 'Parigha', 'Shiva', 'Siddha',
                      'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra', 'Vaidhriti']
VARA_NAMES = ['Somavara (Monday)', 'Mangalavara (Tuesday)', 'Budhavara (Wednesday)',
              'Guruvara (Thursday)', 'Shukravara (Friday)', 'Shanivara (Saturday)',
              'Ravivara (Sunday)']

PLANET_ABBR = {'Sun': 'Sun', 'Moon': 'Moo', 'Mars': 'Mar', 'Mercury': 'Mer',
               'Jupiter': 'Jup', 'Venus': 'Ven', 'Saturn': 'Sat', 'Rahu': 'Rah',
               'Ketu': 'Ket'}

# Ashtakoot-style nakshatra classifications (Varna/Vasya are by Moon's Rashi;
# Yoni/Gana/Nadi are by Moon's Nakshatra). Standard classical tables used for
# guna-milan matching, reused here since they're the same tables AstroSage-style
# "Avkahada Chakra" panels report. Not central to a life-events reading -
# supplementary classification, offered as-is from the classical lists.
YONI_BY_NAKSHATRA = {
    'Ashwini': 'Horse', 'Bharani': 'Elephant', 'Krittika': 'Goat',
    'Rohini': 'Serpent', 'Mrigashira': 'Serpent', 'Ardra': 'Dog',
    'Punarvasu': 'Cat', 'Pushya': 'Goat', 'Ashlesha': 'Cat',
    'Magha': 'Rat', 'Purva Phalguni': 'Rat', 'Uttara Phalguni': 'Cow',
    'Hasta': 'Buffalo', 'Chitra': 'Tiger', 'Swati': 'Buffalo',
    'Vishakha': 'Tiger', 'Anuradha': 'Mriga', 'Jyeshtha': 'Mriga',
    'Mula': 'Dog', 'Purva Ashadha': 'Monkey', 'Uttara Ashadha': 'Nakula',
    'Shravana': 'Monkey', 'Dhanishta': 'Lion', 'Shatabhisha': 'Horse',
    'Purva Bhadrapada': 'Lion', 'Uttara Bhadrapada': 'Cow', 'Revati': 'Elephant',
}
GANA_BY_NAKSHATRA = {}
for _n in ['Ashwini', 'Mrigashira', 'Punarvasu', 'Pushya', 'Hasta', 'Swati',
           'Anuradha', 'Shravana', 'Revati']:
    GANA_BY_NAKSHATRA[_n] = 'Devta'
for _n in ['Bharani', 'Rohini', 'Ardra', 'Purva Phalguni', 'Uttara Phalguni',
           'Purva Ashadha', 'Uttara Ashadha', 'Purva Bhadrapada', 'Uttara Bhadrapada']:
    GANA_BY_NAKSHATRA[_n] = 'Manushya'
for _n in ['Krittika', 'Ashlesha', 'Magha', 'Chitra', 'Vishakha', 'Jyeshtha',
           'Mula', 'Dhanishta', 'Shatabhisha']:
    GANA_BY_NAKSHATRA[_n] = 'Rakshasa'
NADI_CYCLE = ['Adi', 'Madhya', 'Antya']

VARNA_BY_SIGN = {}
for _s in ['Cancer', 'Scorpio', 'Pisces']:
    VARNA_BY_SIGN[_s] = 'Bramhin'
for _s in ['Aries', 'Leo', 'Sagittarius']:
    VARNA_BY_SIGN[_s] = 'Kshatriya'
for _s in ['Taurus', 'Virgo', 'Capricorn']:
    VARNA_BY_SIGN[_s] = 'Vaishya'
for _s in ['Gemini', 'Libra', 'Aquarius']:
    VARNA_BY_SIGN[_s] = 'Shudra'

VASYA_WHOLE_SIGN = {
    'Aries': 'Chatushpada', 'Taurus': 'Chatushpada', 'Gemini': 'Manav',
    'Cancer': 'Jalachar', 'Leo': 'Vanachar', 'Virgo': 'Manav',
    'Libra': 'Manav', 'Scorpio': 'Keeta', 'Aquarius': 'Manav',
    'Pisces': 'Jalachar',
}

SIGN_ELEMENT = {}
for _i, _s in enumerate(SIGNS):
    SIGN_ELEMENT[_s] = ['Fire', 'Earth', 'Air', 'Water'][_i % 4]
PAYA_BY_ELEMENT = {'Fire': 'Copper', 'Earth': 'Silver', 'Air': 'Iron', 'Water': 'Gold'}


def vasya_of(sign, deg_in_sign_val):
    """Vasya (Vashya) classification by Moon's Rashi. Sagittarius and Capricorn
    are classically split by degree (0-15/15-30); other signs are whole-sign.
    This does not attempt finer sub-degree splits some classical sources apply
    beyond these two signs."""
    if sign == 'Sagittarius':
        return 'Manav' if deg_in_sign_val < 15 else 'Chatushpada'
    if sign == 'Capricorn':
        return 'Chatushpada' if deg_in_sign_val < 15 else 'Jalachar'
    return VASYA_WHOLE_SIGN[sign]


def hms_dot(hours):
    h = int(hours) % 24
    m_full = (hours - int(hours)) * 60
    m = int(m_full)
    s = int(round((m_full - m) * 60))
    return f"{h:02d}.{m:02d}.{s:02d}"


def y_m_d(years_float):
    y = int(years_float)
    months_frac = (years_float - y) * 12
    m = int(months_frac)
    d = int(round((months_frac - m) * 30))
    return y, m, d


def compute_avkahada_chakra(natal, birth_jd, lat, lon_geo, moon_lon):
    lagna_sign = natal['ascendant']['sign']
    moon = natal['planets']['Moon']
    rasi_sign = moon['sign']
    nak = moon['nakshatra']
    pada = moon['pada']
    nak_lord = moon['nakshatra_lord']

    span = 360.0 / 27
    idx = int(moon_lon // span) % 27
    frac_elapsed = (moon_lon % span) / span
    start_lord = NAKSHATRA_LORD[nak]
    balance_years_raw = (1 - frac_elapsed) * DASHA_YEARS[start_lord]
    by, bm, bd = y_m_d(balance_years_raw)

    sun = natal['planets']['Sun']
    ayanamsha_deg = swe.get_ayanamsa_ut(birth_jd)
    trop_sun_lon = (sun['longitude'] + ayanamsha_deg) % 360
    ecl_res, _ = swe.calc_ut(birth_jd, swe.ECL_NUT)
    obliquity_mean = ecl_res[1]
    gst = swe.sidtime(birth_jd)
    lst = (gst + lon_geo / 15) % 24

    return {
        'paya_nakshatra_based': PAYA_BY_ELEMENT[SIGN_ELEMENT[moon['navamsa_sign']]],
        'varna': VARNA_BY_SIGN[rasi_sign],
        'yoni': YONI_BY_NAKSHATRA[nak],
        'gana': GANA_BY_NAKSHATRA[nak],
        'vasya': vasya_of(rasi_sign, deg_in_sign(moon['longitude'])),
        'nadi': NADI_CYCLE[idx % 3],
        'dasa_balance_at_birth': f"{PLANET_ABBR[start_lord]} {by} Y {bm} M {bd} D",
        'lagna': lagna_sign,
        'lagna_lord': PLANET_ABBR[SIGN_LORD[lagna_sign]],
        'rasi': rasi_sign,
        'rasi_lord': PLANET_ABBR[SIGN_LORD[rasi_sign]],
        'nakshatra_pada': f"{nak} {pada}",
        'nakshatra_lord': PLANET_ABBR[nak_lord],
        'julian_day': int(birth_jd),
        'sunsign_indian_sidereal': sun['sign'],
        'sunsign_western_tropical': sign_of(trop_sun_lon),
        'ayanamsha': dms3(ayanamsha_deg),
        'ayanamsha_name': 'Lahiri',
        'obliquity': dms3(obliquity_mean),
        'sidereal_time_at_birth': hms_dot(lst),
        'ghatak_malefics': None,  # not yet implemented - do not guess this one
    }


def setup():
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def sign_of(lon):
    return SIGNS[int(lon // 30) % 12]


def deg_in_sign(lon):
    return lon % 30


def dms(deg_in_sign_val):
    d = int(deg_in_sign_val)
    m_full = (deg_in_sign_val - d) * 60
    m = int(m_full)
    s = int(round((m_full - m) * 60))
    return f"{d:02d}-{m:02d}-{s:02d}"


def dms3(deg_val):
    """Same as dms() but zero-padded to 3 digits (for 0-180 degree values
    like ayanamsha/obliquity, matching standard kundli-software formatting)."""
    d = int(deg_val)
    m_full = (deg_val - d) * 60
    m = int(m_full)
    s = int(round((m_full - m) * 60))
    return f"{d:03d}-{m:02d}-{s:02d}"


def nakshatra_of(lon):
    span = 360.0 / 27
    idx = int(lon // span) % 27
    pos_in_nak = lon % span
    pada = int(pos_in_nak // (span / 4)) + 1
    return NAKSHATRAS[idx], pada


def house_from_lagna(sign, lagna_sign):
    return ((SIGNS.index(sign) - SIGNS.index(lagna_sign)) % 12) + 1


def dignity_of(planet, sign):
    d = []
    if EXALTATION.get(planet) == sign:
        d.append('Exalted')
    if DEBILITATION.get(planet) == sign:
        d.append('Debilitated')
    if sign in OWN_SIGNS.get(planet, []):
        d.append('Own sign')
    return d or ['Neutral']


def navamsa_sign(sign, lon_in_sign):
    """Return the navamsa (D9) sign for a given D1 sign + degree-in-sign."""
    pada = int(lon_in_sign // (10 / 3.0))  # 0..8
    element = SIGNS.index(sign) % 4
    # movable(fire): Aries,Leo,Sagittarius -> start Aries(0)
    # fixed(earth): Taurus,Virgo,Capricorn -> start Capricorn(9)
    # dual(air): Gemini,Libra,Aquarius -> start Libra(6)
    # dual(water): Cancer,Scorpio,Pisces -> start Cancer(3)
    starts = {0: 0, 1: 9, 2: 6, 3: 3}
    start_idx = starts[element]
    return SIGNS[(start_idx + pada) % 12]


def julday_from_civil(date_str, time_str, utc_offset):
    y, mo, d = (int(x) for x in date_str.split('-'))
    h, mi = (int(x) for x in time_str.split(':'))
    local_hours = h + mi / 60.0
    ut_hours = local_hours - utc_offset
    jd = swe.julday(y, mo, d, ut_hours)
    return jd


def compute_natal(jd_ut, lat, lon_geo):
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon_geo, b'W', FLAG)
    asc_lon = ascmc[0]
    lagna_sign = sign_of(asc_lon)
    lagna_nak, lagna_pada = nakshatra_of(asc_lon)
    navamsa_asc = navamsa_sign(lagna_sign, deg_in_sign(asc_lon))

    houses = {}
    house_lords = {}
    for h in range(1, 13):
        sign_idx = (SIGNS.index(lagna_sign) + h - 1) % 12
        s = SIGNS[sign_idx]
        houses[h] = s
        house_lords[h] = SIGN_LORD[s]

    sun_lon, _ = swe.calc_ut(jd_ut, swe.SUN, FLAG)
    sun_lon = sun_lon[0]

    planets = {}
    for name in CLASSICAL_ORDER + ['Rahu']:
        pos, _ = swe.calc_ut(jd_ut, PLANET_IDS[name], FLAG)
        lon_ = pos[0]
        speed = pos[3]
        sign = sign_of(lon_)
        dis = deg_in_sign(lon_)
        nak, pada = nakshatra_of(lon_)
        retro = speed < 0
        combust = False
        if name in COMBUSTION_ORB:
            angle = abs(lon_ - sun_lon)
            angle = min(angle, 360 - angle)
            combust = angle <= COMBUSTION_ORB[name]
        nav_sign = navamsa_sign(sign, dis)
        rules_houses = [h for h, s in houses.items() if SIGN_LORD[s] == name]
        planets[name] = {
            'longitude': round(lon_, 4),
            'sign': sign,
            'degree_in_sign': dms(dis),
            'nakshatra': nak,
            'pada': pada,
            'nakshatra_lord': NAKSHATRA_LORD[nak],
            'house_from_lagna': house_from_lagna(sign, lagna_sign),
            'rules_houses': rules_houses,
            'retrograde': retro,
            'dignity': dignity_of(name, sign),
            'combust': combust,
            'navamsa_sign': nav_sign,
            'navamsa_dignity': dignity_of(name, nav_sign),
            'vargottama': nav_sign == sign,
            'navamsa_house_from_navamsa_lagna': house_from_lagna(nav_sign, navamsa_asc),
        }

    # Ketu = Rahu + 180 (nodes are not classical sign lords/dignities beyond Neutral here)
    rahu_lon = planets['Rahu']['longitude']
    ketu_lon = (rahu_lon + 180) % 360
    ketu_sign = sign_of(ketu_lon)
    ketu_dis = deg_in_sign(ketu_lon)
    ketu_nak, ketu_pada = nakshatra_of(ketu_lon)
    ketu_nav_sign = navamsa_sign(ketu_sign, ketu_dis)
    planets['Ketu'] = {
        'longitude': round(ketu_lon, 4),
        'sign': ketu_sign,
        'degree_in_sign': dms(ketu_dis),
        'nakshatra': ketu_nak,
        'pada': ketu_pada,
        'nakshatra_lord': NAKSHATRA_LORD[ketu_nak],
        'house_from_lagna': house_from_lagna(ketu_sign, lagna_sign),
        'rules_houses': [],
        'retrograde': True,
        'dignity': ['Neutral'],
        'combust': False,
        'navamsa_sign': ketu_nav_sign,
        'navamsa_dignity': ['Neutral'],
        'vargottama': ketu_nav_sign == ketu_sign,
        'navamsa_house_from_navamsa_lagna': house_from_lagna(ketu_nav_sign, navamsa_asc),
    }

    return {
        'ascendant': {
            'longitude': round(asc_lon, 4),
            'sign': lagna_sign,
            'degree_in_sign': dms(deg_in_sign(asc_lon)),
            'nakshatra': lagna_nak,
            'pada': lagna_pada,
        },
        'navamsa_ascendant_sign': navamsa_asc,
        'houses_whole_sign': houses,
        'house_lords': house_lords,
        'planets': planets,
    }


def compute_chara_karakas(planets):
    """Jaimini chara karakas from the 7 classical grahas, ranked by degree-in-sign (desc)."""
    rows = []
    for name in CLASSICAL_ORDER:
        d = planets[name]['degree_in_sign']
        parts = [int(x) for x in d.split('-')]
        deg_decimal = parts[0] + parts[1] / 60 + parts[2] / 3600
        rows.append((name, deg_decimal))
    rows.sort(key=lambda r: -r[1])
    return {CHARA_KARAKA_NAMES[i]: rows[i][0] for i in range(7)}


def jd_to_iso(jd):
    y, m, d, h = swe.revjul(jd)
    total_seconds = int(round(h * 3600))
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}"


def iso_to_jd(iso):
    dt = datetime.fromisoformat(iso)
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def compute_pratyantardashas(antardasha):
    """Given one antardasha dict {lord:'MD-AD', start, end, years}, return its 9 pratyantardashas."""
    md_lord, ad_lord = antardasha['lord'].split('-')
    start_jd = iso_to_jd(antardasha['start'])
    ad_years = antardasha['years']
    idx = DASHA_SEQUENCE.index(ad_lord)
    result = []
    cur_jd = start_jd
    for i in range(9):
        pd_lord = DASHA_SEQUENCE[(idx + i) % 9]
        pd_years = ad_years * DASHA_YEARS[pd_lord] / 120.0
        end_jd = cur_jd + pd_years * 365.2425
        result.append({
            'lord': f"{md_lord}-{ad_lord}-{pd_lord}",
            'start': jd_to_iso(cur_jd),
            'end': jd_to_iso(end_jd),
            'years': round(pd_years, 4),
        })
        cur_jd = end_jd
    return result


def compute_antardashas(mahadasha, with_pratyantardasha_for=None):
    """Given one mahadasha dict {lord,start,end,years}, return its 9 antardashas.
    If with_pratyantardasha_for is an antardasha lord name (e.g. 'Mercury'), also
    attach pratyantardashas to that one antardasha to keep output size sane.
    """
    lord = mahadasha['lord']
    start_jd = iso_to_jd(mahadasha['start'])
    md_years = mahadasha['years']
    idx = DASHA_SEQUENCE.index(lord)
    result = []
    cur_jd = start_jd
    for i in range(9):
        ad_lord = DASHA_SEQUENCE[(idx + i) % 9]
        ad_years = md_years * DASHA_YEARS[ad_lord] / 120.0
        end_jd = cur_jd + ad_years * 365.2425
        entry = {
            'lord': f"{lord}-{ad_lord}",
            'start': jd_to_iso(cur_jd),
            'end': jd_to_iso(end_jd),
            'years': round(ad_years, 4),
        }
        if with_pratyantardasha_for == ad_lord:
            entry['pratyantardashas'] = compute_pratyantardashas(entry)
        result.append(entry)
        cur_jd = end_jd
    return result


def compute_dasha_timeline(moon_lon, birth_jd, cycles=1):
    nak, pada = nakshatra_of(moon_lon)
    span = 360.0 / 27
    frac_elapsed = (moon_lon % span) / span
    start_lord = NAKSHATRA_LORD[nak]
    start_idx = DASHA_SEQUENCE.index(start_lord)
    balance_years = (1 - frac_elapsed) * DASHA_YEARS[start_lord]

    timeline = []
    cur_jd = birth_jd
    lord = start_lord
    dur_years = balance_years
    idx = start_idx
    total_years = 0
    while total_years < 120 * cycles:
        end_jd = cur_jd + dur_years * 365.2425
        md = {
            'lord': lord,
            'start': jd_to_iso(cur_jd),
            'end': jd_to_iso(end_jd),
            'years': round(dur_years, 3),
        }
        md['antardashas'] = compute_antardashas(md)
        timeline.append(md)
        total_years += dur_years
        cur_jd = end_jd
        idx = (idx + 1) % 9
        lord = DASHA_SEQUENCE[idx]
        dur_years = DASHA_YEARS[lord]
    return timeline


def dasha_at(timeline, as_of_jd):
    """Full Mahadasha -> Antardasha -> Pratyantardasha resolution for any instant."""
    as_of_iso = jd_to_iso(as_of_jd)
    for md in timeline:
        if md['start'] <= as_of_iso <= md['end']:
            current_ad = None
            for ad in md['antardashas']:
                if ad['start'] <= as_of_iso <= ad['end']:
                    current_ad = ad
                    break
            pds = None
            current_pd = None
            if current_ad:
                pds = compute_pratyantardashas(current_ad)
                for pd_ in pds:
                    if pd_['start'] <= as_of_iso <= pd_['end']:
                        current_pd = pd_
                        break
            return {
                'as_of': as_of_iso,
                'mahadasha': md['lord'], 'mahadasha_start': md['start'], 'mahadasha_end': md['end'],
                'antardasha': current_ad['lord'] if current_ad else None,
                'antardasha_start': current_ad['start'] if current_ad else None,
                'antardasha_end': current_ad['end'] if current_ad else None,
                'pratyantardasha': current_pd['lord'] if current_pd else None,
                'pratyantardasha_start': current_pd['start'] if current_pd else None,
                'pratyantardasha_end': current_pd['end'] if current_pd else None,
                'all_pratyantardashas_this_antardasha': pds,
            }
    return None


def compute_current_transits(jd_ut, lagna_sign):
    result = {}
    for name in CLASSICAL_ORDER + ['Rahu']:
        pos, _ = swe.calc_ut(jd_ut, PLANET_IDS[name], FLAG)
        lon_ = pos[0]
        sign = sign_of(lon_)
        nak, pada = nakshatra_of(lon_)
        result[name] = {
            'sign': sign,
            'degree_in_sign': dms(deg_in_sign(lon_)),
            'nakshatra': nak,
            'pada': pada,
            'house_from_natal_lagna': house_from_lagna(sign, lagna_sign),
            'retrograde': pos[3] < 0,
        }
    rahu_lon_full, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, FLAG)
    ketu_lon = (rahu_lon_full[0] + 180) % 360
    ketu_sign = sign_of(ketu_lon)
    ketu_nak, ketu_pada = nakshatra_of(ketu_lon)
    result['Ketu'] = {
        'sign': ketu_sign,
        'degree_in_sign': dms(deg_in_sign(ketu_lon)),
        'nakshatra': ketu_nak,
        'pada': ketu_pada,
        'house_from_natal_lagna': house_from_lagna(ketu_sign, lagna_sign),
        'retrograde': True,
    }
    return result


def compute_sade_sati_status(natal_moon_sign, transit_saturn_sign):
    moon_idx = SIGNS.index(natal_moon_sign)
    phases = {
        SIGNS[(moon_idx - 1) % 12]: 'Sade Sati - rising phase (Saturn 12th from natal Moon)',
        SIGNS[moon_idx]: 'Sade Sati - peak phase (Saturn transiting natal Moon sign)',
        SIGNS[(moon_idx + 1) % 12]: 'Sade Sati - setting phase (Saturn 2nd from natal Moon)',
    }
    ashtama_sign = SIGNS[(moon_idx + 7) % 12]
    if transit_saturn_sign in phases:
        return {'status': phases[transit_saturn_sign], 'ashtama_shani_sign': ashtama_sign}
    if transit_saturn_sign == ashtama_sign:
        return {'status': 'Ashtama Shani (Saturn 8th from natal Moon)', 'ashtama_shani_sign': ashtama_sign}
    return {'status': 'Not currently in Sade Sati or Ashtama Shani', 'ashtama_shani_sign': ashtama_sign}


MANGAL_DOSHA_HOUSES = {1, 2, 4, 7, 8, 12}


def compute_mangal_dosha(mars_house_from_lagna, mars_house_from_moon):
    """Kuja/Mangal Dosha: Mars in 1st/2nd/4th/7th/8th/12th from Lagna or Moon.
    Checked from Lagna and Moon only - the two references classical sources
    agree on universally; some schools also check from Venus. Classical
    cancellation (bhanga) rules exist (Mars in its own/exalted sign, benefic
    aspects, etc.) and are numerous and inconsistent across sources, so
    they're deliberately not evaluated here - a 'present: true' result means
    the raw placement condition is met, not a final verdict."""
    from_lagna = mars_house_from_lagna in MANGAL_DOSHA_HOUSES
    from_moon = mars_house_from_moon in MANGAL_DOSHA_HOUSES
    return {
        'present': from_lagna or from_moon,
        'present_from_lagna': from_lagna,
        'present_from_moon': from_moon,
        'mars_house_from_lagna': mars_house_from_lagna,
        'mars_house_from_moon': mars_house_from_moon,
        'note': ('Raw placement condition only - classical cancellation (bhanga) rules '
                 '(e.g. Mars in own/exalted sign, benefic aspects) are not evaluated.'),
    }


KALSARPA_TYPE_BY_RAHU_HOUSE = ['Anant', 'Kulik', 'Vasuki', 'Shankhpal', 'Padma', 'Mahapadma',
                                'Takshak', 'Karkotak', 'Shankhachur', 'Ghatak', 'Vishdhar', 'Sheshnag']


def compute_kalsarpa_dosha(classical_planet_longitudes, rahu_lon, ketu_lon, rahu_house_from_lagna):
    """Kalsarpa Dosha: all 7 classical grahas fall within one of the two
    180-degree arcs bounded by Rahu and Ketu, with none on the other side."""
    def in_arc(lon, start, end):
        span = (end - start) % 360
        pos = (lon - start) % 360
        return pos <= span

    all_in_rahu_to_ketu = all(in_arc(lon, rahu_lon, ketu_lon) for lon in classical_planet_longitudes.values())
    all_in_ketu_to_rahu = all(in_arc(lon, ketu_lon, rahu_lon) for lon in classical_planet_longitudes.values())
    present = all_in_rahu_to_ketu or all_in_ketu_to_rahu
    return {
        'present': present,
        'type': KALSARPA_TYPE_BY_RAHU_HOUSE[rahu_house_from_lagna - 1] if present else None,
    }


SATURN_MOON_PHASE_BY_HOUSE = {
    12: 'Sade Sati - Rising', 1: 'Sade Sati - Peak', 2: 'Sade Sati - Setting',
    4: 'Kantak Shani', 8: 'Ashtama Shani',
}


def compute_sade_sati_full_timeline(natal_moon_sign, birth_jd, years_span=100, step_days=2.0):
    """Full-life Saturn-from-Moon timeline: every Sade Sati (12th/1st/2nd
    from natal Moon), Kantak Shani (4th), and Ashtama Shani (8th) phase from
    birth through birth + years_span, with exact start/end dates. Reuses
    scan_sign_ingress with the natal Moon sign as the reference point instead
    of the Lagna - the 'house_from_natal_lagna' key in its output is really
    'house from natal Moon' in this call, relabeled below.

    Scans from 3 years before birth (longer than Saturn's max stay in one
    sign) so a phase already under way at birth reports its true start date
    rather than being truncated at the birth date, then drops any phase that
    fully ended before birth."""
    birth_iso = jd_to_iso(birth_jd)[:10]
    jd_start = birth_jd - 3 * 365.2425
    jd_end = birth_jd + years_span * 365.2425
    events = scan_sign_ingress('Saturn', jd_start, jd_end, natal_moon_sign, step_days=step_days)
    timeline = []
    for i, ev in enumerate(events):
        house_from_moon = ev['house_from_natal_lagna']
        phase = SATURN_MOON_PHASE_BY_HOUSE.get(house_from_moon)
        end = events[i + 1]['date'] if i + 1 < len(events) else None
        if phase and (end is None or end > birth_iso):
            timeline.append({
                'phase': phase,
                'saturn_sign': ev['enters_sign'],
                'house_from_natal_moon': house_from_moon,
                'start': ev['date'],
                'end': end,
            })
    return timeline


def compute_panchang(jd_ut, sun_lon, moon_lon):
    diff = (moon_lon - sun_lon) % 360
    tithi_num = int(diff // 12) + 1  # 1..30
    paksha = 'Shukla' if tithi_num <= 15 else 'Krishna'
    local_num = tithi_num if tithi_num <= 15 else tithi_num - 15
    if local_num == 15:
        tithi_name = 'Purnima' if paksha == 'Shukla' else 'Amavasya'
    else:
        tithi_name = TITHI_NAMES_1_14[local_num - 1]

    karana_idx = int(diff // 6)  # 0..59
    if karana_idx == 0:
        karana_name = 'Kimstughna'
    elif karana_idx == 59:
        karana_name = 'Naga'
    elif karana_idx == 58:
        karana_name = 'Chatushpada'
    elif karana_idx == 57:
        karana_name = 'Shakuni'
    else:
        karana_name = KARANA_MOVABLE[(karana_idx - 1) % 7]

    yoga_sum = (moon_lon + sun_lon) % 360
    yoga_idx = int(yoga_sum // (360 / 27)) % 27
    nitya_yoga = NITYA_YOGA_NAMES[yoga_idx]

    y, m, d, _h = swe.revjul(jd_ut)
    weekday = date(y, m, d).weekday()  # Monday=0..Sunday=6
    vara = VARA_NAMES[weekday]

    return {
        'tithi': f"{paksha} {tithi_name}", 'tithi_number': tithi_num,
        'karana': karana_name, 'nitya_yoga': nitya_yoga, 'vara': vara,
    }


def scan_sign_ingress(planet_name, jd_start, jd_end, lagna_sign, step_days=1.0):
    pid = PLANET_IDS[planet_name] if planet_name != 'Ketu' else swe.MEAN_NODE
    events = []
    last_sign = None
    jd = jd_start
    while jd < jd_end:
        pos, _ = swe.calc_ut(jd, pid, FLAG)
        lon_ = pos[0]
        if planet_name == 'Ketu':
            lon_ = (lon_ + 180) % 360
        s = sign_of(lon_)
        if s != last_sign:
            events.append({
                'date': jd_to_iso(jd)[:10],
                'enters_sign': s,
                'house_from_natal_lagna': house_from_lagna(s, lagna_sign),
            })
            last_sign = s
        jd += step_days
    return events


def compute_moon_month_calendar(year, month, lagna_sign):
    jd_start = swe.julday(year, month, 1, 0.0)
    if month == 12:
        jd_end = swe.julday(year + 1, 1, 1, 0.0)
    else:
        jd_end = swe.julday(year, month + 1, 1, 0.0)
    jd_end += 3
    return scan_sign_ingress('Moon', jd_start, jd_end, lagna_sign, step_days=0.5)


def compute_fast_planet_month(year, month, lagna_sign):
    jd_start = swe.julday(year, month, 1, 0.0)
    if month == 12:
        jd_end = swe.julday(year + 1, 1, 1, 0.0)
    else:
        jd_end = swe.julday(year, month + 1, 1, 0.0)
    out = {}
    for name in ['Sun', 'Mercury', 'Venus', 'Mars']:
        out[name] = scan_sign_ingress(name, jd_start, jd_end, lagna_sign, step_days=1.0)
    return out


def main():
    ap = argparse.ArgumentParser(description='Vedic sidereal (Lahiri) astrology calculator')
    ap.add_argument('--name', default='')
    ap.add_argument('--date', required=True, help='YYYY-MM-DD (local birth date)')
    ap.add_argument('--time', required=True, help='HH:MM 24-hour local birth time')
    ap.add_argument('--utc-offset', required=True, type=float, help='e.g. 5.5 for IST')
    ap.add_argument('--lat', required=True, type=float)
    ap.add_argument('--lon', required=True, type=float)
    ap.add_argument('--place', default='')
    ap.add_argument('--forward-years', type=int, default=8,
                     help='years to forward-scan Jupiter/Saturn/Rahu/Ketu house transits')
    ap.add_argument('--sade-sati-years', type=int, default=100,
                     help='years from birth to scan for the full Sade Sati/Kantak Shani/Ashtama Shani timeline')
    ap.add_argument('--now', default=None,
                     help='override "current" instant as ISO YYYY-MM-DDTHH:MM in UTC (default: real now)')
    ap.add_argument('--dasha-lookup', default=None,
                     help='ISO YYYY-MM-DDTHH:MM (UTC) to resolve Mahadasha/Antardasha/Pratyantardasha '
                          'for any past or future instant, independent of --now')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    setup()

    birth_jd = julday_from_civil(args.date, args.time, args.utc_offset)
    natal = compute_natal(birth_jd, args.lat, args.lon)
    lagna_sign = natal['ascendant']['sign']
    natal_moon_sign = natal['planets']['Moon']['sign']

    moon_lon = natal['planets']['Moon']['longitude']
    sun_lon_birth = natal['planets']['Sun']['longitude']
    dasha_timeline = compute_dasha_timeline(moon_lon, birth_jd, cycles=1)
    panchang = compute_panchang(birth_jd, sun_lon_birth, moon_lon)
    avkahada_chakra = compute_avkahada_chakra(natal, birth_jd, args.lat, args.lon, moon_lon)

    if args.now:
        dt = datetime.fromisoformat(args.now)
        jd_now = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
    else:
        dt = datetime.utcnow()
        jd_now = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    current_dasha = dasha_at(dasha_timeline, jd_now)
    karakas = compute_chara_karakas(natal['planets'])
    transits_now = compute_current_transits(jd_now, lagna_sign)
    sade_sati = compute_sade_sati_status(natal_moon_sign, transits_now['Saturn']['sign'])
    sade_sati_timeline = compute_sade_sati_full_timeline(natal_moon_sign, birth_jd, years_span=args.sade_sati_years)

    mars_house_from_moon = house_from_lagna(natal['planets']['Mars']['sign'], natal_moon_sign)
    mangal_dosha = compute_mangal_dosha(natal['planets']['Mars']['house_from_lagna'], mars_house_from_moon)

    classical_lons = {name: natal['planets'][name]['longitude'] for name in CLASSICAL_ORDER}
    kalsarpa_dosha = compute_kalsarpa_dosha(
        classical_lons, natal['planets']['Rahu']['longitude'], natal['planets']['Ketu']['longitude'],
        natal['planets']['Rahu']['house_from_lagna'])

    y_now, m_now, d_now, _ = swe.revjul(jd_now)
    moon_month = compute_moon_month_calendar(y_now, m_now, lagna_sign)
    fast_month = compute_fast_planet_month(y_now, m_now, lagna_sign)

    jd_fwd_end = jd_now + args.forward_years * 365.2425
    forward_scan = {}
    for name in ['Jupiter', 'Saturn', 'Rahu', 'Ketu']:
        forward_scan[name] = scan_sign_ingress(name, jd_now, jd_fwd_end, lagna_sign, step_days=1.0)

    output = {
        'input': {
            'name': args.name, 'date': args.date, 'time': args.time,
            'utc_offset': args.utc_offset, 'lat': args.lat, 'lon': args.lon,
            'place': args.place,
        },
        'ayanamsha': 'Lahiri',
        'house_system': 'Whole Sign',
        'panchang_at_birth': panchang,
        'avkahada_chakra': avkahada_chakra,
        'natal_chart': natal,
        'jaimini_chara_karakas': karakas,
        'vimshottari_dasha_timeline': dasha_timeline,
        'current_dasha': current_dasha,
        'sade_sati_status': sade_sati,
        'sade_sati_full_timeline': sade_sati_timeline,
        'mangal_dosha': mangal_dosha,
        'kalsarpa_dosha': kalsarpa_dosha,
        'current_transits': transits_now,
        'this_month_moon_calendar': moon_month,
        'this_month_fast_planets': fast_month,
        f'forward_{args.forward_years}yr_house_transit_scan': forward_scan,
    }

    if args.dasha_lookup:
        dt2 = datetime.fromisoformat(args.dasha_lookup)
        jd_lookup = swe.julday(dt2.year, dt2.month, dt2.day, dt2.hour + dt2.minute / 60.0)
        output['dasha_lookup'] = dasha_at(dasha_timeline, jd_lookup)

    text = json.dumps(output, indent=2)
    if args.out:
        with open(args.out, 'w') as f:
            f.write(text)
    else:
        print(text)


if __name__ == '__main__':
    main()
