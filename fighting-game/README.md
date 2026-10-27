# Fighting game prototype

**English** | [中文](README.zh-CN.md)

A 6-button 2D fighting game in the style of KOF97, running in the browser. This first build has
Character 1 (Shoto) with every move from the spec, a training mode and a two-player versus mode.
The fighters are placeholder figures until real sprites exist.

The rules, frame counting and current frame data are in [docs/design.md](docs/design.md).

## Run it

Needs [Node.js](https://nodejs.org) 20 or newer.

```sh
cd fighting-game
npm install
npm run dev        # opens a local address to play at, reloads when files change
npm test           # 70 frame-exact tests of the rules
npm run build      # a finished copy in dist/, for any web host
```

## Controls

| | Player 1 | Player 2 (versus mode) |
| --- | --- | --- |
| Move / jump / crouch | W A S D | Arrow keys |
| LP MP HP | U I O | Numpad 4 5 6 |
| LK MK HK | J K L | Numpad 1 2 3 |
| Gamepad | first pad: X Y RB = punches, A B RT = kicks | second pad |

Hold back to block, down-back to block lows.

Training keys: `1` boxes, `2` frame data, `3` pause, `4` next frame (while paused), `5` dummy stand / crouch /
jump, `6` dummy blocks, `7` training / versus, `8` full meter, `0` reset positions.

Two people on one keyboard will hit key limits (many keyboards can't read that many keys at once);
use at least one gamepad for versus.

## Changing a move

Every move is one block of numbers in `src/characters/shoto/moves.ts`, for example:

```ts
export const standLP: MoveData = {
  name: 'Palm Strike',
  kind: 'normal',
  strength: 'L',
  startup: 4,          // frames 1–4: no hitbox; the hitbox appears on frame 5
  active: 2,           // the hitbox exists for 2 frames
  recovery: 7,         // then 7 frames before the fighter can act again
  damage: 30,
  hitstun: 12,
  blockstun: 8,
  knockback: { distance: 14, speed: 3.5 },   // pixels, pixels per frame
  hitboxes: [{ boxes: [{ x: 24, y: 70, w: 22, h: 14 }] }],
  hurtboxes: [{ frames: [5, 9], boxes: [{ x: 10, y: 72, w: 26, h: 10 }] }],
};
```

`src/moves/types.ts` explains every field. A wrong number (for example a hitbox outside the active frames)
stops the game with a message naming the move. Run `npm test` after a change: the tests check the rules,
not the exact numbers, so tuning a move doesn't break them.

## How it is built

- **TypeScript**, no game engine. The fight (`src/sim/`) is plain code that advances exactly one frame at a
  time with whole-number positions, so the same inputs always give the same fight. That makes the tests
  exact and leaves the door open for replays and online play.
- **Moves are data** (`src/characters/`), compiled and checked at start-up (`src/moves/compile.ts`).
- **Drawing** (`src/render/`) is done pixel by pixel into a 304×224 picture, the size of the KOF97 screen,
  then scaled up with hard edges.
- **Vite** builds the page, **Vitest** runs the tests.

```
src/
  config.ts            rules for the whole game
  characters/shoto/    Character 1: moves, inputs, placeholder animation
  moves/               move fields and checks
  input/               buttons, motions (4-2-1-6, 6-2-3), input history
  sim/                 the fight: states, hits, blocking, knockback, meter
  game/                training and versus modes, keyboard and gamepads
  render/              pixels, stage, fighters, HUD, training overlays
tests/                 frame-by-frame tests of every rule
docs/design.md         rules, defaults, frame data, open questions
```
