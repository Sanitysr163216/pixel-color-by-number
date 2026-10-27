import type { CompiledCharacter, CompiledSpecial } from '../characters/compile';
import type { ButtonName } from '../input/buttons';
import { InputHistory } from '../input/history';
import type { CompiledMove } from '../moves/compile';

/**
 * ground     standing, walking or crouching; free to act
 * jumpSquat  the frames on the ground before a jump
 * jump       in the air; can block, and can attack once per jump
 * move       doing a move (startup / active / recovery)
 * landing    landing recovery after a move that left the ground
 * hitstun    hit on the ground
 * blockstun  blocking (on the ground or in the air)
 * airReset   hit in the air by a light/medium normal: flipping back, invulnerable until landing
 * knockdown  knocked down: falling, then on the ground until wakeup; invulnerable throughout
 * ko         knocked out
 */
export type StateName =
  | 'ground'
  | 'jumpSquat'
  | 'jump'
  | 'move'
  | 'landing'
  | 'hitstun'
  | 'blockstun'
  | 'airReset'
  | 'knockdown'
  | 'ko';

/** Knockback still to apply: `left` units at `speed` units per frame in screen direction `dir`. */
export interface Slide {
  left: number;
  speed: number;
  dir: number;
  /** The attacker, who slides back instead if this fighter is stuck in a corner. */
  from: 0 | 1;
}

export interface Fighter {
  readonly index: 0 | 1;
  readonly char: CompiledCharacter;
  readonly input: InputHistory;
  /** Position and speed in simulation units. y is the height of the feet above the ground. vx is in screen direction. */
  x: number;
  y: number;
  vx: number;
  vy: number;
  facing: 1 | -1;
  health: number;
  /** 0 to 1000; 100 points = 1 bar. */
  meter: number;
  state: StateName;
  /** Frames spent in the current state. */
  frame: number;
  crouching: boolean;
  /** Walking direction relative to facing while in 'ground'. */
  walk: -1 | 0 | 1;
  jumpDir: -1 | 0 | 1;
  move: CompiledMove | null;
  /** Frame of the current move: 1 on the frame it starts. */
  moveFrame: number;
  /** The move was started in the air (a jumping attack). */
  moveFromAir: boolean;
  /** The special the current move came from, so a second button can upgrade it to its CE. */
  special: { def: CompiledSpecial; button: ButtonName } | null;
  /** Hit numbers of the current move that already connected. */
  hitsDone: number;
  /** Frames left in hitstun, blockstun, landing recovery or on the ground after a knockdown. */
  stun: number;
  airBlock: boolean;
  /** airReset: touched the ground; the fighter is back on the next frame. */
  landed: boolean;
  /** knockdown: lying on the ground. */
  down: boolean;
  wakeupMultiplier: number;
  /** Frames left frozen by hitstop. */
  hitstop: number;
  slide: Slide | null;
  /** Used an attack during this jump: can't attack again until landing (blocking in the air resets this). */
  airActionUsed: boolean;
  /** Training dummy: blocks everything it is allowed to block. */
  autoBlock: boolean;
  combo: { hits: number; damage: number };
  /** For the training display. */
  lastMove: CompiledMove | null;
  lastCommand: string;
  lastCommandFrame: number;
}

export function createFighter(index: 0 | 1, char: CompiledCharacter): Fighter {
  return {
    index,
    char,
    input: new InputHistory(),
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    facing: index === 0 ? 1 : -1,
    health: char.health,
    meter: 0,
    state: 'ground',
    frame: 0,
    crouching: false,
    walk: 0,
    jumpDir: 0,
    move: null,
    moveFrame: 0,
    moveFromAir: false,
    special: null,
    hitsDone: 0,
    stun: 0,
    airBlock: false,
    landed: false,
    down: false,
    wakeupMultiplier: 1,
    hitstop: 0,
    slide: null,
    airActionUsed: false,
    autoBlock: false,
    combo: { hits: 0, damage: 0 },
    lastMove: null,
    lastCommand: '',
    lastCommandFrame: 0,
  };
}

/** Which part of its move a fighter is in. */
export function movePhase(f: Fighter): 'startup' | 'active' | 'recovery' | null {
  const m = f.move;
  if (f.state !== 'move' || !m) return null;
  if (f.moveFrame <= m.startup) return 'startup';
  if (f.moveFrame <= m.startup + m.active) return 'active';
  return 'recovery';
}
