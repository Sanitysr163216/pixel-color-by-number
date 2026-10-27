/**
 * Numbers that apply to the whole game. Character and move numbers live in src/characters/<name>/.
 *
 * Units: distances are pixels of the 304×224 screen, times are frames (1/60 second).
 */

/** The game logic runs at exactly this many frames per second, whatever the monitor's refresh rate. */
export const FPS = 60;

/** Internal resolution: the size of the KOF97 picture on the Neo Geo. */
export const SCREEN_W = 304;
export const SCREEN_H = 224;

/** Screen row the fighters stand on. */
export const FLOOR_Y = 200;

/** Width of the whole stage. The camera scrolls inside it. */
export const STAGE_W = 640;

/** Closest a fighter's centre can get to the stage edge. */
export const WALL_MARGIN = 20;

/** The fighters can never be further apart than this, so both stay on screen. */
export const MAX_SEPARATION = SCREEN_W - 48;

export const RULES = {
  /** Gravity for jumps and falls, px per frame per frame. */
  gravity: 0.5,

  /**
   * How many frames a button press is remembered while the fighter can't act yet (0 = no buffer).
   * Presses made during hitstop always count for chains and special cancels.
   */
  inputBuffer: {
    /** Normals and command normals. */
    normals: 1,
    /** Special moves, CE and Chakra specials. */
    specials: 3,
  },

  /**
   * Two punches (or two kicks) pressed at most this many frames apart count as pressed together (CE input).
   * 0 = exactly the same frame. With 1, a second button one frame later upgrades the special that just started.
   */
  ceWindow: 0,

  /** Double-tap forward (dash) or back (back hop): 6-5-6 or 4-5-4 within this many frames. */
  doubleTapWindow: 12,

  /**
   * Proximity guard: a fighter holding back goes into the block stance this many frames before the opponent's
   * first active frame, if the attack would reach them. They stop walking backward while in it.
   */
  proximityGuard: 2,

  meter: {
    /** Points in one bar. */
    perBar: 100,
    /** Number of bars. */
    bars: 10,
    /** Points the defender gets for every hit they block. The attacker gets nothing for a blocked hit. */
    onBlock: 2,
    /** Points the attacker gets for a hit that isn't blocked: this × 1 / 2 / 3 for light / medium / heavy. */
    onHitPerLevel: 3,
  },

  /** Light and medium normals that hit an airborne opponent flip them backwards; invulnerable until they land. */
  airReset: {
    /** Upward speed at the start of the flip, px/frame. */
    popUp: 4,
    /** Horizontal speed away from the attacker, px/frame. */
    pushAway: 2,
  },

  knockdown: {
    /**
     * Frames a knocked-down fighter stays on the ground, counted from the frame they touch it.
     * On the next frame their hurtbox comes back and their buttons work again (same frame).
     */
    wakeup: 40,
    /** Upward speed when a grounded fighter is knocked down, px/frame. */
    popUp: 3,
    /** Horizontal speed away from the attacker while falling, px/frame. */
    pushAway: 1.5,
  },

  /** Frames a fighter can't act after landing during an air attack. */
  airAttackLanding: 2,
};

/**
 * Values a move gets when it leaves the field out, by strength.
 * Heavier moves push further and faster (knockback) and build more meter.
 */
export const STRENGTH_DEFAULTS = {
  L: { knockback: { distance: 14, speed: 3.5 }, meterLevel: 1 },
  M: { knockback: { distance: 22, speed: 4.5 }, meterLevel: 2 },
  H: { knockback: { distance: 32, speed: 5.5 }, meterLevel: 3 },
};

/**
 * Hitstop: frames both fighters freeze when a move connects. Each character can change these
 * (CharacterData.hitstop), and a single move can set its own (MoveData.hitstop).
 */
export interface HitstopTable {
  /** Moves done from the ground, by strength. */
  ground: { L: number; M: number; H: number };
  /** Moves done in the air that connect with a grounded opponent (every move). */
  airToGround: number;
  /** Moves done in the air that connect with an airborne opponent. */
  airToAir: { hit: number; block: number };
}

export const DEFAULT_HITSTOP: HitstopTable = {
  ground: { L: 7, M: 9, H: 11 },
  airToGround: 7,
  airToAir: { hit: 3, block: 7 },
};
