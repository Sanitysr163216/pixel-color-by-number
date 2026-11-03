/**
 * Character 1 (Shoto / "zoner") — every move's numbers.
 *
 * Frames: startup N means the hitbox first appears on frame N + 1 (frame 1 = the frame the button is pressed).
 * Boxes: { x, y, w, h } in pixels; x forward from the centre (negative = behind), y up from the feet.
 * Anything left out uses the defaults in src/config.ts (hitstop, meter) — see src/moves/types.ts for every field.
 *
 * All numbers are first guesses to tune by playing.
 */
import type { MoveData, ProjectileData } from '../../moves/types';

// ---------------------------------------------------------------- standing normals

/** Standing palm strike, hits at a high height (whiffs on crouching opponents). */
export const standLP: MoveData = {
  name: 'Palm Strike',
  kind: 'normal',
  strength: 'L',
  startup: 4,
  active: 2,
  recovery: 7,
  damage: 30,
  hitstun: 12,
  blockstun: 8,
  knockback: { distance: 14, speed: 3.5 },
  hitboxes: [{ boxes: [{ x: 24, y: 70, w: 22, h: 14 }] }],
  hurtboxes: [{ frames: [5, 9], boxes: [{ x: 10, y: 72, w: 26, h: 10 }] }], // the arm
};

/** Both hands attack. */
export const standMP: MoveData = {
  name: 'Twin Palm',
  kind: 'normal',
  strength: 'M',
  startup: 6,
  active: 3,
  recovery: 11,
  damage: 60,
  hitstun: 17,
  blockstun: 13,
  knockback: { distance: 22, speed: 4.5 },
  hitboxes: [{ boxes: [{ x: 20, y: 50, w: 24, h: 22 }] }],
  hurtboxes: [{ frames: [7, 13], boxes: [{ x: 10, y: 54, w: 26, h: 14 }] }], // the arms
};

/** Standing HK: high hitting donkey kick (whiffs on crouching opponents). */
export const standHK: MoveData = {
  name: 'Donkey Kick',
  kind: 'normal',
  strength: 'H',
  startup: 9,
  active: 4,
  recovery: 17,
  damage: 90,
  hitstun: 21,
  blockstun: 16,
  knockback: { distance: 32, speed: 5.5 },
  hitboxes: [{ boxes: [{ x: 26, y: 64, w: 26, h: 18 }] }],
  hurtboxes: [{ frames: [8, 16], boxes: [{ x: 8, y: 60, w: 34, h: 16 }] }], // the leg
};

// ---------------------------------------------------------------- crouching normals

/** Two punches with separate active frames (hits twice). Close range. */
export const crouchLP: MoveData = {
  name: 'Double Jab',
  kind: 'normal',
  strength: 'L',
  startup: 4,
  active: 7,
  recovery: 7,
  damage: 15, // per hit
  hitstun: 10,
  blockstun: 7,
  knockback: { distance: 6, speed: 2 },
  hitboxes: [
    { frames: [1, 2], boxes: [{ x: 14, y: 34, w: 24, h: 14 }], hit: 0 },
    { frames: [6, 7], boxes: [{ x: 14, y: 34, w: 24, h: 14 }], hit: 1 },
  ],
  hurtboxes: [
    { frames: [5, 7], boxes: [{ x: 8, y: 36, w: 24, h: 10 }] },
    { frames: [10, 13], boxes: [{ x: 8, y: 34, w: 24, h: 10 }] },
  ],
};

/** Horizontal hand chop. Slow startup, good range. */
export const crouchMP: MoveData = {
  name: 'Low Chop',
  kind: 'normal',
  strength: 'M',
  startup: 10,
  active: 3,
  recovery: 14,
  damage: 55,
  hitstun: 16,
  blockstun: 12,
  knockback: { distance: 22, speed: 4.5 },
  hitboxes: [{ boxes: [{ x: 22, y: 34, w: 38, h: 12 }] }],
  hurtboxes: [{ frames: [11, 17], boxes: [{ x: 10, y: 36, w: 40, h: 10 }] }],
};

/** Spins on his heel to deliver a knuckle hit: a spinning backhand. */
export const crouchHP: MoveData = {
  name: 'Spinning Backhand',
  kind: 'normal',
  strength: 'H',
  startup: 9,
  active: 4,
  recovery: 18,
  damage: 85,
  hitstun: 20,
  blockstun: 15,
  knockback: { distance: 32, speed: 5.5 },
  hitboxes: [{ boxes: [{ x: 20, y: 44, w: 34, h: 18 }] }],
  hurtboxes: [{ frames: [10, 16], boxes: [{ x: 8, y: 46, w: 36, h: 12 }] }],
};

/** Super short range stomp: barely stands up halfway, arching the back. Low. */
export const crouchLK: MoveData = {
  name: 'Stomp',
  kind: 'normal',
  strength: 'L',
  startup: 5,
  active: 2,
  recovery: 9,
  damage: 25,
  hitstun: 11,
  blockstun: 8,
  guard: 'low',
  knockback: { distance: 10, speed: 3 },
  hitboxes: [{ boxes: [{ x: 8, y: 0, w: 22, h: 12 }] }],
  // Half standing: 74 px tall instead of 62.
  hurtboxes: [{ frames: [1, 14], replace: true, boxes: [{ x: -4, y: 56, w: 18, h: 18 }, { x: -16, y: 0, w: 34, h: 58 }] }],
};

/** Crouching back kick (donkey kick) at knee level. Low. Pushes the character forward during recovery. */
export const crouchMK: MoveData = {
  name: 'Low Donkey Kick',
  kind: 'normal',
  strength: 'M',
  startup: 7,
  active: 3,
  recovery: 15,
  damage: 50,
  hitstun: 15,
  blockstun: 11,
  guard: 'low',
  knockback: { distance: 22, speed: 4.5 },
  motion: [{ frame: 11, forward: 1.2 }], // from the first recovery frame
  hitboxes: [{ boxes: [{ x: 18, y: 8, w: 36, h: 16 }] }],
  hurtboxes: [{ frames: [8, 14], boxes: [{ x: 10, y: 10, w: 34, h: 12 }] }],
};

const sweepFront = { x: 8, y: 0, w: 38, h: 14 };
const sweepBack = { x: -46, y: 0, w: 38, h: 14 };
const legFront = { x: 8, y: 0, w: 30, h: 12 };
const legBack = { x: -38, y: 0, w: 30, h: 12 };

/**
 * A crouch on one leg and a double spin sweep. The hitbox covers both directions, one side at a time
 * (like Zangief's lariat in SSF2T): front, back, front, back. Mediocre reach. Hits once.
 */
export const crouchHK: MoveData = {
  name: 'Double Spin Sweep',
  kind: 'normal',
  strength: 'H',
  startup: 8,
  active: 12,
  recovery: 20,
  damage: 80,
  hitstun: 0, // knocks down instead
  blockstun: 14,
  guard: 'low',
  knockdown: true,
  knockback: { distance: 32, speed: 5.5 },
  hitboxes: [
    { frames: [1, 3], boxes: [sweepFront] },
    { frames: [4, 6], boxes: [sweepBack] },
    { frames: [7, 9], boxes: [sweepFront] },
    { frames: [10, 12], boxes: [sweepBack] },
  ],
  hurtboxes: [
    { frames: [9, 11], boxes: [legFront] },
    { frames: [12, 14], boxes: [legBack] },
    { frames: [15, 17], boxes: [legFront] },
    { frames: [18, 20], boxes: [legBack] },
  ],
};

// ---------------------------------------------------------------- jumping normals
// Every jumping attack has to be blocked standing.

/** Small range punch. */
export const jumpLP: MoveData = {
  name: 'Jumping Jab',
  kind: 'normal',
  strength: 'L',
  startup: 3,
  active: 5,
  recovery: 5,
  damage: 30,
  hitstun: 12,
  blockstun: 8,
  knockback: { distance: 14, speed: 3.5 },
  hitboxes: [{ boxes: [{ x: 12, y: 50, w: 20, h: 12 }] }],
};

/** A slightly longer range punch aimed downwards. */
export const jumpMP: MoveData = {
  name: 'Jumping Down Punch',
  kind: 'normal',
  strength: 'M',
  startup: 5,
  active: 5,
  recovery: 6,
  damage: 55,
  hitstun: 16,
  blockstun: 12,
  knockback: { distance: 22, speed: 4.5 },
  hitboxes: [{ boxes: [{ x: 12, y: 30, w: 28, h: 16 }] }],
};

/** An okay range hand chop, parallel to the ground. */
export const jumpHP: MoveData = {
  name: 'Jumping Chop',
  kind: 'normal',
  strength: 'H',
  startup: 7,
  active: 4,
  recovery: 8,
  damage: 85,
  hitstun: 19,
  blockstun: 14,
  knockback: { distance: 32, speed: 5.5 },
  hitboxes: [{ boxes: [{ x: 16, y: 50, w: 32, h: 12 }] }],
};

/** Fast knee: a small hitbox under the character, at the knees. */
export const jumpLK: MoveData = {
  name: 'Jumping Knee',
  kind: 'normal',
  strength: 'L',
  startup: 3,
  active: 6,
  recovery: 4,
  damage: 30,
  hitstun: 12,
  blockstun: 8,
  knockback: { distance: 14, speed: 3.5 },
  hitboxes: [{ boxes: [{ x: -6, y: 10, w: 26, h: 16 }] }],
};

/** A heel kick that hits high, above the jumping character's body. */
export const jumpHK: MoveData = {
  name: 'Jumping Heel Kick',
  kind: 'normal',
  strength: 'H',
  startup: 7,
  active: 5,
  recovery: 8,
  damage: 90,
  hitstun: 20,
  blockstun: 15,
  knockback: { distance: 32, speed: 5.5 },
  hitboxes: [{ boxes: [{ x: 10, y: 66, w: 28, h: 24 }] }],
};

/**
 * A side kick like Ryu's jumping MK in SF2: forward and down. The second box, around the hip, reaches a little
 * behind the centre so it can cross up. Like every jumping attack, it has to be blocked standing.
 */
export const jumpMK: MoveData = {
  name: 'Jumping Side Kick',
  kind: 'normal',
  strength: 'M',
  startup: 5,
  active: 10,
  recovery: 4,
  damage: 60,
  hitstun: 16,
  blockstun: 12,
  knockback: { distance: 22, speed: 4.5 },
  hitboxes: [{ boxes: [{ x: 16, y: 16, w: 24, h: 18 }, { x: -12, y: 24, w: 30, h: 16 }] }],
};

// ---------------------------------------------------------------- command normals

/**
 * Forward + MP: moves the character forward, lowers the character's hurtbox and hits far, with a slightly
 * disjointed hitbox (it reaches past the arm's hurtbox). Like Yun's lunge in Third Strike: both arms
 * extended in opposite directions.
 */
export const forwardMP: MoveData = {
  name: 'Lunging Palm',
  kind: 'command',
  strength: 'M',
  startup: 8,
  active: 3,
  recovery: 14,
  damage: 55,
  hitstun: 16,
  blockstun: 12,
  knockback: { distance: 22, speed: 4.5 },
  motion: [
    { frame: 1, forward: 2 },
    { frame: 9, forward: 0 },
  ],
  hitboxes: [{ boxes: [{ x: 26, y: 44, w: 38, h: 14 }] }],
  hurtboxes: [
    // Lowered body: 64 px tall instead of 96, so high attacks go over it.
    { frames: [3, 22], replace: true, boxes: [{ x: -14, y: 0, w: 30, h: 36 }, { x: -4, y: 36, w: 28, h: 28 }] },
    { frames: [9, 14], boxes: [{ x: 12, y: 46, w: 36, h: 10 }] }, // the front arm, 16 px shorter than the hitbox
  ],
};

/** Forward + MK: a standing axe kick that moves forward. Overhead (must be blocked standing). */
export const forwardMK: MoveData = {
  name: 'Axe Kick',
  kind: 'command',
  strength: 'M',
  startup: 18,
  active: 3,
  recovery: 14,
  damage: 70,
  hitstun: 18,
  blockstun: 12,
  guard: 'overhead',
  knockback: { distance: 22, speed: 4.5 },
  motion: [
    { frame: 4, forward: 1.5 },
    { frame: 18, forward: 0 },
  ],
  hitboxes: [
    { frames: [1, 1], boxes: [{ x: 14, y: 56, w: 24, h: 44 }] }, // the heel coming down from above
    { frames: [2, 3], boxes: [{ x: 16, y: 24, w: 26, h: 40 }] },
  ],
  hurtboxes: [{ frames: [10, 24], boxes: [{ x: 6, y: 40, w: 22, h: 52 }] }], // the raised leg
};

// ---------------------------------------------------------------- throw

/**
 * Close forward + MP or HP: a throw like a judo shoulder throw. Grabs on the first frame, turns, and slams the
 * opponent into the ground behind him (the sides switch). The opponent is never airborne and is knocked down.
 * Both fighters are invulnerable during the throw.
 */
export const shoulderThrow: MoveData = {
  name: 'Shoulder Throw',
  kind: 'throw',
  strength: 'H',
  startup: 0, // grabs on the frame the button is pressed
  active: 1,
  recovery: 27,
  damage: 120,
  hitstun: 0,
  blockstun: 0,
  knockdown: true,
  invincible: [[1, 28]],
  hitboxes: [],
  throw: { slamFrame: 20, landAt: -40 },
};

// ---------------------------------------------------------------- Leopard Hand Strike (4, 2, 1, 6 + P)
// A very fast punch that is "charged" visually. The hitbox is out for 1 frame, fast recovery, high damage
// for this cast. If the user is hit during its startup, they take double damage.

export const leopardL: MoveData = {
  name: 'Leopard Strike L',
  kind: 'special',
  strength: 'L',
  startup: 7,
  active: 1,
  recovery: 10,
  damage: 100,
  hitstun: 20,
  blockstun: 12,
  knockback: { distance: 16, speed: 4 },
  vulnerable: { frames: 'startup', damageMultiplier: 2 },
  hitboxes: [{ boxes: [{ x: 22, y: 54, w: 30, h: 16 }] }],
  hurtboxes: [{ frames: [8, 12], boxes: [{ x: 10, y: 56, w: 28, h: 12 }] }],
};

export const leopardM: MoveData = {
  name: 'Leopard Strike M',
  kind: 'special',
  strength: 'M',
  startup: 9,
  active: 1,
  recovery: 12,
  damage: 120,
  hitstun: 22,
  blockstun: 14,
  knockback: { distance: 22, speed: 4.5 },
  vulnerable: { frames: 'startup', damageMultiplier: 2 },
  hitboxes: [{ boxes: [{ x: 22, y: 54, w: 36, h: 16 }] }],
  hurtboxes: [{ frames: [10, 15], boxes: [{ x: 10, y: 56, w: 30, h: 12 }] }],
};

/**
 * Knocks the opponent down immediately; their wakeup takes twice as long.
 * Its recovery is much longer than the other versions.
 */
export const leopardH: MoveData = {
  name: 'Leopard Strike H',
  kind: 'special',
  strength: 'H',
  startup: 11,
  active: 1,
  recovery: 32,
  damage: 140,
  hitstun: 0, // knocks down instead
  blockstun: 16,
  knockdown: { wakeupMultiplier: 2 },
  knockback: { distance: 30, speed: 5.5 },
  vulnerable: { frames: 'startup', damageMultiplier: 2 },
  hitboxes: [{ boxes: [{ x: 22, y: 52, w: 42, h: 20 }] }],
  hurtboxes: [{ frames: [12, 20], boxes: [{ x: 10, y: 56, w: 32, h: 12 }] }],
};

// ---------------------------------------------------------------- Rising Push (6, 2, 3 + K)
// The character pushes himself up and forward, upside-down on a staff. He leaves the ground and kicks
// after startup (no separate kick motion). The move ends when he lands, then landingRecovery applies.

/** Inverted body between the staff and the hips; the kicking feet above have no hurtbox. */
const invertedBody = [{ x: -8, y: 18, w: 22, h: 58 }];

/** Light: 1 frame startup (hitbox from frame 2), low and short, hits forward and up. */
export const risingPushL: MoveData = {
  name: 'Rising Push L',
  kind: 'special',
  strength: 'L',
  startup: 1,
  active: 6,
  recovery: 0,
  landingRecovery: 10,
  damage: 80,
  hitstun: 0, // knocks down instead
  blockstun: 14,
  knockdown: true,
  knockback: { distance: 24, speed: 4 },
  motion: [{ frame: 2, forward: 1, up: 6 }],
  hitboxes: [{ boxes: [{ x: 2, y: 72, w: 26, h: 30 }] }],
  hurtboxes: [{ frames: [2, 99], replace: true, boxes: invertedBody }],
};

/** Medium: 2 frame startup, goes higher and further forward, hits directly above the head. */
export const risingPushM: MoveData = {
  name: 'Rising Push M',
  kind: 'special',
  strength: 'M',
  startup: 2,
  active: 8,
  recovery: 0,
  landingRecovery: 14,
  damage: 100,
  hitstun: 0,
  blockstun: 16,
  knockdown: true,
  knockback: { distance: 26, speed: 4.5 },
  motion: [{ frame: 3, forward: 2, up: 8 }],
  hitboxes: [{ boxes: [{ x: -12, y: 84, w: 26, h: 26 }] }],
  hurtboxes: [{ frames: [3, 99], replace: true, boxes: invertedBody }],
};

/**
 * Heavy: 5 frame startup, goes forward by a considerable margin. Hits like the medium at first; near the
 * maximum height the hitbox extends to slightly behind him.
 */
export const risingPushH: MoveData = {
  name: 'Rising Push H',
  kind: 'special',
  strength: 'H',
  startup: 5,
  active: 20,
  recovery: 0,
  landingRecovery: 18,
  damage: 120,
  hitstun: 0,
  blockstun: 18,
  knockdown: true,
  knockback: { distance: 30, speed: 5 },
  motion: [{ frame: 6, forward: 3.5, up: 9 }],
  hitboxes: [
    { frames: [1, 14], boxes: [{ x: -12, y: 84, w: 26, h: 26 }] },
    { frames: [15, 20], boxes: [{ x: -30, y: 84, w: 44, h: 26 }] }, // extends behind at the top
  ],
  hurtboxes: [{ frames: [6, 99], replace: true, boxes: invertedBody }],
};

// ---------------------------------------------------------------- Soul Flake (2, 3, 6 + P)
// A light blue bubble orb, slightly see-through, thrown with a black rod. Every version can be blocked in the
// air, and blocking it in the air takes double chip.

const flake = (speed: number): ProjectileData => ({
  speed,
  boxes: [{ x: -9, y: -9, w: 18, h: 18 }],
  hits: 1,
  hitInterval: 0,
  spawn: { x: 38, y: 58 },
  radius: 9,
});

/** Light: startup 12, recovery 43. */
export const soulFlakeL: MoveData = {
  name: 'Soul Flake L',
  kind: 'special',
  strength: 'L',
  startup: 12,
  active: 1, // the frame the orb appears
  recovery: 43,
  damage: 70, // the same for L, M and H
  hitstun: 20,
  blockstun: 16,
  knockback: { distance: 16, speed: 4 },
  airBlockable: true,
  airBlockChip: 2,
  hitboxes: [],
  projectile: flake(3),
};

/** Medium: 25% faster than light, 1 frame more recovery. */
export const soulFlakeM: MoveData = { ...soulFlakeL, name: 'Soul Flake M', strength: 'M', recovery: 44, projectile: flake(3 * 1.25) };

/** Heavy: 75% faster than light, 2 frames more recovery. */
export const soulFlakeH: MoveData = { ...soulFlakeL, name: 'Soul Flake H', strength: 'H', recovery: 45, projectile: flake(3 * 1.75) };

/**
 * CE: a much larger orb at half the light one's speed, too tall to jump over. 5 hits instead of 1, 2.5 times the
 * damage in total. Blocking it on the ground locks the blocker's stance. The thrower counts as airborne during
 * the startup (but not the recovery).
 */
export const soulFlakeCE: MoveData = {
  name: 'Soul Flake CE',
  kind: 'ce',
  strength: 'H',
  startup: 20,
  active: 1,
  recovery: 45,
  damage: 35, // per hit; 5 hits = 175 = 2.5 × 70
  hitstun: 14,
  blockstun: 14,
  hitstop: 5,
  knockback: { distance: 4, speed: 2 },
  airBlockable: true,
  airBlockChip: 2,
  airborne: [[1, 20]],
  hitboxes: [],
  projectile: {
    speed: 1.5,
    boxes: [{ x: -32, y: -56, w: 64, h: 150 }],
    hits: 5,
    hitInterval: 8,
    spawn: { x: 44, y: 60 },
    radius: 40,
    lockGuard: true,
  },
};

// ---------------------------------------------------------------- Chakra specials

/**
 * Spiritual Tunneling (half circle forward + two punches, 1 bar): dashes forward and punches at head level,
 * knocking down. Clones of him do the same animation a little behind and fuse with him. Invincible until
 * the first recovery frame.
 */
export const spiritualTunneling: MoveData = {
  name: 'Spiritual Tunneling',
  kind: 'chakra',
  strength: 'H',
  startup: 8,
  active: 4,
  recovery: 20,
  damage: 220,
  hitstun: 0, // knocks down instead
  blockstun: 18,
  knockdown: true,
  knockback: { distance: 30, speed: 5 },
  invincible: [[1, 12]],
  motion: [
    { frame: 1, forward: 9 },
    { frame: 9, forward: 0 },
  ],
  meterOnHit: 0,
  barCost: 1,
  hitboxes: [{ boxes: [{ x: 16, y: 70, w: 34, h: 24 }] }],
};
