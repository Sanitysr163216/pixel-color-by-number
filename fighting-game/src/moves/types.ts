import type { Strength } from '../input/buttons';

/**
 * A rectangle relative to the fighter, in pixels.
 * x: forward from the fighter's centre (negative = behind). y: up from the feet. w, h: size.
 */
export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

/**
 * normal: a button on its own (standing, crouching or jumping).
 * command: a button plus a direction (e.g. forward + MK).
 * special: a motion plus a button. ce: Chakra Enhance version of a special. chakra: Chakra special.
 */
export type MoveKind = 'normal' | 'command' | 'special' | 'ce' | 'chakra';

/** How the move has to be blocked. mid: standing or crouching. low: crouching. overhead: standing. */
export type Guard = 'mid' | 'low' | 'overhead';

export interface HitboxPhase {
  /**
   * Active frames this phase covers, counted from the first active frame (= 1).
   * Leave it out to use every active frame. A hitbox can never exist outside the active frames.
   */
  frames?: [number, number];
  boxes: Box[];
  /**
   * Phases with different numbers can each hit once (multi-hit moves).
   * Phases with the same number share one hit. Default 0, so a move hits once.
   */
  hit?: number;
}

export interface HurtboxPhase {
  /** Frames of the move, counted from the first startup frame (= 1). */
  frames: [number, number];
  boxes: Box[];
  /**
   * true: these boxes replace the fighter's normal hurtboxes (e.g. a move that lowers the body).
   * false or left out: they are added to them (e.g. an outstretched arm or leg).
   */
  replace?: boolean;
}

export interface MotionStep {
  /** Frame of the move on which the speed changes (1 = first startup frame). */
  frame: number;
  /** Forward speed, px per frame (negative = backward). Stays until the next step or the end of the move. */
  forward?: number;
  /** Upward speed, px per frame. The fighter leaves the ground and gravity brings them back down. */
  up?: number;
}

export interface MoveData {
  name: string;
  kind: MoveKind;
  /** Light, medium or heavy. Sets the defaults below and the meter gained on hit. */
  strength: Strength;

  /** Frames before the hitbox appears. startup 4: frames 1–4 have no hitbox, frame 5 is the first active frame. */
  startup: number;
  /** Frames the hitbox exists. */
  active: number;
  /** Frames after the last active frame before the fighter can act again. */
  recovery: number;

  damage: number;
  /** Frames the opponent can't act after being hit (after hitstop). */
  hitstun: number;
  /** Frames the opponent can't act after blocking (after hitstop). */
  blockstun: number;
  /** Default 'mid'. */
  guard?: Guard;
  /** Frames both fighters freeze when the move connects. Default by strength: L 7, M 9, H 11. */
  hitstop?: number;
  /**
   * How far (px) and how fast (px per frame) the opponent slides away on hit or block.
   * Default by strength: L 14 px at 3.5, M 22 px at 4.5, H 32 px at 5.5.
   * If the opponent is in the corner, the attacker slides back instead.
   */
  knockback?: { distance: number; speed: number };

  hitboxes: HitboxPhase[];
  hurtboxes?: HurtboxPhase[];
  /** Movement during the move. */
  motion?: MotionStep[];
  /**
   * For moves that leave the ground: if the fighter is still in the air when the move's frames run out,
   * they keep falling (still unable to act), then can't act for this many frames after landing.
   */
  landingRecovery?: number;

  /** Knocks a grounded opponent down on hit. wakeupMultiplier 2: they stay on the ground twice as long. */
  knockdown?: true | { wakeupMultiplier: number };
  /**
   * What happens to an airborne opponent hit by this move.
   * Default: light and medium normals → 'reset' (flip backwards, invulnerable until landing);
   * heavies and specials done from the ground → 'knockdown'; heavies done in the air → 'reset'.
   */
  airHit?: 'reset' | 'knockdown';
  /**
   * Can an airborne opponent block this move?
   * Default: light and medium normals from the ground → yes; heavies and specials from the ground → no;
   * anything done in the air → yes.
   */
  airBlockable?: boolean;

  /** Frames of the move where the fighter can't be hit at all. */
  invincible?: Array<[number, number]>;
  /** Frames of the move where the fighter counts as airborne even while touching the ground. */
  airborne?: Array<[number, number]>;
  /** The fighter takes more damage if they are hit during these frames ('startup' = all startup frames). */
  vulnerable?: { frames: 'startup' | [number, number]; damageMultiplier: number };

  /** Meter the attacker gets when the move hits (not blocked). Default 3 × 1 / 2 / 3 for L / M / H. */
  meterOnHit?: number;
  /** Bars it costs to do the move: CE 1, Chakra specials 1 or 2. */
  barCost?: number;
}
