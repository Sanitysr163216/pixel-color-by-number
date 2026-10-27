/**
 * Placeholder animation for Character 1: stick-figure poses until real sprites exist.
 * Each move's poses are spread over its startup / active / recovery frames, so the animation stays in
 * sync when the frame data changes.
 */
import type { P, Pose } from '../../render/figure';
import { movePhase, type Fighter } from '../../sim/fighter';

export interface PoseResult {
  pose: Pose;
  rotate?: number;
  pivot?: P;
}

const STANCE: Pose = {
  head: [5, 87], neck: [3, 78], hip: [0, 49],
  fe: [12, 63], fh: [20, 71], be: [8, 62], bh: [16, 68],
  fk: [9, 25], ff: [14, 0], bk: [-8, 25], bf: [-14, 0],
};

/** Moves the upper body (head, neck, hips, arms). */
function shift(p: Pose, dx: number, dy: number): Pose {
  const s = (q: P): P => [q[0] + dx, q[1] + dy];
  return { ...p, head: s(p.head), neck: s(p.neck), hip: s(p.hip), fe: s(p.fe), fh: s(p.fh), be: s(p.be), bh: s(p.bh) };
}

const BREATHE = shift(STANCE, 0, -1);
const WALK: Pose[] = [
  { ...STANCE, fk: [11, 25], ff: [16, 0], bk: [-10, 25], bf: [-16, 0] },
  { ...shift(STANCE, 0, 1), fk: [6, 26], ff: [3, 4], bk: [-1, 25], bf: [-3, 0] },
  { ...STANCE, fk: [-8, 25], ff: [-13, 0], bk: [9, 25], bf: [15, 0] },
  { ...shift(STANCE, 0, 1), fk: [0, 25], ff: [-2, 0], bk: [5, 26], bf: [3, 4] },
];
const CROUCH: Pose = {
  head: [8, 56], neck: [5, 48], hip: [-2, 25],
  fe: [14, 40], fh: [21, 47], be: [10, 38], bh: [17, 44],
  fk: [14, 20], ff: [12, 0], bk: [-10, 12], bf: [-16, 0],
};
const JUMP_SQUAT: Pose = {
  head: [6, 70], neck: [4, 61], hip: [0, 37],
  fe: [13, 50], fh: [20, 57], be: [9, 48], bh: [16, 54],
  fk: [12, 20], ff: [14, 0], bk: [-8, 19], bf: [-14, 0],
};
const JUMP_UP: Pose = {
  head: [4, 82], neck: [2, 73], hip: [0, 46],
  fe: [10, 60], fh: [16, 67], be: [6, 58], bh: [12, 64],
  fk: [13, 40], ff: [6, 26], bk: [3, 37], bf: [-5, 24],
};
const JUMP_DOWN: Pose = {
  head: [4, 86], neck: [2, 77], hip: [0, 48],
  fe: [12, 64], fh: [20, 70], be: [-4, 66], bh: [-10, 72],
  fk: [8, 25], ff: [10, 4], bk: [-6, 27], bf: [-10, 7],
};
const HIT1: Pose = {
  head: [-3, 85], neck: [-2, 76], hip: [0, 48],
  fe: [-2, 61], fh: [4, 54], be: [-10, 63], bh: [-16, 57],
  fk: [8, 25], ff: [13, 0], bk: [-9, 25], bf: [-15, 0],
};
const HIT2: Pose = {
  head: [-8, 82], neck: [-6, 74], hip: [-2, 47],
  fe: [-4, 62], fh: [0, 54], be: [-14, 64], bh: [-20, 60],
  fk: [7, 24], ff: [12, 0], bk: [-11, 24], bf: [-17, 0],
};
const CROUCH_HIT: Pose = {
  head: [1, 54], neck: [0, 46], hip: [-4, 25],
  fe: [6, 38], fh: [10, 31], be: [-2, 37], bh: [-6, 30],
  fk: [12, 20], ff: [12, 0], bk: [-12, 12], bf: [-18, 0],
};
const BLOCK: Pose = {
  head: [2, 86], neck: [1, 77], hip: [-1, 48],
  fe: [10, 69], fh: [14, 81], be: [12, 63], bh: [16, 74],
  fk: [9, 25], ff: [14, 0], bk: [-9, 24], bf: [-16, 0],
};
const CROUCH_BLOCK: Pose = { ...CROUCH, fe: [12, 45], fh: [16, 56], be: [14, 41], bh: [18, 52] };
const AIR_BLOCK: Pose = { ...JUMP_UP, fe: [10, 66], fh: [14, 77], be: [12, 62], bh: [16, 72] };
const LYING: Pose = {
  head: [-36, 7], neck: [-27, 7], hip: [0, 7],
  fe: [-20, 13], fh: [-12, 18], be: [-20, 3], bh: [-11, 2],
  fk: [14, 14], ff: [28, 4], bk: [13, 10], bf: [27, 2],
};
const KNEEL: Pose = {
  head: [6, 64], neck: [4, 56], hip: [-2, 30],
  fe: [12, 44], fh: [16, 36], be: [6, 42], bh: [10, 34],
  fk: [12, 22], ff: [14, 0], bk: [-12, 6], bf: [-22, 2],
};

// ---------------------------------------------------------------- moves

const LP0: Pose = { ...STANCE, fe: [8, 66], fh: [12, 72] };
const LP1: Pose = {
  ...STANCE, head: [8, 87], neck: [5, 78], hip: [1, 49],
  fe: [22, 77], fh: [36, 79], be: [8, 62], bh: [12, 66], bigHand: true,
};
const LP2: Pose = { ...LP1, fe: [20, 75], fh: [32, 76] };

const MP0: Pose = { ...STANCE, fe: [4, 64], fh: [8, 70], be: [0, 62], bh: [4, 68] };
const MP1: Pose = {
  ...STANCE, head: [8, 86], neck: [5, 77], hip: [1, 49],
  fe: [20, 66], fh: [34, 64], be: [18, 62], bh: [32, 58], bigHand: true,
};
const MP2: Pose = { ...MP1, fe: [18, 66], fh: [30, 64], be: [16, 62], bh: [28, 59] };

const DK0: Pose = {
  ...STANCE, head: [-4, 84], neck: [-3, 76], hip: [0, 48],
  fe: [-2, 62], fh: [2, 54], be: [-6, 62], bh: [-2, 54],
  fk: [10, 40], ff: [6, 26], bk: [-4, 25], bf: [-6, 0],
};
const DK1: Pose = {
  head: [-14, 70], neck: [-10, 64], hip: [0, 50],
  fe: [-12, 52], fh: [-14, 40], be: [-8, 50], bh: [-10, 38],
  fk: [14, 54], ff: [10, 40], bk: [-2, 26], bf: [-4, 0],
};
const DK2: Pose = {
  head: [-20, 58], neck: [-13, 56], hip: [2, 50],
  fe: [-16, 44], fh: [-20, 32], be: [-12, 42], bh: [-16, 30],
  fk: [22, 62], ff: [44, 72], bk: [0, 26], bf: [-2, 0],
};
const DK3: Pose = { ...DK2, fk: [18, 56], ff: [34, 58] };

const SW0: Pose = {
  head: [-3, 52], neck: [-2, 44], hip: [0, 22],
  fe: [-6, 32], fh: [-12, 24], be: [6, 32], bh: [12, 24],
  fk: [14, 12], ff: [24, 4], bk: [-4, 14], bf: [-8, 0],
};
const SWEEP_FRONT: Pose = {
  head: [-6, 51], neck: [-4, 44], hip: [0, 21],
  fe: [-12, 34], fh: [-18, 28], be: [-4, 30], bh: [-10, 22],
  fk: [22, 9], ff: [44, 4], bk: [-4, 14], bf: [-8, 0],
};
const SWEEP_BACK: Pose = {
  head: [6, 51], neck: [4, 44], hip: [0, 21],
  fe: [12, 34], fh: [18, 28], be: [4, 30], bh: [10, 22],
  fk: [-22, 9], ff: [-42, 4], bk: [4, 14], bf: [8, 0],
};

const LU0: Pose = {
  head: [12, 66], neck: [9, 58], hip: [0, 36],
  fe: [6, 50], fh: [2, 44], be: [12, 48], bh: [18, 52],
  fk: [14, 18], ff: [20, 0], bk: [-12, 16], bf: [-22, 0],
};
const LU1: Pose = {
  head: [14, 64], neck: [10, 56], hip: [2, 36],
  fe: [20, 52], fh: [32, 51], be: [8, 48], bh: [4, 42],
  fk: [16, 18], ff: [22, 0], bk: [-12, 16], bf: [-24, 0], bigHand: true,
};
const LU2: Pose = { ...LU1, fe: [18, 52], fh: [28, 51] };

const AX0: Pose = { ...STANCE, head: [3, 87], neck: [1, 78], fk: [12, 46], ff: [16, 30] };
const AX1: Pose = { ...STANCE, head: [1, 87], neck: [0, 78], hip: [-1, 50], fe: [6, 66], fh: [12, 72], fk: [12, 72], ff: [16, 98] };
const AX2: Pose = { ...AX1, fk: [16, 76], ff: [26, 102] };
const AX3: Pose = { ...AX1, head: [4, 86], neck: [2, 77], fk: [18, 72], ff: [30, 88] };
const AX4: Pose = { ...STANCE, head: [6, 85], neck: [4, 76], fk: [22, 62], ff: [34, 46] };
const AX5: Pose = { ...STANCE, fk: [20, 24], ff: [28, 0] };

const LE0: Pose = {
  head: [2, 84], neck: [0, 75], hip: [-2, 46],
  fe: [-6, 62], fh: [-12, 58], be: [8, 60], bh: [14, 64],
  fk: [10, 22], ff: [16, 0], bk: [-10, 22], bf: [-18, 0], bigHand: true,
};
const LE1: Pose = {
  head: [12, 80], neck: [8, 72], hip: [2, 44],
  fe: [24, 66], fh: [40, 64], be: [0, 58], bh: [-4, 52],
  fk: [16, 22], ff: [22, 0], bk: [-12, 20], bf: [-24, 0], bigHand: true,
};
const LE2: Pose = { ...LE1, fe: [20, 66], fh: [32, 64] };

const RP0: Pose = { ...CROUCH, fe: [16, 40], fh: [18, 34], be: [12, 38], bh: [16, 32], staff: [[20, 0], [14, 56]] };
const RP_FORWARD: Pose = {
  head: [5, 38], neck: [4, 46], hip: [2, 68],
  fe: [7, 39], fh: [4, 31], be: [-1, 39], bh: [1, 31],
  fk: [10, 84], ff: [18, 98], bk: [3, 83], bf: [8, 97],
  staff: [[1, -4], [5, 40]],
};
const RP_UP: Pose = { ...RP_FORWARD, fk: [4, 85], ff: [4, 102], bk: [-2, 84], bf: [-4, 100] };
const RP_SPLIT: Pose = { ...RP_FORWARD, fk: [8, 84], ff: [16, 98], bk: [-6, 84], bf: [-22, 96] };
const RP_FALL: Pose = { ...JUMP_DOWN, fe: [8, 64], fh: [12, 61], be: [-2, 64], bh: [-6, 61], staff: [[-12, 58], [18, 62]] };
const RP_LAND: Pose = { ...CROUCH, fe: [10, 40], fh: [14, 34], be: [-2, 40], bh: [-8, 32], staff: [[-14, 30], [18, 36]] };

interface MoveAnim {
  startup: Pose[];
  active: Pose[];
  recovery: Pose[];
  /** Pose while still falling after the move's frames are over. */
  fall?: Pose;
}

const MOVES: Record<string, MoveAnim> = {
  '5LP': { startup: [STANCE, LP0], active: [LP1], recovery: [LP2, LP0, STANCE] },
  '5MP': { startup: [MP0], active: [MP1], recovery: [MP2, MP0, STANCE] },
  '5HP': { startup: [DK0, DK1], active: [DK2], recovery: [DK2, DK3, DK0, STANCE] },
  '2HK': { startup: [CROUCH, SW0], active: [SWEEP_FRONT, SWEEP_BACK, SWEEP_FRONT, SWEEP_BACK], recovery: [SW0, CROUCH] },
  '6MP': { startup: [STANCE, LU0], active: [LU1], recovery: [LU2, LU0, STANCE] },
  '6MK': { startup: [AX0, AX1, AX2], active: [AX3, AX4, AX4], recovery: [AX5, STANCE] },
  leopard: { startup: [LE0], active: [LE1], recovery: [LE1, LE2, STANCE] },
  'rising.L': { startup: [RP0], active: [RP_FORWARD], recovery: [RP_FALL], fall: RP_FALL },
  'rising.M': { startup: [RP0], active: [RP_UP], recovery: [RP_FALL], fall: RP_FALL },
  'rising.H': {
    startup: [RP0],
    // 14 frames hitting above, then 6 frames reaching behind (matches the hitbox phases).
    active: [RP_UP, RP_UP, RP_UP, RP_UP, RP_UP, RP_UP, RP_UP, RP_SPLIT, RP_SPLIT, RP_SPLIT],
    recovery: [RP_FALL],
    fall: RP_FALL,
  },
};

const FALLBACK: MoveAnim = { startup: [LP0], active: [LP1], recovery: [STANCE] };

/** Spreads `poses` evenly over `length` frames and returns the one for `frame` (1-based). */
function spread(poses: Pose[], frame: number, length: number): Pose {
  if (!poses.length) return STANCE;
  const i = Math.floor(((frame - 1) * poses.length) / Math.max(1, length));
  return poses[Math.min(poses.length - 1, Math.max(0, i))];
}

function moveAnim(id: string): MoveAnim {
  return MOVES[id] ?? MOVES[id.split('.')[0]] ?? FALLBACK;
}

export function shotoPose(f: Fighter, clock: number): PoseResult {
  switch (f.state) {
    case 'ground':
      if (f.crouching) return { pose: CROUCH };
      if (f.walk) {
        const i = Math.floor(f.frame / 6) % 4;
        return { pose: WALK[f.walk > 0 ? i : 3 - i] };
      }
      return { pose: Math.floor(clock / 24) % 2 ? BREATHE : STANCE };
    case 'jumpSquat':
      return { pose: JUMP_SQUAT };
    case 'jump':
      return { pose: f.vy > 0 ? JUMP_UP : JUMP_DOWN };
    case 'landing':
      return { pose: f.lastMove?.id.startsWith('rising') ? RP_LAND : CROUCH };
    case 'hitstun':
      if (f.crouching) return { pose: CROUCH_HIT };
      return { pose: f.frame <= 4 ? HIT2 : HIT1 };
    case 'blockstun':
      return { pose: f.airBlock ? AIR_BLOCK : f.crouching ? CROUCH_BLOCK : BLOCK };
    case 'airReset':
      if (f.landed) return { pose: JUMP_DOWN };
      // One backward somersault, then upright until landing.
      return { pose: HIT2, rotate: Math.min(1, f.frame / 26) * Math.PI * 2, pivot: [0, 50] };
    case 'knockdown':
    case 'ko':
      if (!f.down) return { pose: HIT2, rotate: Math.min(1, f.frame / 12) * 1.3, pivot: [0, 30] };
      if (f.state === 'knockdown' && f.stun < 12) return { pose: f.stun >= 6 ? KNEEL : CROUCH };
      return { pose: LYING };
    case 'move': {
      const m = f.move!;
      const anim = moveAnim(m.id);
      const phase = movePhase(f);
      if (phase === 'startup') return { pose: spread(anim.startup, f.moveFrame, m.startup) };
      if (phase === 'active') return { pose: spread(anim.active, f.moveFrame - m.startup, m.active) };
      const k = f.moveFrame - m.startup - m.active;
      if (k > m.recovery) return { pose: anim.fall ?? STANCE };
      return { pose: spread(anim.recovery, k, m.recovery) };
    }
  }
}
