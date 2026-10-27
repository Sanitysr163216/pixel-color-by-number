# Design notes

The rules as specified, how the game reads them, and the defaults chosen where the spec says nothing.
Every number here lives in code and can be changed there (see "Where to change things" at the end).

## Conventions

- **60 frames per second.** All times are frames of 1/60 second. The logic runs at exactly 60 Hz whatever the
  monitor's refresh rate, and the same inputs always give exactly the same fight.
- **Numpad notation** for directions, relative to the way the fighter faces:

  ```
  7 8 9      up-back    up    up-forward
  4 5 6  =   back     neutral   forward
  1 2 3      down-back  down  down-forward
  ```

- **Frame counting.** Frame 1 is the frame the button is pressed.
  `startup: N` means frames 1 to N have no hitbox; the hitbox first appears on frame N + 1.
  The light Rising Push has `startup: 1`, so its hitbox comes out on the second frame.
  After `active` and `recovery`, the fighter can act again on frame startup + active + recovery + 1.
- **Hitstun / blockstun N** are counted after hitstop. The defender can act again on the frame after the N-th.
- **Landing recovery R**: the fighter touches the ground on frame L and can act again on frame L + R.
- **Wakeup W**: the fighter lies on the ground for W frames, counting the frame they touch it. On the next frame
  the hurtbox comes back and the buttons work again, on the same frame.
- **Distances** are pixels of the 304×224 screen (the size of KOF97's picture on the Neo Geo).
  Box positions are measured from the fighter's centre at the feet: x forward, y up.

## Buttons and inputs

- 6 buttons: LP MP HP (punches), LK MK HK (kicks).
- What a press does, in order of priority: Chakra special > special move (CE if two punches or two kicks) >
  command normal (direction + button) > normal (standing, crouching or jumping).
- Motions allow other directions in between, because a stick rolls through them:
  4-2-1-6 also matches 4,1,2,1,2,3,6. 4-2-1-6 must be done within 20 frames, 6-2-3 within 15.
  A half circle forward (4-1-2-3-6) does not count as 4-2-1-6.
- **Input buffer**: a press is remembered for 3 frames while the fighter is busy, so a button pressed just before
  recovery ends still comes out on the first free frame.
- **CE (Chakra Enhance)**: the special's motion with two punches (or two kicks) pressed on the same frame, or the
  second one frame later. Costs 1 bar. With less than 1 bar, the normal version of the heavier button comes out.
- **Moves not made yet** (blank in the spec): the input is read, nothing happens. Training mode shows the input
  as "EMPTY SLOT" or "NOT MADE YET". This covers standing LK/MK/HK, crouching LP/MP/HP/LK/MK, all jumping
  attacks, both CE versions and the Chakra specials.

## Universal rules (from the spec)

| Rule | How it works |
| --- | --- |
| Startup / active / recovery | Every move has all three. The hitbox exists only on active frames. |
| Knockback on every normal | Each move sets `knockback: { distance, speed }` (px, px per frame). Defaults: light 14 px at 3.5, medium 22 px at 4.5, heavy 32 px at 5.5. It starts after hitstop. If the opponent is in the corner, the attacker slides back instead. Specials have knockback too. |
| Hitstun per move | Every move sets its own `hitstun` and `blockstun`. |
| Blocking | Hold back. Crouch (down-back) to block lows; overheads (forward + MK) must be blocked standing. |
| Air blocking | Light and medium normals done from the ground can be blocked in the air; heavies done from the ground can't. Light, medium and heavy attacks done in the air can all be blocked by an airborne opponent. |
| Hit in the air by a light or medium normal | Flips backwards, invulnerable until landing, can't act until landing. |
| Hit in the air by a heavy or a special done from the ground | Knocked down like a sweep; the wakeup count starts when they hit the ground. |
| Acting in the air | After using a move in the air, or after being hit in the air, a fighter can't act until landing. Blocking in the air gives the air attack back. |
| Knockdown and wakeup | Invulnerable from the hit until wakeup. The hurtbox and the buttons come back on the same frame. |
| Meter | 10 bars of 100 points. Blocking: +2 per blocked hit for the defender; the attacker gets nothing for a blocked hit. Hitting: +3 × 1 / 2 / 3 for light / medium / heavy. |
| CE | Alternate version of a special with two buttons, 1 bar. |
| Chakra specials | Moves that cost 1–2 bars. |
| Special properties | Per move, by frame: `invincible`, `airborne`, `vulnerable` (extra damage taken), hurtbox changes, movement. |

## Defaults chosen where the spec says nothing

Please confirm or change these.

1. **Specials done from the ground can't be blocked in the air.** The spec only says this for heavies.
   Per move: `airBlockable`.
2. **A heavy done in the air that hits an airborne opponent flips them** (the knockdown rule names heavies done
   from the ground). Per move: `airHit: 'knockdown'`.
3. **Rising Push knocks down a grounded opponent** (like a dragon punch). Per version: remove `knockdown`.
4. **Jumping attacks have to be blocked standing**, as in SF and KOF. Per move: `guard`.
5. **Hitstop** (both fighters freeze on contact): light 7, medium 9, heavy 11 frames. Per move: `hitstop`.
6. **Wakeup** takes 40 frames; heavy Leopard Strike's knockdown makes it 80.
7. **Character basics**: 1000 health; walk 2.5 px per frame forward, 2 back; jumps have 4 frames on the ground
   first, last about 41 frames and go about 105 px high; forward, neutral and backward jumps only.
8. **Not in the game until the spec asks for them**: dashes, throws, chip damage, cancels (normal into special),
   proximity guard (holding back near an attack makes you block instead of walking away).
9. **Landing during an air attack**: 2 frames before the fighter can act.

## Character 1: Shoto / "zoner"

Current numbers (all first guesses, to tune by playing). S / A / R = startup / active / recovery.

| Input | Move | S | A | R | Damage | Hitstun | Blockstun | Knockback | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 5LP | Palm Strike | 4 | 2 | 7 | 30 | 12 | 8 | 14 px at 3.5 | Hits high: whiffs on crouching opponents |
| 5MP | Twin Palm | 6 | 3 | 11 | 60 | 17 | 13 | 22 px at 4.5 | Both hands |
| 5HP | Donkey Kick | 9 | 4 | 17 | 90 | 21 | 16 | 32 px at 5.5 | Hits high |
| 2HK | Double Spin Sweep | 8 | 12 | 20 | 80 | knockdown | 14 | 32 px at 5.5 | Low. Hitbox alternates front, back, front, back (3 frames each); hits once |
| 6 + MP | Lunging Palm | 8 | 3 | 14 | 55 | 16 | 12 | 22 px at 4.5 | Slides 16 px forward; hitbox reaches past the arm; hurtbox lowered to 64 px |
| 6 + MK | Axe Kick | 18 | 3 | 14 | 70 | 18 | 12 | 22 px at 4.5 | Overhead; moves 21 px forward |
| 4 2 1 6 + LP | Leopard Strike L | 7 | 1 | 10 | 100 | 20 | 12 | 16 px at 4 | Double damage if hit during startup |
| 4 2 1 6 + MP | Leopard Strike M | 9 | 1 | 12 | 120 | 22 | 14 | 22 px at 4.5 | Double damage if hit during startup |
| 4 2 1 6 + HP | Leopard Strike H | 11 | 1 | 32 | 140 | knockdown | 16 | 30 px at 5.5 | Knocks down at once; wakeup ×2; long recovery; double damage if hit during startup |
| 6 2 3 + LK | Rising Push L | 1 | 6 | 0 | 80 | knockdown | 14 | 24 px at 4 | Hitbox from frame 2, forward and up; low jump; 10 frames landing recovery |
| 6 2 3 + MK | Rising Push M | 2 | 8 | 0 | 100 | knockdown | 16 | 26 px at 4.5 | Higher and further; hits directly above the head; 14 landing |
| 6 2 3 + HK | Rising Push H | 5 | 20 | 0 | 120 | knockdown | 18 | 30 px at 5 | Goes much further; near the top the hitbox reaches behind; 18 landing |

Rising Push leaves the ground after its startup; its feet (the hitbox) have no hurtbox. The move ends when the
fighter lands, then the landing recovery applies.

## Still open

- **Forward + MP**: the spec's sentence stops at "lowers the character hitbox and…". Currently it lowers the
  hurtbox, so high attacks like 5LP pass over it. What comes after "and"?
- **Projectiles**: planned. The engine needs a projectile object (own hitbox, speed, lifetime, clash rules);
  it will be added with the first projectile move.
- **Mechanics from Darkstalkers, SSF2T and Third Strike** are expected later. The move data already has room for
  per-frame properties; cancels, chains, parries, guard cancels and similar systems become new fields and states.

## Where to change things

| What | File |
| --- | --- |
| A move's numbers and boxes | `src/characters/shoto/moves.ts` |
| Which input does which move, motions, walk and jump, hurtboxes | `src/characters/shoto/character.ts` |
| Rules for the whole game (meter, buffer, CE window, wakeup, gravity) | `src/config.ts` |
| What every move field means | `src/moves/types.ts` |
| Air block and air hit defaults | `canAirBlock` and `airHitResult` in `src/moves/compile.ts` |
| Placeholder animation | `src/characters/shoto/poses.ts` |
