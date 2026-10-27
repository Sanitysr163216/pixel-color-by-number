import type { UBox } from '../moves/compile';

/** A box placed in the world, in simulation units. l < r, b < t (y goes up). */
export interface Rect {
  l: number;
  r: number;
  b: number;
  t: number;
}

/** Places a fighter-relative box in the world; boxes are mirrored when the fighter faces left. */
export function place(x: number, y: number, facing: number, box: UBox): Rect {
  const l = facing === 1 ? x + box.x : x - box.x - box.w;
  return { l, r: l + box.w, b: y + box.y, t: y + box.y + box.h };
}

/** Boxes that only touch edges don't overlap. */
export function overlap(a: Rect, b: Rect): boolean {
  return a.l < b.r && b.l < a.r && a.b < b.t && b.b < a.t;
}

export function intersection(a: Rect, b: Rect): Rect {
  return { l: Math.max(a.l, b.l), r: Math.min(a.r, b.r), b: Math.max(a.b, b.b), t: Math.min(a.t, b.t) };
}
