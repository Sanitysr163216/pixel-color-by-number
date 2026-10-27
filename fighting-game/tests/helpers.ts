import { CHARACTERS } from '../src/characters';
import { compileCharacter, type CompiledCharacter } from '../src/characters/compile';
import { shoto } from '../src/characters/shoto/character';
import type { CharacterData } from '../src/characters/types';
import { px } from '../src/core/units';
import { BTN, NEUTRAL, type ButtonName, type RawInput } from '../src/input/buttons';
import type { MoveData } from '../src/moves/types';
import type { Fighter } from '../src/sim/fighter';
import { World } from '../src/sim/world';

/** Two Shotos `gap` px apart in the middle of the stage, P1 on the left facing right. */
export function newWorld(gap = 60, chars: [CompiledCharacter, CompiledCharacter] = [CHARACTERS.shoto, CHARACTERS.shoto]): World {
  const w = new World(chars);
  w.resetRound(gap);
  return w;
}

/**
 * One frame of input in numpad notation, seen by a fighter facing `facing` (P1 starts facing right = 1,
 * P2 facing left = -1). Buttons are pressed on this frame.
 */
export function inp(dir = 5, buttons: ButtonName[] = [], facing = 1): RawInput {
  const x = (((dir - 1) % 3) - 1) * facing;
  const y = dir <= 3 ? -1 : dir >= 7 ? 1 : 0;
  const mask = buttons.reduce((m, b) => m | BTN[b], 0);
  return { x, y, held: mask, pressed: mask };
}

/** P2 input (facing left at the start). */
export function inp2(dir = 5, buttons: ButtonName[] = []): RawInput {
  return inp(dir, buttons, -1);
}

/** Steps the world once per input; the shorter list is padded with neutral. */
export function play(w: World, p1: RawInput[], p2: RawInput[] = []): void {
  const n = Math.max(p1.length, p2.length);
  for (let i = 0; i < n; i++) w.step([p1[i] ?? NEUTRAL, p2[i] ?? NEUTRAL]);
}

/** Steps `n` frames holding the same input (buttons count as pressed only on the first frame). */
export function hold(w: World, n: number, p1: RawInput = NEUTRAL, p2: RawInput = NEUTRAL): void {
  for (let i = 0; i < n; i++) {
    w.step([i === 0 ? p1 : { ...p1, pressed: 0 }, i === 0 ? p2 : { ...p2, pressed: 0 }]);
  }
}

/** Steps until `done` is true (at most `limit` frames). Returns the number of frames stepped. */
export function until(w: World, done: () => boolean, p1: RawInput = NEUTRAL, p2: RawInput = NEUTRAL, limit = 600): number {
  for (let n = 1; n <= limit; n++) {
    w.step([p1, p2]);
    if (done()) return n;
  }
  throw new Error('condition never became true');
}

/** The inputs that perform a move of the Shoto, ending with the button press. */
export function inputsFor(id: string, facing = 1): RawInput[] {
  const i = (dir: number, b: ButtonName[] = []) => inp(dir, b, facing);
  const [special, version] = id.split('.');
  const button = (type: 'P' | 'K') => `${version}${type}` as ButtonName;
  if (special === 'leopard') return [i(4), i(2), i(1), i(6, [button('P')])];
  if (special === 'rising') return [i(6), i(2), i(3, [button('K')])];
  const dir = Number(id[0]);
  return [i(dir, [id.slice(1) as ButtonName])];
}

export function distance(w: World): number {
  return Math.abs(w.fighters[1].x - w.fighters[0].x) / px(1);
}

/** Puts a fighter in the air as if jumping, at height `y` px going up at `vy` px/frame. */
export function putInAir(f: Fighter, y: number, vy: number, airActionUsed = false): void {
  f.state = 'jump';
  f.frame = 0;
  f.move = null;
  f.y = px(y);
  f.vy = px(vy);
  f.vx = 0;
  f.airActionUsed = airActionUsed;
}

/** A Shoto with extra moves, for testing rules no real move uses yet (jumping attacks, CE). */
export function testCharacter(extra: { normals?: Partial<CharacterData['normals']>; leopardCE?: MoveData }): CompiledCharacter {
  const data: CharacterData = {
    ...shoto,
    normals: { ...shoto.normals, ...extra.normals },
    specials: shoto.specials.map((s) => (s.id === 'leopard' && extra.leopardCE ? { ...s, CE: extra.leopardCE } : s)),
  };
  return compileCharacter(data);
}

export const jumpLP: MoveData = {
  name: 'Jumping LP',
  kind: 'normal',
  strength: 'L',
  startup: 3,
  active: 4,
  recovery: 6,
  damage: 30,
  hitstun: 12,
  blockstun: 8,
  hitboxes: [{ boxes: [{ x: 6, y: 20, w: 30, h: 40 }] }],
};

export const jumpHP: MoveData = {
  ...jumpLP,
  name: 'Jumping HP',
  strength: 'H',
  startup: 5,
  active: 6,
  recovery: 8,
  damage: 80,
  hitstun: 18,
  blockstun: 14,
};

export const leopardCE: MoveData = {
  name: 'Leopard Strike CE',
  kind: 'ce',
  strength: 'H',
  startup: 5,
  active: 2,
  recovery: 12,
  damage: 150,
  hitstun: 24,
  blockstun: 16,
  hitboxes: [{ boxes: [{ x: 22, y: 50, w: 46, h: 24 }] }],
};
