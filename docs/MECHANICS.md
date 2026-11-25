# Mechanics

How the cards of the night rewrite the rules of the Codex. (The hidden formulas that decide
which **rites** a note performs are deliberately not here; they live in
[Forbidden Lore](FORBIDDEN_LORE.md).)

## The draw

* Each Codex has a private random **soul secret**. The five cards of a day are derived from it
  and the date with HMAC-SHA256 and a SHA-256 counter-mode stream (`nocturne/rng.py`), shuffled
  with Fisher–Yates. The hand is therefore **fixed** for that day (drawing again shows the same
  five) and **unique** to every day and every Codex.
* About **one card in three falls reversed**.
* The hand is recorded when first drawn, so a past night keeps its cards forever, even if a
  future version of the Codex changes the deck.
* You may perform the ritual only for **today**. Past nights without a ritual stay
  *unobserved*, and the future is veiled.

## The positions

You keep three cards. The order in which you choose them assigns their positions:

| Position | Governs |
|---|---|
| ♔ **The Crown** (first kept) | The night's **aspect**: palette, ambient particles, musical mode and root note. Its number is the *Crown's number* used by one of the rites. Reversed, the aspect is **eclipsed**: dimmed colours, a violet glow and the Locrian mode. |
| ❦ **The Heart** (second kept) | The **resonant number** (the card's number reduced to one digit; the Fool counts as 22), and the **awakened** sigils. Reversed, the number is reflected (*n → 10 − n*) and a minor card awakens the opposite element. |
| ☾ **The Shadow** (third kept) | The night's **constraint**. Reversed, the curse breaks into a **boon**. |
| 🜂 **The Ashes** (the two burned) | A burned minor card **banishes** its element: those sigils crumble to ash and take no part in any rite. A burned Major **forbids** its ruling sigil: using it binds the note in chains. |

Banishment beats awakening: a sigil can never be both. Each Major Arcanum kept in any position
also brings its **arcanum** (below).

## Minor Arcana

| Suit | Element | Crown aspect | Crown mode | Heart awakens | Shadow (upright) | Shadow (reversed) |
|---|---|---|---|---|---|---|
| Wands | fire | Aspect of Embers · embers | phrygian | fire sigils | **Ember Tithe**: every note needs 1 sigil (2 from the Eight, 3 from the Knight) | **Free Flame**: fire sigils awakened |
| Cups | water | Aspect of Tides · droplets | aeolian | water sigils | **Tide of Forgetting**: notes fade unless you draw near | **The Tide Returns**: a past note echoes back |
| Swords | air | Aspect of Whispers · feathers | dorian | air sigils | **Vow of Brevity**: a character limit by rank | **Unbound Tongue**: no limit, and the quill sings |
| Pentacles | earth | Aspect of Stones · spores | harmonic minor | earth sigils | **Weight of Stone**: notes anchored (and music stilled from the Ten) | **Bedrock Ward**: no note can be bound |

The rank shades the colour and shifts the root note. **Vow of Brevity** limits by rank:
Ace → 999, Two → 888, Three → 777, Four → 666, Five → 616, Six → 555, Seven → 444, Eight → 404, Nine → 333, Ten → 313, Page → 222, Knight → 213, Queen → 144, King → 111.

## Major Arcana

| # | Card | Rules | Arcanum | Boon — in the Crown, the Heart, or a reversed Shadow | Curse — upright in the Shadow |
|---|---|---|---|---|---|
| 0 | The Fool | 🜁 | `wild` | **The Wild Card.** The Fool's sigil 🜁 counts as every element tonight. | **Fool's Errand.** The sigil palette is scrambled into a new order. |
| I | The Magician | ☿ | `four_tools` | **The Four Tools.** All four element sigils are awakened, and a storm needs only two of a kind. | **Sleight of Hand.** One sigil has been spirited away: it is forbidden tonight. |
| II | The High Priestess | ☥ | `veil` | **Veil of Isis.** Notes stay veiled until you draw near, and ☥ is awakened. | **Vow of Secrecy.** Notes are veiled, and none may exceed 777 characters. |
| III | The Empress | ♀ | `bloom` | **Bloom.** Petals follow every inscription, and ♀ alone calls the Petal Rain. | **Overgrowth.** Every note must grow to at least 13 words. |
| IV | The Emperor | ♂ | `decree` | **Imperial Ledger.** Notes fall into stately ranks, and the Crown's number may be met within one. | **Iron Decree.** Notes are anchored where they fall, and none may exceed 666 characters. |
| V | The Hierophant | ✠ | `illuminate` | **Illumination.** Notes open with gilded initials, and two crosses suffice for the Trinity. | **Liturgy.** Every note must begin with a sigil. |
| VI | The Lovers | ❦ | `twin` | **Kindred.** Any sigil written twice, anywhere in a note, calls the Twin Flames. | **Severed Pair.** Sigils must come in pairs: an even number in every note. |
| VII | The Chariot | ☄ | `velocity` | **Momentum.** A velocity gauge rides with your quill; swift writing summons the Streak. | **Runaway Reins.** Your notes drift across the board of their own accord. |
| VIII | Strength | 🜍 | `ward` | **Fortitude.** Forbidden sigils lose their bite: no note can be bound tonight. | **The Leash.** No note may exceed 444 characters. |
| IX | The Hermit | ✶ | `lantern` | **Lantern Vigil.** The first note of the night is lit by the Hermit's lantern. | **Solitude.** Darkness falls: only a lantern lights the page, and the music is silent. |
| X | Wheel of Fortune | ♃ | `wheel` | **Turning Fortune.** The resonant number turns with every hour. | **Spin of Fate.** The resonant number turns each hour, and the sigil palette is scrambled. |
| XI | Justice | ⚖ | `balance` | **Even Scales.** A single light and a single dark sigil suffice to balance the scales. | **Scales Demand.** Light and dark sigils must be equal in every note. |
| XII | The Hanged Man | 🜄 | `inversion` | **New Perspective.** A palindrome anywhere in a note, not only in its title, calls the Mirror. | **Inversion.** The night hangs upside down: the title is mirrored and new notes sink beneath old. |
| XIII | Death | ☠ | `moths` | **Memento Mori.** ☠ calls the moths at any hour, and deleted notes leave as moths. | **Memento.** Tonight's notes fade unless you draw near, and deleted notes leave as moths. |
| XIV | Temperance | ⚗ | `fusion` | **Alchemy.** Opposite elements anywhere in a note call the Conjunction. | **Measured Breath.** No note may exceed 333 characters. |
| XV | The Devil | ⛧ | `chains` | **Temptation.** Every dark sigil is awakened. | **The Pact.** Two sigils are forbidden; using one binds the note in chains. |
| XVI | The Tower | ☈ | `tremor` | **Revelation.** A single exclamation beneath ☈ calls the lightning. | **Upheaval.** The board quakes with every inscription, and the notes scatter. |
| XVII | The Star | ✦ | `starfield` | **Constellation.** Each note lights a star, and a single star sigil calls the Starfall. | **Starless Night.** The sky is empty and the music silent; only your notes light stars. |
| XVIII | The Moon | ☽ | `illusion` | **Lunar Hours.** The Witching Hour lasts the whole night, from nine until five. | **Lunacy.** The ink shimmers and wavers, and the Witching Hour lasts all night. |
| XIX | The Sun | ☉ | `gilded` | **Radiance.** Every light sigil is awakened. | **Glare.** The Codex burns too bright, and ☽ is forbidden. |
| XX | Judgement | 🜂 | `echo` | **The Calling.** A voice from a past night returns to the board. | **Reckoning.** A past note returns, and every note must bear 🜂. |
| XXI | The World | ♄ | `ouroboros` | **Completion.** The four elements alone close the Ouroboros. | **Unfinished.** Every note must bear at least four sigils. |

When a Major sits in the Crown it brings its own aspect:

| Card | Palette accent | Particles | Mode |
|---|---|---|---|
| The Fool | `#8fd3c4` | feathers | lydian |
| The Magician | `#f2c14e` | motes | mixolydian |
| The High Priestess | `#6c7fd1` | motes | aeolian |
| The Empress | `#d46a8c` | petals | ionian |
| The Emperor | `#c0392b` | embers | harmonic minor |
| The Hierophant | `#c8a96e` | motes | dorian |
| The Lovers | `#e05a7a` | petals | lydian |
| The Chariot | `#5b8def` | motes | mixolydian |
| Strength | `#e07b39` | embers | harmonic minor |
| The Hermit | `#f0b75a` | motes | dorian |
| Wheel of Fortune | `#9d7bd8` | stars | lydian |
| Justice | `#c9c3b0` | ash | ionian |
| The Hanged Man | `#3fa7a0` | droplets | phrygian |
| Death | `#d9d2c0` | ash | locrian |
| Temperance | `#7ec8e3` | droplets | dorian |
| The Devil | `#8b0a1a` | embers | hungarian minor |
| The Tower | `#ff7b29` | ash | double harmonic |
| The Star | `#7fb7ff` | stars | lydian |
| The Moon | `#a9b8d6` | motes | aeolian |
| The Sun | `#e6b422` | motes | ionian |
| Judgement | `#ff9a3c` | embers | mixolydian |
| The World | `#6fbf73` | spores | ionian |

### What the effects do

| Effect | On the board |
|---|---|
| veil | Notes are blurred until you hover over them |
| fading | Notes are faint until you hover over them |
| lantern | Darkness falls; only a lantern of light follows your cursor |
| starfield | Each note lights a star; the night's stars join into a constellation |
| mirror | The title is mirrored and new notes sink beneath old ones |
| illusion | Ink shimmers and wavers |
| gilded | Gold light and borders; the Sun's glare |
| illuminate | Notes open with gilded blackletter initials |
| bloom | Petals fall with every inscription |
| drift | Notes drift slowly across the board |
| tremor / scatter | The board quakes on every inscription; the other notes scatter |
| anchored | Notes cannot be moved once placed |
| grid | Notes fall into stately ranks |
| scramble | The sigil palette is shuffled |
| velocity | A gauge measures how fast you write |
| echo | A note from a past night returns to the board |
| silence | The ambient organ is stilled |
| quill_song | Each keystroke plays a note of the night's mode |
| moths | Burned (deleted) notes leave as a cloud of moths |
| chains | Forbidden sigils are marked with chains |

## Sigils

| Glyph | Name | Shortcode | Element | Polarity | Value | Ruled by |
|---|---|---|---|---|---|---|
| 🜁 | Air | `:air:` | air | light | 22 | The Fool |
| ☿ | Mercury | `:mercury:` | air | light | 1 | The Magician |
| ☥ | Ankh | `:ankh:` | water | light | 2 | The High Priestess |
| ♀ | Venus | `:venus:` | earth | light | 3 | The Empress |
| ♂ | Mars | `:mars:` | fire | dark | 4 | The Emperor |
| ✠ | Cross Pattée | `:cross:` | earth | light | 5 | The Hierophant |
| ❦ | Floral Heart | `:heart:` | air | light | 6 | The Lovers |
| ☄ | Comet | `:comet:` | water | light | 7 | The Chariot |
| 🜍 | Sulfur | `:sulfur:` | fire | dark | 8 | Strength |
| ✶ | Lantern Star | `:lantern:` | earth | light | 9 | The Hermit |
| ♃ | Jupiter | `:jupiter:` | air | light | 10 | Wheel of Fortune |
| ⚖ | Scales | `:scales:` | air | light | 11 | Justice |
| 🜄 | Water | `:water:` | water | dark | 12 | The Hanged Man |
| ☠ | Skull | `:skull:` | water | dark | 13 | Death |
| ⚗ | Alembic | `:alembic:` | fire | light | 14 | Temperance |
| ⛧ | Inverted Pentagram | `:pact:` | earth | dark | 15 | The Devil |
| ☈ | Thunder | `:thunder:` | fire | dark | 16 | The Tower |
| ✦ | Star | `:star:` | air | light | 17 | The Star |
| ☽ | Luna | `:luna:` | water | dark | 18 | The Moon |
| ☉ | Sol | `:sol:` | fire | light | 19 | The Sun |
| 🜂 | Fire | `:fire:` | fire | light | 20 | Judgement |
| ♄ | Saturn | `:saturn:` | earth | dark | 21 | The World |
| 🜃 | Earth | `:earth:` | earth | dark | 4 | — |
| ⛤ | Quintessence | `:quintessence:` | spirit | light | 5 | — |

* A sigil's **value** is the number of the card that rules it.
* The Fool's **wild** sigil 🜁 (when the Fool is kept) counts as every element.
* ⛤ Quintessence can stand in for one missing element in the Ouroboros.
* Type a shortcode such as `:sol:` and it turns into its glyph as you write.

## Constraints

When a note breaks an edict, the Quill lists what is wrong (✗) and the server refuses the ink
with a clear message. Possible edicts: a character limit (counted on the body), a minimum
number of sigils, a minimum number of words, *begins with a sigil*, *sigils in pairs*, *light
and dark balanced*, and *must bear* a given sigil.

## Writing rules

* Notes may be written and edited only on the night they belong to. At midnight the night is
  sealed: you can read, recite and burn its notes, but not change them.
* A note that uses a **forbidden** sigil (without a ward) is **bound in chains** and can never be
  edited again.
* Burning (deleting) a note is always allowed: your privacy outranks every edict.

## Houses

Each sealed night is presided over by one of twelve Houses, chosen from the kept cards. Its
crest seals every note of the night.

| House | Motto | Arms |
|---|---|---|
| House Vesperine | *We keep the last light.* | gothic shield, per pale sable and argent, a candle or |
| The Ashen Cantors | *Sing, though the throat be smoke.* | heater shield, chief cinder and or, a moth argent |
| Order of the Pale Chalice | *Drink, and remember.* | kite shield, bordure azure and argent, a chalice argent |
| House Ravenmourne | *Nevermore is not never.* | heater shield, per bend sable and gules, a raven argent |
| The Thornwake Covenant | *Every rose is a wound kept.* | french shield, quarterly vert and argent, a rose gules |
| House Gloamspire | *Above the fog, the bells.* | swiss shield, per fess purpure and sable, a tower or |
| The Lantern Wardens | *Hold the flame, not the hand.* | gothic shield, plain sable and or, a lantern or |
| House Morrowbane | *Tomorrow is a debt.* | heater shield, per saltire argent and sable, a hourglass gules |
| Order of the Hollow Crown | *Kings are only heavy hats.* | kite shield, chevron gules and or, three crown or |
| The Drowned Bell | *Toll beneath the waves.* | french shield, barry azure and argent, a bell sable |
| House Sepulchre | *We are what remains.* | heater shield, per pale sable and cinder, a skull argent |
| The Starless Synod | *Count the dark between.* | gothic shield, gyronny purpure and sable, a star8 argent |

The **Forge** (Tome → Houses) turns any name or motto into a personal crest. The same name
always forges the same arms.
