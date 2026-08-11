# Planetary Remedies (Upaya) Reference

**Read this disclaimer before using anything below, and repeat its substance
to the user when giving remedies:**

These are traditional/folk Jyotish practices, compiled from classical
remedial-astrology sources. They are not scientifically validated, and this
reference does not claim they work by any mechanism outside of the tradition's
own framework (faith, ritual, psychological focus, symbolic association).
Never present them as a guaranteed fix, a substitute for medical/mental-health
care, legal advice, or financial planning, or as something a real problem
"requires" to be solved. Offer them as optional traditional practice for
someone who wants to engage with the tradition on its own terms.

**Gemstones are deliberately not prescribed here.** Wearing an unsuitable
stone (wrong planet, wrong quality, wrong finger/metal, contraindicated by
another placement) is treated seriously in the classical literature itself as
something that can do more harm than good. If a user wants a gemstone
recommendation, tell them this needs a practitioner who examines the full
chart in person - don't generate one from this reference.

## How to select remedies for a specific chart

Don't dump all nine grahas' remedies on someone. Select by relevance, in this
priority order:
1. The current Mahadasha lord and current Antardasha lord (from `current_dasha`
   in the script output) - these are the "live" planets right now.
2. Any planet that's Debilitated, combust, or in the 6th/8th/12th house
   (`dignity`, `combust`, `house_from_lagna` fields).
3. `sade_sati_status` if it's active - Saturn-specific protocol below.
4. A planet the user's actual question is about (e.g. asking about marriage ->
   look at the 7th lord and Darakaraka, not a random planet).

Two or three well-chosen remedies, each tied to something real in the chart,
is more useful than a checklist of nine.

---

## Sun (Surya)

**Signifies:** soul/self, vitality, father, authority, government, bones, eyes.

**Relevant when:** debilitated (Libra), combust, placed in 6th/8th/12th,
afflicted by conjunction with Saturn/Rahu/Ketu, or currently a dasha lord.

**Upaya:**
- Offer water to the rising sun each morning (Surya Arghya), facing east,
  ideally from a copper vessel.
- Donate copper, wheat, jaggery, or red cloth, ideally on Sundays.
- Recite the Aditya Hridayam stotra.
- Consciously work on the relationship with one's father or authority figures.

**Mantra:** Beej mantra *Om Hraam Hreem Hraum Sah Suryaya Namah*; simple form
*Om Suryaya Namah*. Traditionally recited facing the sun at sunrise.

**Why:** In this framework the Sun is the significator of the self and of
vital force (atma/prana). Facing the physically rising sun each morning is
meant to align one's own vitality with that daily renewal. Copper and wheat
are Sun's classical correspondences (fire element, warm/dry qualities in
Ayurvedic terms), so offering them is read as "feeding" a weak Sun. Reconciling
with a father figure addresses the relational layer the Sun carries (paternal
lineage, authority, one's relationship to one's own confidence).

---

## Moon (Chandra)

**Signifies:** mind, emotions, mother, intuition, fluids, the general public.

**Relevant when:** debilitated (Scorpio), waning/dark-of-month weak, afflicted
by Saturn (classically "Vish Yoga") or by Rahu/Ketu, placed in 6th/8th/12th.

**Upaya:**
- Donate white items - rice, milk, silver, white cloth - especially on
  Mondays.
- Worship Shiva (the Moon rests on Shiva's head in iconography, read as a
  symbol of a restless mind held by disciplined stillness).
- Keep a stable sleep schedule; moderate alcohol/fluid intake.
- Maintain a warm, low-conflict relationship with one's mother where possible.

**Mantra:** Beej mantra *Om Shraam Shreem Shraum Sah Chandraya Namah*; also
*Om Namah Shivaya* for the Chandra-Shiva association. Recited on Mondays,
often facing the moon at night when visible.

**Why:** The Moon governs *manas* (the emotional mind) in this framework.
White, cooling substances are the classical antidote to an agitated or weak
Moon - the logic is thermal/qualitative (cooling counters emotional heat or
instability), the same logic behind many Ayurvedic Moon remedies. Shiva
worship draws directly on the myth of the crescent moon on Shiva's head:
externalizing the aspiration to hold an unsteady mind in stillness.

---

## Mars (Mangal)

**Signifies:** courage, physical energy, siblings, land/property, conflict,
surgery.

**Relevant when:** debilitated (Cancer), retrograde, involved in classical
Mangal Dosha placements (varies by school - commonly 1st/2nd/4th/7th/8th/12th
from Lagna, Moon, or Venus), conjunct Saturn or Rahu, currently a dasha lord.

**Upaya:**
- Donate red lentils (masoor dal), red cloth, or jaggery, ideally on Tuesdays.
- Worship Hanuman or Kartikeya (both classically associated with disciplined
  strength).
- Channel the energy physically - structured exercise or martial practice
  rather than suppression.
- Deliberately slow down before conflict with siblings or in disputes over
  property.

**Mantra:** Beej mantra *Om Kraam Kreem Kraum Sah Bhaumaya Namah*; the Hanuman
Chalisa is also commonly used for Mars-related concerns.

**Why:** Mars is read as raw fire/blood/muscular energy. Red offerings and
Tuesday timing follow its classical color/day correspondence. Hanuman is
invoked specifically because he represents Mars's energy already disciplined
into protective strength rather than raw aggression - the remedy models the
transformation being sought, not just an offering.

---

## Mercury (Budh)

**Signifies:** intellect, communication, commerce, siblings (younger),
nervous system.

**Relevant when:** combust, debilitated (Pisces), conjunct malefics, in
6th/8th/12th.

**Upaya:**
- Donate green items - moong dal (green gram), green cloth - ideally on
  Wednesdays.
- Worship Ganesha (invoked here for clarity of thought) or Vishnu.
- Practice deliberately honest, unhurried speech.
- Mentor or support younger siblings or students.

**Mantra:** Beej mantra *Om Braam Breem Braum Sah Budhaya Namah*.

**Why:** Mercury governs *buddhi* - discriminating intellect and expression.
Green is its classical color, tied to growth and adaptability. Ganesha is
invoked as remover of obstacles specifically for obstacles to clear thinking
and communication, which is the domain Mercury governs.

---

## Jupiter (Guru / Brihaspati)

**Signifies:** wisdom, higher learning, teachers, dharma, expansion, children,
wealth.

**Relevant when:** debilitated (Capricorn), combust, conjunct malefics, or in
6th/8th/12th (unusual for a natural benefic, and worth remedying when it
happens), currently a dasha lord.

**Upaya:**
- Donate yellow items - turmeric, chana dal (Bengal gram), yellow cloth,
  books - ideally on Thursdays.
- Actively respect teachers, mentors, and elders; support education-related
  causes.
- Recite the Vishnu Sahasranama or a Guru-focused mantra.

**Mantra:** Beej mantra *Om Graam Greem Graum Sah Gurave Namah*; also
*Om Namo Bhagavate Vasudevaya*.

**Why:** Jupiter represents dharma, expansive growth, and guidance. Yellow and
gold are its classical colors, symbolically tied to abundance and wisdom.
Honoring teachers directly engages the guru-shishya (mentor-student)
relationship Jupiter signifies, rather than treating the remedy as a purely
ritual transaction.

---

## Venus (Shukra)

**Signifies:** love, beauty, relationships, creativity, comfort, art, wealth.

**Relevant when:** combust, debilitated (Virgo), afflicted in 6th/8th/12th, or
when the Darakaraka (spouse-indicator) is weak.

**Upaya:**
- Donate white or pastel items, sugar, ghee, or perfume, ideally on Fridays.
- Worship Lakshmi or Durga.
- Invest time in creative or artistic practice.
- Watch for and moderate overindulgence or vanity-driven spending, which is
  Venus unbalanced rather than Venus expressed well.

**Mantra:** Beej mantra *Om Draam Dreem Draum Sah Shukraya Namah*.

**Why:** Venus governs *rasa* - aesthetic pleasure and relational harmony.
Lakshmi worship draws on Venus's shared signification of beauty and
prosperity. The caution against excess is deliberate: Venus's affliction
often shows up as indulgence rather than deprivation, so the "remedy" is
sometimes restraint, not more offerings.

---

## Saturn (Shani)

**Signifies:** discipline, delay, karma, longevity, structure, labor, the
underprivileged.

**Relevant when:** debilitated (Aries), Sade Sati or Ashtama Shani currently
active (see protocol below), conjunct malefics, ruling a difficult house,
currently a dasha lord.

**Upaya:**
- Donate black sesame, mustard oil, iron, black cloth, or urad dal, ideally on
  Saturdays.
- Serve or donate to the underprivileged, elderly, or laborers directly rather
  than only through ritual donation.
- Worship Hanuman (classically considered protective during hard Saturn
  periods) or Shani directly.
- Prioritize discipline, patience, and follow-through - Saturn is described as
  rewarding consistency over intensity.

**Mantra:** Beej mantra *Om Praam Preem Praum Sah Shanaye Namah*; also
*Om Sham Shanicharaya Namah*; the Hanuman Chalisa is widely used alongside
direct Shani mantras.

**Why:** Saturn governs karma and structural discipline. Dark, heavy
offerings (sesame, iron, black cloth) match its classical "heavy," restrictive
qualitative correspondence. Service to the underprivileged is not incidental -
it directly engages the social-duty and labor significations Saturn carries,
and is traditionally held to ease its harsher lessons through lived humility
rather than ritual alone.

---

## Rahu (North Node)

**Signifies:** obsession, foreign/unconventional elements, illusion, sudden
ambition or change. Not a physical body - a shadow/mathematical point.

**Relevant when:** currently a dasha lord, conjunct malefics, placed in
8th/12th, or afflicting a house's matters through occupation there.

**Upaya:**
- Donate multi-colored items or blankets, and mustard oil, ideally on
  Saturdays (Rahu's remedies are often paired with Saturn-style practices).
- Feed or care for dogs.
- Worship Durga.
- Build deliberate grounding routines - Rahu's nature is restless and
  illusion-prone, so remedies lean toward stability rather than more
  stimulation.

**Mantra:** Beej mantra *Om Bhraam Bhreem Bhraum Sah Rahave Namah*; the Durga
Chalisa is also used.

**Why:** Rahu has no physical body in this framework, so its remedies target
the *psychological* qualities it's associated with - obsession and illusion -
rather than a planetary deity in the usual sense. Durga is invoked for
protective clarity against confusion. Caring for dogs draws on a
long-standing regional/mythological association between Rahu and dogs in
several traditions.

---

## Ketu (South Node)

**Signifies:** detachment, unresolved past-life/ancestral karma, spirituality,
endings, disconnection. Also a shadow/mathematical point.

**Relevant when:** currently a dasha lord, conjunct malefics, or placed in a
house whose matters feel chronically unresolved or repeatedly "let go of."

**Upaya:**
- Donate sesame or multi-colored items, ideally on Saturdays.
- Worship Ganesha.
- Engage in meditation, spiritual study, or ancestor-honoring practice (Pitru
  Tarpana) rather than resisting detachment where Ketu sits.
- Where Ketu occupies a house, the traditional advice is often to lean into
  its detachment rather than force attachment against it.

**Mantra:** Beej mantra *Om Sraam Sreem Sraum Sah Ketave Namah*; Ganesha
mantra *Om Gam Ganapataye Namah*.

**Why:** Ketu represents karmic release and spiritual detachment. Ganesha -
remover of obstacles and patron of new beginnings - is invoked to help
integrate Ketu's disruptive energy as a completion/release rather than pure
loss. The advice to "lean into detachment" reflects the tradition's own
framing of Ketu: fighting its nature is considered less effective than
working with it.

---

## Sade Sati / Ashtama Shani protocol

When `sade_sati_status` shows an active phase (rising/peak/setting) or
Ashtama Shani, the classical guidance converges on the Saturn remedies above,
applied more consistently for the duration of the transit rather than as a
one-time act:
- Saturday donations (black sesame, mustard oil, iron, black cloth) kept up
  weekly, not just once.
- Regular Hanuman worship - this combination is one of the most consistently
  repeated recommendations across sources for Sade Sati specifically.
- Avoid major irreversible decisions driven by impatience during the peak
  phase where possible - the tradition frames this window as one for
  endurance and structural change, not for shortcuts.
- Note explicitly to the user that Sade Sati is widely feared in folk
  practice well beyond what classical texts themselves claim, and that not
  every Sade Sati is difficult - its actual effect depends on Saturn's natal
  dignity and the houses involved, which the reading should already have
  covered.

---

## General principles (repeat these to the user)

- Tie remedies to what's actually weak, afflicted, or currently active in
  *this* chart - not a generic nine-planet checklist.
- These address the traditional/psychological/behavioral layer. They are not
  a substitute for medical, legal, financial, or mental-health care, and
  should never be framed as required for safety or as guaranteed to produce
  an outcome.
- Gemstones: don't prescribe them here - point to an in-person practitioner.
- Mantra repetition is traditionally often done in multiples of 108 (a full
  mala), but there's no single universally "correct" count across sources -
  frame any count you mention as a common convention, not a precise
  requirement.
