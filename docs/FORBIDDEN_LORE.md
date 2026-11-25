# ⚠ Forbidden Lore

> *Turn back now if you would rather discover the rites yourself.* Every hidden formula of
> the Codex is written below. The Codex itself only ever shows a riddle until you perform a
> rite for the first time.

## How a note is weighed

When you inscribe a note, `nocturne/arcane.py` measures:

* **Weight**: the sum of the letters of title and body (A=1 … Z=26; accents are folded and
  sigils, digits and punctuation weigh nothing).
* **Root**: the weight reduced by repeated digit sums to a single digit. The *master root*
  stops at 11, 22 or 33.
* **Sigils**: which sigils appear, in order, and which are *active* (not banished, not
  forbidden). Active sigils standing **side by side** (separated only by spaces) form pairs.
* **Sigil sum**: the sum of the values of the active sigils.
* The **hour** you wrote at, the number of **exclamation marks**, **palindromes**, and your
  writing **velocity** (characters a minute, measured by the Quill).

Rites are checked from grandest to least. At most **3** are performed per note
(consequences such as chains and ashes always play first). If nothing stirs, the ink simply
settles. A rite performed with an **awakened** sigil is *awakened*: stronger, brighter and
louder.

The **omen candle** beside the Inscribe button lights one flame for each rite your draft would
perform, without saying which.

## The 29 rites

### The Ouroboros

*grand rite* · animation `ouroboros` · sound `serpent`

> Gather the four, and let the end bite the beginning.

Bear sigils of all four elements, and begin and end with the same sigil (five or more). Under the World, the four alone suffice. The Fool's wild sigil counts as every element, and ⛤ may stand in for one that is missing.

### The Master Number

*grand rite* · animation `master` · sound `organ`

> Some numbers refuse to be reduced.

When a note's weight reduces to 11, 22 or 33 before becoming a single digit.

### Resonance

*grand rite* · animation `resonance` · sound `chord`

> Words have weight. Weigh them to the number the Heart keeps.

Sum the letters (A=1 … Z=26) of title and body and reduce the sum to one digit. If it equals the Heart's number, the night resonates. Under the Wheel the number turns with the hour.

### The Crown Remembers

*grand rite* · animation `crown` · sound `fanfare`

> Offer the Crown a tribute of sigils equal to its number.

If the values of two or more sigils sum to the Crown card's number, the Crown remembers you. A sigil's value is the number of the card that rules it. Under the Emperor, within one is close enough.

### The Eclipse

*major rite* · animation `eclipse` · sound `eclipse`

> When the sun and the moon stand side by side.

Set ☉ and ☽ next to one another.

### The Blood Moon

*major rite* · animation `bloodmoon` · sound `heartbeat`

> The moon drinks what Mars spills.

Set ☽ beside ♂ — or bear ☽ and write the word 'blood'.

### The Thirteenth Toll

*major rite* · animation `toll` · sound `toll`

> Thirteen is a door. Make your weight knock upon it.

A note whose weight (the sum of its letters) is a multiple of thirteen.

### The Witching Hour

*major rite* · animation `witching` · sound `witching`

> Some ink only wakes at midnight.

Inscribe between midnight and one, or at exactly 3:33. Under the Moon the hour lasts from nine at night until five.

### Nevermore

*major rite* · animation `raven` · sound `raven`

> Quoth a certain dark bird…

Write the word 'nevermore'.

### Night Moths

*major rite* · animation `moths` · sound `flutter`

> Bones draw moths — but only after dark.

Bear ☠ between nine at night and five in the morning (at any hour under Death).

### The Tower Strike

*major rite* · animation `lightning` · sound `thunder`

> Shout thrice beneath the storm.

Bear ☈ and three exclamation marks (one under the Tower).

### The Even Scales

*major rite* · animation `scales` · sound `scales`

> Light and shadow, weighed and found equal.

Use as many light sigils as dark ones, at least two of each (one under Justice).

### Twin Flames

*minor rite* · animation `twin` · sound `twin`

> Two candles, one flame.

Write the same sigil twice in a row. Under the Lovers, anywhere in the note.

### The Conjunction

*major rite* · animation `conjunction` · sound `alchemy`

> Marry fire to water, or air to earth.

Set sigils of opposite elements side by side. Under Temperance, anywhere.

### Ember Storm

*minor rite* · animation `embers` · sound `fire`

> Three sparks make a wildfire.

Three fire sigils in one note (two under the Magician).

### The Drowned Tide

*minor rite* · animation `tide` · sound `water`

> Three drops make a flood.

Three water sigils in one note (two under the Magician).

### Gale of Feathers

*minor rite* · animation `gale` · sound `wind`

> Three breaths make a storm.

Three air sigils in one note (two under the Magician).

### Thornbloom

*minor rite* · animation `thorns` · sound `creak`

> Three stones make a garden of thorns.

Three earth sigils in one note (two under the Magician).

### Starfall

*minor rite* · animation `starfall` · sound `sparkle`

> Wish upon enough stars and they fall to you.

Three star sigils — ✦ ✶ ☄ — in one note (one under the Star).

### Petal Rain

*minor rite* · animation `petals` · sound `harp`

> Love grows where Venus walks beside a heart.

Bear ♀ together with ❦ (♀ alone under the Empress).

### Mirror of Mercury

*major rite* · animation `quicksilver` · sound `glass`

> Words that read the same in the looking-glass.

Title the note with a palindrome of five letters or more, or set ☿ three times. Under the Hanged Man, a palindrome anywhere will do.

### The Wordless Prayer

*major rite* · animation `prayer` · sound `choir`

> Speak only in signs.

A note of three or more sigils and not a single word.

### Prime Glint

*minor rite* · animation `glint` · sound `glint`

> Indivisible weights shine alone.

A note whose weight is a prime number greater than one hundred.

### The Chariot Streak

*minor rite* · animation `streak` · sound `gallop`

> Ride the quill faster than thought.

Write sixty characters or more at 250 characters a minute (150 under the Chariot).

### Lantern Vigil

*minor rite* · animation `lantern` · sound `chime`

> A small light for the hour before dawn.

Bear ✶ between four and six in the morning — or, under the Hermit, inscribe the night's first note.

### Trinity of Rays

*major rite* · animation `rays` · sound `choir`

> Three crosses raise a cathedral of light.

Bear ✠ three times (twice under the Hierophant).

### Chains of the Pact

*consequence rite* · animation `chains` · sound `chains`

> Use what was forbidden.

A forbidden sigil binds the note in chains: it can no longer be edited.

### The Ward Holds

*consequence rite* · animation `ward` · sound `ward`

> Defy the forbidden beneath a ward.

Under Strength or a Bedrock Ward, forbidden sigils are inert and bind nothing.

### Ashes

*consequence rite* · animation `ash` · sound `fizzle`

> Use what was banished.

Sigils of a banished element crumble to ash and take no part in any rite.

