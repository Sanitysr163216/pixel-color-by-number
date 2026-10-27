import type { Color, Framebuffer } from './framebuffer';
import type { FighterPalette } from './palette';

/** A point relative to the fighter: x forward from the centre, y up from the feet, in pixels. */
export type P = readonly [number, number];

/**
 * A placeholder body pose: joint positions for a fighter facing right.
 * f… = the limb nearer the viewer (drawn in front of the body), b… = the far limb.
 * e = elbow, h = hand, k = knee, f = foot.
 */
export interface Pose {
  head: P;
  neck: P;
  hip: P;
  fe: P;
  fh: P;
  be: P;
  bh: P;
  fk: P;
  ff: P;
  bk: P;
  bf: P;
  /** A staff held in the hands, from one end to the other. */
  staff?: readonly [P, P];
  /** Front hand drawn bigger: an open palm or a clenched fist. */
  bigHand?: boolean;
}

export interface FigureOptions {
  /** Screen position of the fighter's origin (centre, at the feet). */
  x: number;
  y: number;
  facing: number;
  palette: FighterPalette;
  /** Rotation in radians around `pivot`, counter-clockwise for a fighter facing right (flips, falls). */
  rotate?: number;
  pivot?: P;
}

export type ScreenPoints = Record<'head' | 'neck' | 'hip' | 'fh' | 'bh' | 'ff' | 'bf', [number, number]>;

/** Draws a chunky outlined mannequin. Returns where some joints ended up on screen (for effects). */
export function drawFigure(fb: Framebuffer, pose: Pose, o: FigureOptions): ScreenPoints {
  const angle = o.rotate ?? 0;
  const [px, py] = o.pivot ?? pose.hip;
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const T = (p: P): [number, number] => {
    const dx = p[0] - px;
    const dy = p[1] - py;
    const lx = px + dx * cos - dy * sin;
    const ly = py + dx * sin + dy * cos;
    return [o.x + o.facing * lx, o.y - ly];
  };
  const add = (p: P, dx: number, dy: number): P => [p[0] + dx, p[1] + dy];
  const lerp = (a: P, b: P, t: number): P => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  const pal = o.palette;

  const limb = (points: P[], r: number, color: Color) => {
    const s = points.map(T);
    for (let i = 0; i + 1 < s.length; i++) fb.capsule(s[i][0], s[i][1], s[i + 1][0], s[i + 1][1], r + 1, pal.outline);
    for (let i = 0; i + 1 < s.length; i++) fb.capsule(s[i][0], s[i][1], s[i + 1][0], s[i + 1][1], r, color);
  };
  const ball = (p: P, r: number, color: Color) => {
    const [x, y] = T(p);
    fb.disc(x, y, r + 1, pal.outline);
    fb.disc(x, y, r, color);
  };
  const foot = (ankle: P, color: Color) => limb([ankle, add(ankle, 5, -1)], 2, color);

  const { head, neck, hip } = pose;
  const shoulderF = add(neck, 1, -3);
  const shoulderB = add(neck, -1, -3);

  // Far arm and leg.
  limb([shoulderB, pose.be, pose.bh], 3, pal.giShade);
  ball(pose.bh, 3, pal.skinShade);
  limb([hip, pose.bk, pose.bf], 4, pal.pantsShade);
  foot(pose.bf, pal.skinShade);

  // Body: chest, waist, belt.
  const waist = lerp(neck, hip, 0.55);
  limb([add(neck, 0, -2), waist], 7, pal.gi);
  limb([waist, hip], 6, pal.gi);
  const beltC = lerp(neck, hip, 0.86);
  const ax = hip[0] - neck[0];
  const ay = hip[1] - neck[1];
  const len = Math.hypot(ax, ay) || 1;
  const nx = (-ay / len) * 6;
  const ny = (ax / len) * 6;
  limb([add(beltC, nx, ny), add(beltC, -nx, -ny)], 1.5, pal.accent);

  // Head: hair at the back, face, headband with its tail, eye.
  ball(head, 7, pal.hair);
  const [fx, fy] = T(add(head, 1.5, -1));
  fb.disc(fx, fy, 6, pal.skin);
  limb([add(head, -6, 3), add(head, 6, 3)], 1, pal.accent);
  limb([add(head, -6, 3), add(head, -11, 0)], 1, pal.accent);
  const [ex, ey] = T(add(head, 4, 1));
  fb.pixel(ex, ey, pal.outline);
  fb.pixel(ex, ey - 1, pal.outline);

  if (pose.staff) limb([pose.staff[0], pose.staff[1]], 1.5, pal.staff);

  // Near leg and arm.
  limb([hip, pose.fk, pose.ff], 4, pal.pants);
  foot(pose.ff, pal.skin);
  limb([shoulderF, pose.fe, pose.fh], 3, pal.gi);
  ball(pose.fh, pose.bigHand ? 4 : 3, pal.skin);

  return { head: T(head), neck: T(neck), hip: T(hip), fh: T(pose.fh), bh: T(pose.bh), ff: T(pose.ff), bf: T(pose.bf) };
}
