import { RULES, STRENGTH_DEFAULTS } from '../config';
import { px } from '../core/units';
import type { Strength } from '../input/buttons';
import type { Box, Guard, MoveData, MoveKind } from './types';

/** A box in simulation units. */
export interface UBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** A move with every default filled in, frames turned into move-frame ranges and pixels into units. */
export interface CompiledMove {
  id: string;
  name: string;
  kind: MoveKind;
  strength: Strength;
  /** How it has to be blocked when done from the ground. */
  guard: Guard;
  /** How it has to be blocked when done in the air (overhead unless the move says otherwise). */
  airGuard: Guard;
  startup: number;
  active: number;
  recovery: number;
  /** startup + active + recovery. The fighter can act again on frame total + 1. */
  total: number;
  damage: number;
  hitstun: number;
  blockstun: number;
  /** The move's own hitstop, or null to use the character's hitstop table. */
  hitstop: number | null;
  knockback: { distance: number; speed: number };
  /** Move frames (1 = first startup frame) where each hitbox phase exists. */
  hitPhases: { from: number; to: number; boxes: UBox[]; hit: number }[];
  hurtPhases: { from: number; to: number; boxes: UBox[]; replace: boolean }[];
  motion: { frame: number; forward?: number; up?: number }[];
  landingRecovery: number;
  knockdown: { wakeupMultiplier: number } | null;
  airHit?: 'reset' | 'knockdown';
  airBlockable?: boolean;
  invincible: [number, number][];
  airborne: [number, number][];
  vulnerable: { from: number; to: number; damageMultiplier: number } | null;
  meterOnHit: number;
  barCost: number;
  /** The move as written, for display. */
  data: MoveData;
}

export function ubox(b: Box): UBox {
  return { x: px(b.x), y: px(b.y), w: px(b.w), h: px(b.h) };
}

/** Fills in defaults and checks the numbers, with an error message that says which move is wrong. */
export function compileMove(id: string, m: MoveData): CompiledMove {
  const fail = (message: string): never => {
    throw new Error(`Move ${id} (${m.name}): ${message}`);
  };
  const whole = (value: number, field: string, min = 0) => {
    if (!Number.isInteger(value) || value < min) fail(`${field} must be a whole number of at least ${min}, not ${value}`);
  };
  const range = (r: [number, number], field: string) => {
    whole(r[0], `${field} start`, 1);
    whole(r[1], `${field} end`, 1);
    if (r[0] > r[1]) fail(`${field} [${r[0]}, ${r[1]}] ends before it starts`);
  };

  whole(m.startup, 'startup');
  whole(m.active, 'active', 1);
  whole(m.recovery, 'recovery');
  whole(m.hitstun, 'hitstun');
  whole(m.blockstun, 'blockstun');
  if (!(m.damage >= 0)) fail(`damage must be 0 or more, not ${m.damage}`);
  if (m.hitstop !== undefined) whole(m.hitstop, 'hitstop');
  if (m.landingRecovery !== undefined) whole(m.landingRecovery, 'landingRecovery');
  if (m.knockback && !(m.knockback.distance >= 0 && m.knockback.speed > 0))
    fail('knockback needs a distance of 0 or more and a speed above 0');
  if (!m.hitboxes.length) fail('needs at least one hitbox phase');

  const defaults = STRENGTH_DEFAULTS[m.strength];
  const knockback = m.knockback ?? defaults.knockback;

  const hitPhases = m.hitboxes.map((p, i) => {
    const [a, b] = p.frames ?? [1, m.active];
    range([a, b], `hitboxes[${i}].frames`);
    if (b > m.active) fail(`hitboxes[${i}].frames [${a}, ${b}] go past the ${m.active} active frame(s)`);
    if (!p.boxes.length) fail(`hitboxes[${i}] has no boxes`);
    const hit = p.hit ?? 0;
    if (!Number.isInteger(hit) || hit < 0 || hit > 30) fail(`hitboxes[${i}].hit must be a whole number from 0 to 30`);
    return { from: m.startup + a, to: m.startup + b, boxes: p.boxes.map(ubox), hit };
  });

  const hurtPhases = (m.hurtboxes ?? []).map((p, i) => {
    range(p.frames, `hurtboxes[${i}].frames`);
    return { from: p.frames[0], to: p.frames[1], boxes: p.boxes.map(ubox), replace: p.replace ?? false };
  });

  (m.invincible ?? []).forEach((r, i) => range(r, `invincible[${i}]`));
  (m.airborne ?? []).forEach((r, i) => range(r, `airborne[${i}]`));
  (m.motion ?? []).forEach((s, i) => whole(s.frame, `motion[${i}].frame`, 1));

  let vulnerable: CompiledMove['vulnerable'] = null;
  if (m.vulnerable) {
    const [from, to] = m.vulnerable.frames === 'startup' ? [1, m.startup] : m.vulnerable.frames;
    if (m.vulnerable.frames !== 'startup') range([from, to], 'vulnerable.frames');
    vulnerable = { from, to, damageMultiplier: m.vulnerable.damageMultiplier };
  }

  return {
    id,
    name: m.name,
    kind: m.kind,
    strength: m.strength,
    guard: m.guard ?? 'mid',
    // Jumping attacks have to be blocked standing unless the move says otherwise.
    airGuard: m.guard ?? 'overhead',
    startup: m.startup,
    active: m.active,
    recovery: m.recovery,
    total: m.startup + m.active + m.recovery,
    damage: m.damage,
    hitstun: m.hitstun,
    blockstun: m.blockstun,
    hitstop: m.hitstop ?? null,
    knockback: { distance: px(knockback.distance), speed: px(knockback.speed) },
    hitPhases,
    hurtPhases,
    motion: (m.motion ?? []).map((s) => ({
      frame: s.frame,
      forward: s.forward === undefined ? undefined : px(s.forward),
      up: s.up === undefined ? undefined : px(s.up),
    })),
    landingRecovery: m.landingRecovery ?? 0,
    knockdown: m.knockdown === undefined ? null : m.knockdown === true ? { wakeupMultiplier: 1 } : m.knockdown,
    airHit: m.airHit,
    airBlockable: m.airBlockable,
    invincible: m.invincible ?? [],
    airborne: m.airborne ?? [],
    vulnerable,
    meterOnHit: m.meterOnHit ?? RULES.meter.onHitPerLevel * defaults.meterLevel,
    barCost: m.barCost ?? (m.kind === 'ce' ? 1 : 0),
    data: m,
  };
}

/** Normals and command normals: the moves the light/medium/heavy air rules talk about. */
export function isNormal(m: CompiledMove): boolean {
  return m.kind === 'normal' || m.kind === 'command';
}

/** What an airborne opponent does when this move hits them (see MoveData.airHit). */
export function airHitResult(m: CompiledMove, fromAir: boolean): 'reset' | 'knockdown' {
  if (m.airHit) return m.airHit;
  if (isNormal(m) && m.strength !== 'H') return 'reset';
  return fromAir ? 'reset' : 'knockdown';
}

/** Whether an airborne opponent may block this move (see MoveData.airBlockable). */
export function canAirBlock(m: CompiledMove, fromAir: boolean): boolean {
  if (m.airBlockable !== undefined) return m.airBlockable;
  if (fromAir) return true;
  return isNormal(m) && m.strength !== 'H';
}
