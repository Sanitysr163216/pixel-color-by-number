# Design notes

The rules as specified, how the game reads them, and the assumptions made where the spec says nothing.
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
- **Wakeup W**: the fighter lies on the ground for W frames, counting the frame they touch it (the timer never
  starts before that). On the next frame the hurtbox comes back and the buttons work again, on the same frame.
- **Distances** are pixels of the 304×224 screen (the size of KOF97's picture on the Neo Geo).
  Box positions are measured from the fighter's centre at the feet: x forward, y up.

## Buttons, inputs and movement

- 6 buttons: LP MP HP (punches), LK MK HK (kicks).
- What a press does, in order of priority: Chakra special > special move (CE with two punches or two kicks) >
  command normal (direction + button) > normal (standing, crouching or jumping).
- Motions allow other directions in between, because a stick rolls through them:
  4-2-1-6 also matches 4,1,2,1,2,3,6. 4-2-1-6 must be done within 20 frames, 6-2-3 within 15.
  A half circle forward (4-1-2-3-6) does not count as 4-2-1-6.
- **Input buffer**, at any moment of the round: a normal pressed 1 frame before it can come out still comes out;
  specials, CE and Chakra specials are remembered for 3 frames.
- **CE (Chakra Enhance)**: the special's motion with two punches (or two kicks) on exactly the same frame. Costs 1 bar.
  With no bar, or while the CE move isn't made yet, the two buttons do the lighter button's version of the special.
- **Several buttons on the same frame** with no move for that combination: only the lightest one comes out
  (LP + HP = LP). Between a punch and a kick of the same strength, the punch.
- **Moves not made yet** (blank in the spec): the input is read, nothing happens. Training mode shows the input
  as "EMPTY SLOT". The list is under Character 1 below.
- **Walk** forward and back, **jump** forward, neutral or backward.
- **Dash**: tap forward twice (6-5-6 within 12 frames). The fighter runs forward continuously while forward is held;
  any other input stops it at once. Attacks can't be used during the dash.
- **Back hop**: tap back twice (4-5-4). A short hop backwards, like Bishamon's in Vampire Savior. Air normals can be
  used until the fighter lands.

## Rules

| Rule | How it works |
| --- | --- |
| Startup / active / recovery | Every move has all three. The hitbox exists only on active frames. |
| Knockback on every normal | Each move sets `knockback: { distance, speed }` (px, px per frame). Defaults: light 14 px at 3.5, medium 22 px at 4.5, heavy 32 px at 5.5. It starts after hitstop. If the opponent is in the corner, the attacker slides back instead. Specials have knockback too. |
| Hitstun per move | Every move sets its own `hitstun` and `blockstun`. |
| Hitstop | Set per character, defaults: moves done from the ground 7 / 9 / 11 frames (light / medium / heavy); moves done in the air against a grounded opponent 7 for every move; air against air 3 on hit, 7 on block. A single move can set its own. |
| Blocking | Hold back. Crouch (down-back) to block lows; overheads must be blocked standing. Forward + MK is an overhead, and every move done in the air is an overhead unless the move says otherwise. |
| Proximity guard | While holding back, the fighter goes into the block stance from 2 frames before the opponent's first active frame, if the attack would reach them where they stand. They stop walking backward. |
| Blockstrings | Once a fighter blocks, every hit that arrives while they are still in blockstun is blocked too, even if they let go of back, highs and lows alike. |
| Air blocking | Normals done from the ground: light and medium can be blocked in the air, heavies can't. Specials done from the ground can't be blocked in the air, including ones that leave the ground themselves (Rising Push). Anything done after jumping (normals or specials) can be blocked by an airborne opponent. |
| Hit in the air by a normal | A light or medium normal done from the ground, or any normal done in the air: the opponent flips backwards, invulnerable until landing, and can't act until landing. |
| Hit in the air by a heavy or a special done from the ground | Knocked down like a sweep; the wakeup count starts when they hit the ground. Rising Push also knocks down an opponent on the ground. |
| Acting in the air | After using a move in the air, or after being hit in the air, a fighter can't act until landing. Blocking in the air gives the air attack back. |
| Knockdown and wakeup | Invulnerable from the hit until wakeup. The hurtbox and the buttons come back on the same frame. |
| Chains | A normal that connects, on hit or block, can be cancelled into a different normal (command normals included) pressed during the hitstop, or 1 frame before the hit as a buffer. The new normal starts when the hitstop ends. A combo or blockstring can't use the same chain twice: 5LP into 5MP once, while 5MP into 5LP is a different chain. No chains in the air. |
| Special cancels | A normal (not a command normal) can be cancelled into a special, CE or Chakra special, on hit or block, unless that normal was itself reached by a chain. The special has to be pressed between the hit (or up to 3 frames before it, as a buffer) and the end of the normal's active frames. No cancels in the air. |
| Combo counter | Counts every hit until the defender leaves hit stun; shown on the attacker's side from 2 hits; stays 2 seconds after the combo ends; a new combo of 2 or more hits replaces it. |
| Meter | 10 bars of 100 points. Blocking: +2 per blocked hit for the defender; the attacker gets nothing for a blocked hit. Hitting: +3 × 1 / 2 / 3 for light / medium / heavy. |
| CE | Alternate version of a special with two buttons, 1 bar. |
| Chakra specials | Moves that cost 1–2 bars. |
| Special properties | Per move, by frame: `invincible`, `airborne`, `vulnerable` (extra damage taken), hurtbox changes, movement. |

Blockstrings still follow the air-block rules: a grounded heavy can't be blocked in the air even in the middle of a
blockstring.

## Assumptions to confirm

1. **A blockstring can't reuse a chain either**, the same as a combo. Otherwise chains on block could loop forever.
2. **Same-strength buttons together** (LP + LK): the punch comes out.
3. **Landing during an air attack**: 2 frames before the fighter can act.

## Character 1: Shoto / "zoner"

Current numbers (all first guesses, to tune by playing). S / A / R = startup / active / recovery.

| Input | Move | S | A | R | Damage | Hitstun | Blockstun | Knockback | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 5LP | Palm Strike | 4 | 2 | 7 | 30 | 12 | 8 | 14 px at 3.5 | Hits high: whiffs on crouching opponents |
| 5MP | Twin Palm | 6 | 3 | 11 | 60 | 17 | 13 | 22 px at 4.5 | Both hands |
| 5HK | Donkey Kick | 9 | 4 | 17 | 90 | 21 | 16 | 32 px at 5.5 | Hits high |
| 2HK | Double Spin Sweep | 8 | 12 | 20 | 80 | knockdown | 14 | 32 px at 5.5 | Low. Hitbox alternates front, back, front, back (3 frames each); hits once |
| 6 + MP | Lunging Palm | 8 | 3 | 14 | 55 | 16 | 12 | 22 px at 4.5 | Both arms thrown out in opposite directions, like Yun's in Third Strike. Slides 16 px forward, hits far (64 px), hitbox 16 px past the arm, hurtbox lowered to 64 px |
| 6 + MK | Axe Kick | 18 | 3 | 14 | 70 | 18 | 12 | 22 px at 4.5 | Overhead; moves 21 px forward |
| 4 2 1 6 + LP | Leopard Strike L | 7 | 1 | 10 | 100 | 20 | 12 | 16 px at 4 | Double damage if hit during startup |
| 4 2 1 6 + MP | Leopard Strike M | 9 | 1 | 12 | 120 | 22 | 14 | 22 px at 4.5 | Double damage if hit during startup |
| 4 2 1 6 + HP | Leopard Strike H | 11 | 1 | 32 | 140 | knockdown | 16 | 30 px at 5.5 | Knocks down at once; wakeup ×2; long recovery; double damage if hit during startup |
| 6 2 3 + LK | Rising Push L | 1 | 6 | 0 | 80 | knockdown | 14 | 24 px at 4 | Hitbox from frame 2, forward and up; low jump; 10 frames landing recovery |
| 6 2 3 + MK | Rising Push M | 2 | 8 | 0 | 100 | knockdown | 16 | 26 px at 4.5 | Higher and further; hits directly above the head; 14 landing |
| 6 2 3 + HK | Rising Push H | 5 | 20 | 0 | 120 | knockdown | 18 | 30 px at 5 | Goes much further; near the top the hitbox reaches behind; 18 landing |

Rising Push leaves the ground after its startup; its feet (the hitbox) have no hurtbox. The move ends when the
fighter lands, then the landing recovery applies.

Not made yet (the input is read, nothing happens): standing HP, LK, MK; crouching LP, MP, HP, LK, MK; every
jumping attack; both CE versions; the Chakra specials.

Other numbers: 1000 health; walk 2.5 px per frame forward, 2 back; jumps have 4 frames on the ground first, last
about 41 frames and go about 105 px high; wakeup 40 frames (80 after heavy Leopard Strike). Dash and back hop are
estimates of Bishamon's, scaled to this character's size: dash 5 px per frame; back hop leaves the ground at once,
about 19 frames in the air and about 66 px back, no invulnerability.

## Planned

- **Projectiles.** The engine needs a projectile object (own hitbox, speed, lifetime, clash rules); it will be added
  with the first projectile move.
- **Mechanics from Darkstalkers, SSF2T and Third Strike.** The move data has room for per-frame properties; systems
  like parries or guard cancels become new fields and states.

## Where to change things

| What | File |
| --- | --- |
| A move's numbers and boxes | `src/characters/shoto/moves.ts` |
| Which input does which move, motions, walk, jump, dash, back hop, hurtboxes, hitstop table | `src/characters/shoto/character.ts` |
| Rules for the whole game (meter, buffers, CE window, double-tap window, proximity guard, wakeup, gravity) | `src/config.ts` |
| What every move field means | `src/moves/types.ts` |
| Air block and air hit defaults | `canAirBlock` and `airHitResult` in `src/moves/compile.ts` |
| Chains, cancels, blocking, dash | `src/sim/world.ts` |
| Placeholder animation | `src/characters/shoto/poses.ts` |
