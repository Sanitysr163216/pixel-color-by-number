import type { HitstopTable } from '../config';
import type { ButtonName } from '../input/buttons';
import type { Box, MoveData } from '../moves/types';

/**
 * Every button in every stance: 5 = standing, 2 = crouching, j. = jumping.
 * A slot set to null is an empty move: the input is read, but nothing happens.
 */
export const NORMAL_SLOTS = [
  '5LP', '5MP', '5HP', '5LK', '5MK', '5HK',
  '2LP', '2MP', '2HP', '2LK', '2MK', '2HK',
  'j.LP', 'j.MP', 'j.HP', 'j.LK', 'j.MK', 'j.HK',
] as const;
export type NormalSlot = (typeof NORMAL_SLOTS)[number];

/** A button plus a direction, e.g. forward + MK. */
export interface CommandNormal {
  /** Numpad direction relative to the fighter: 6 = forward, 4 = back, 3 = down-forward… */
  direction: number;
  button: ButtonName;
  move: MoveData;
}

/** A special move: a motion plus a punch or a kick. */
export interface SpecialMove {
  /** Short name used in move ids, e.g. 'leopard'. */
  id: string;
  name: string;
  /** Numpad directions in order, relative to the fighter (6 = forward). */
  motion: number[];
  /** Frames allowed from the first direction to the button press. */
  window: number;
  /** P: any punch, K: any kick. The button picks the version (LP = L, MP = M, HP = H). */
  button: 'P' | 'K';
  L: MoveData | null;
  M: MoveData | null;
  H: MoveData | null;
  /** Chakra Enhance: the same motion with two punches (or two kicks). Costs 1 bar. null = not made yet. */
  CE: MoveData | null;
}

/** A move that can only be used by spending 1–2 bars. */
export interface ChakraSpecial {
  id: string;
  name: string;
  motion: number[];
  window: number;
  button: 'P' | 'K';
  move: MoveData;
}

export interface CharacterData {
  name: string;
  health: number;
  /** px per frame. */
  walkForward: number;
  walkBack: number;
  jump: {
    /** Frames on the ground before leaving it. */
    squat: number;
    /** Upward speed at take-off, px per frame. */
    up: number;
    /** Horizontal speed of forward and backward jumps, px per frame. */
    forward: number;
    back: number;
  };
  /** Double-tap forward: a continuous dash while forward is held, px per frame. */
  dash: { speed: number };
  /** Double-tap back: a short hop backwards. Speeds in px per frame. */
  backHop: { up: number; back: number };
  /** Changes to the game's hitstop table for this character's moves (see DEFAULT_HITSTOP in src/config.ts). */
  hitstop?: Partial<HitstopTable>;
  hurtboxes: { stand: Box[]; crouch: Box[]; air: Box[] };
  /** The boxes that stop fighters from walking through each other. */
  pushboxes: { stand: Box; crouch: Box; air: Box; down: Box };
  normals: Record<NormalSlot, MoveData | null>;
  commandNormals: CommandNormal[];
  specials: SpecialMove[];
  chakraSpecials: ChakraSpecial[];
}
