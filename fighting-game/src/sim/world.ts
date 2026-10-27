import { MAX_SEPARATION, RULES, STAGE_W, WALL_MARGIN } from '../config';
import { px } from '../core/units';
import type { CompiledCharacter, CompiledSpecial } from '../characters/compile';
import type { NormalSlot } from '../characters/types';
import {
  BTN,
  HEAVIEST_FIRST,
  KICKS,
  PUNCHES,
  STRENGTH_OF,
  countButtons,
  numpad,
  type ButtonName,
  type RawInput,
  type Strength,
} from '../input/buttons';
import { motionDone } from '../input/motions';
import { airHitResult, canAirBlock, type CompiledMove, type UBox } from '../moves/compile';
import { intersection, overlap, place, type Rect } from './boxes';
import { createFighter, type Fighter } from './fighter';

const GRAVITY = px(RULES.gravity);
const WALL_LEFT = px(WALL_MARGIN);
const WALL_RIGHT = px(STAGE_W - WALL_MARGIN);
const MAX_SEP = px(MAX_SEPARATION);
const PER_BAR = RULES.meter.perBar;
export const METER_MAX = RULES.meter.perBar * RULES.meter.bars;

export interface WorldEvent {
  type: 'hit' | 'block' | 'land';
  /** Where it happened, in simulation units (y up from the ground). */
  x: number;
  y: number;
  /** The attacker for hit/block; the fighter who hit the ground for land. */
  fighter: 0 | 1;
  strength: Strength;
  moveId: string;
}

/** Frame advantage of the last hit or block: positive = the attacker can act first. */
export interface Advantage {
  attacker: 0 | 1;
  blocked: boolean;
  value: number;
}

interface Contact {
  move: CompiledMove;
  fromAir: boolean;
  hit: number;
  where: Rect;
}

/**
 * The fight itself: two fighters and the rules. Advances exactly one frame (1/60 s) per step().
 * Nothing in here reads the clock or the keyboard, so the same inputs always give the same fight.
 */
export class World {
  frame = 0;
  readonly fighters: [Fighter, Fighter];
  /** What happened during the last step (for sparks and sounds). */
  readonly events: WorldEvent[] = [];
  advantage: Advantage | null = null;
  /** false in training: health stops at 1. */
  koEnabled = true;
  private measuring: { attacker: 0 | 1; blocked: boolean; free: [number | null, number | null] } | null = null;

  constructor(chars: [CompiledCharacter, CompiledCharacter]) {
    this.fighters = [createFighter(0, chars[0]), createFighter(1, chars[1])];
    this.resetRound();
  }

  /** Puts both fighters back at the start positions with full health. Meter is kept. */
  resetRound(gap = 140): void {
    const centre = px(STAGE_W / 2);
    for (const f of this.fighters) {
      f.x = centre + (f.index === 0 ? -1 : 1) * px(gap / 2);
      f.facing = f.index === 0 ? 1 : -1;
      f.health = f.char.health;
      f.hitstop = 0;
      f.slide = null;
      f.combo = { hits: 0, damage: 0 };
      f.lastMove = null;
      f.lastCommand = '';
      this.toGround(f);
    }
    this.advantage = null;
    this.measuring = null;
  }

  other(f: Fighter): Fighter {
    return this.fighters[f.index === 0 ? 1 : 0];
  }

  step(inputs: readonly [RawInput, RawInput]): void {
    this.frame++;
    this.events.length = 0;
    const fs = this.fighters;
    fs[0].input.push(inputs[0]);
    fs[1].input.push(inputs[1]);
    const frozen = [fs[0].hitstop > 0, fs[1].hitstop > 0];

    for (const f of fs) if (!frozen[f.index]) this.control(f);
    for (const f of fs) {
      if (frozen[f.index]) f.hitstop--;
      else this.advance(f);
    }
    for (const f of fs) if (!frozen[f.index]) this.slide(f);
    this.separate();
    for (const f of fs) this.face(f);

    // Both hits are found before either is applied, so two moves that connect on the same frame trade.
    const contacts = fs.map((f) => (frozen[f.index] ? null : this.findContact(f)));
    contacts.forEach((c, i) => c && this.applyContact(fs[i], c));
    this.finishMeasure();
  }

  // ---------------------------------------------------------------- per-frame control

  private control(f: Fighter): void {
    this.finish(f);
    const m = this.measuring;
    if (m && m.free[f.index] === null && this.isFree(f)) m.free[f.index] = this.frame;

    switch (f.state) {
      case 'ground':
        if (!this.tryMove(f)) this.groundMovement(f);
        break;
      case 'jump':
        if (!f.airActionUsed) this.tryMove(f);
        break;
      case 'move':
        this.tryUpgradeToCE(f);
        break;
      case 'blockstun':
        // Switch between standing and crouching block while blocking.
        if (!f.airBlock) f.crouching = f.input.get(0)!.y < 0;
        break;
    }
  }

  /** Ends states whose time is up. Runs before the fighter's input is read, so they can act on that same frame. */
  private finish(f: Fighter): void {
    switch (f.state) {
      case 'move':
        if (f.moveFrame < f.move!.total) return;
        if (f.y === 0) this.toGround(f);
        else if (f.moveFromAir) this.toJump(f, true);
        // A move that left the ground keeps falling until it lands (see landMove).
        return;
      case 'hitstun':
      case 'landing':
        if (f.stun <= 0) this.toGround(f);
        return;
      case 'blockstun':
        if (f.stun > 0) return;
        // Blocking in the air gives back the air attack (even if one was used this jump).
        if (f.airBlock) this.toJump(f, false);
        else this.toGround(f);
        return;
      case 'airReset':
        if (f.landed) this.toGround(f);
        return;
      case 'knockdown':
        // Wakeup: the hurtbox comes back on the same frame the buttons start working again.
        if (f.down && f.stun <= 0) this.toGround(f);
        return;
    }
  }

  private isFree(f: Fighter): boolean {
    return f.state === 'ground' || (f.state === 'jump' && !f.airActionUsed);
  }

  private groundMovement(f: Fighter): void {
    const input = f.input.get(0)!;
    const dir = numpad(input.x, input.y, f.facing);
    if (input.y > 0) {
      f.state = 'jumpSquat';
      f.frame = 0;
      f.jumpDir = dir === 9 ? 1 : dir === 7 ? -1 : 0;
      f.walk = 0;
      f.crouching = false;
      return;
    }
    f.crouching = input.y < 0;
    f.walk = f.crouching ? 0 : dir === 6 ? 1 : dir === 4 ? -1 : 0;
  }

  // ---------------------------------------------------------------- reading commands

  /** Looks at the presses of the last few frames (newest first) and starts a move if one matches. */
  private tryMove(f: Fighter): boolean {
    const air = f.state === 'jump';
    for (let age = 0; age <= RULES.inputBuffer; age++) {
      const frame = f.input.get(age);
      if (!frame) break;
      const fresh = frame.pressed & ~frame.used;
      if (fresh && this.resolve(f, age, fresh, air)) return true;
    }
    return false;
  }

  /**
   * Priority: Chakra specials, specials (CE when two punches or two kicks are pressed together),
   * command normals, normals. Returns true if a move started; a recognised input whose move doesn't
   * exist yet uses up the press and does nothing.
   */
  private resolve(f: Fighter, age: number, fresh: number, air: boolean): boolean {
    const c = f.char;
    const frame = f.input.get(age)!;
    if (!air) {
      for (const cs of c.chakraSpecials) {
        const type = cs.button === 'P' ? PUNCHES : KICKS;
        if (!(fresh & type) || !motionDone(f.input, cs.motion, cs.window, f.facing, age)) continue;
        if (f.meter < cs.move.barCost * PER_BAR) continue;
        this.use(f, age, fresh & type);
        f.meter -= cs.move.barCost * PER_BAR;
        this.startMove(f, cs.move, null);
        return true;
      }
      for (const sp of c.specials) {
        const type = sp.button === 'P' ? PUNCHES : KICKS;
        const pressed = fresh & type;
        if (!pressed || !motionDone(f.input, sp.motion, sp.window, f.facing, age)) continue;
        const together = this.pressedTogether(f, age, type);
        if (countButtons(together) >= 2) return this.startCE(f, sp, together, age, type);
        this.use(f, age, pressed);
        return this.startSpecial(f, sp, HEAVIEST_FIRST.find((b) => pressed & BTN[b])!);
      }
      const dir = numpad(frame.x, frame.y, f.facing);
      for (const cn of c.commandNormals) {
        if (cn.direction !== dir || !(fresh & BTN[cn.button])) continue;
        this.use(f, age, BTN[cn.button]);
        this.startMove(f, cn.move, null);
        return true;
      }
    }
    const stance = air ? 'j.' : frame.y < 0 ? '2' : '5';
    for (const b of HEAVIEST_FIRST) {
      if (!(fresh & BTN[b])) continue;
      const slot = `${stance}${b}` as NormalSlot;
      this.use(f, age, BTN[b]);
      const m = c.normals[slot];
      if (m) {
        this.startMove(f, m, null, stance === '2');
        return true;
      }
      this.note(f, `${slot}: EMPTY SLOT`);
    }
    return false;
  }

  /** Unused presses of `type` (punches or kicks) from frame `age` and the RULES.ceWindow frames before it. */
  private pressedTogether(f: Fighter, age: number, type: number): number {
    let mask = 0;
    for (let a = age; a <= age + RULES.ceWindow; a++) {
      const frame = f.input.get(a);
      if (frame) mask |= frame.pressed & ~frame.used & type;
    }
    return mask;
  }

  private startCE(f: Fighter, sp: CompiledSpecial, together: number, age: number, type: number): boolean {
    for (let a = age; a <= age + RULES.ceWindow; a++) this.use(f, a, type);
    const ce = sp.CE;
    if (!ce) {
      this.note(f, `CE ${sp.name}: NOT MADE YET`);
      return false;
    }
    if (f.meter >= ce.barCost * PER_BAR) {
      f.meter -= ce.barCost * PER_BAR;
      this.startMove(f, ce, null);
      return true;
    }
    // Not enough meter: the normal version of the heaviest button.
    return this.startSpecial(f, sp, HEAVIEST_FIRST.find((b) => together & BTN[b])!);
  }

  private startSpecial(f: Fighter, sp: CompiledSpecial, button: ButtonName): boolean {
    const m = sp[STRENGTH_OF[button]];
    if (!m) {
      this.note(f, `${sp.name} ${STRENGTH_OF[button]}: NOT MADE YET`);
      return false;
    }
    this.startMove(f, m, { def: sp, button });
    return true;
  }

  /** A second punch (or kick) right after a special started turns it into the CE version. */
  private tryUpgradeToCE(f: Fighter): void {
    const s = f.special;
    if (!s || f.moveFrame > RULES.ceWindow) return;
    const frame = f.input.get(0)!;
    const type = s.def.button === 'P' ? PUNCHES : KICKS;
    const second = frame.pressed & ~frame.used & type & ~BTN[s.button];
    if (!second) return;
    frame.used |= second;
    const ce = s.def.CE;
    if (!ce) {
      this.note(f, `CE ${s.def.name}: NOT MADE YET`);
      return;
    }
    if (f.meter < ce.barCost * PER_BAR) return;
    f.meter -= ce.barCost * PER_BAR;
    const moveFrame = f.moveFrame;
    this.startMove(f, ce, null);
    f.moveFrame = moveFrame; // the CE counts its frames from the first button
  }

  private use(f: Fighter, age: number, mask: number): void {
    const frame = f.input.get(age);
    if (frame) frame.used |= mask;
  }

  private note(f: Fighter, text: string): void {
    f.lastCommand = text;
    f.lastCommandFrame = this.frame;
  }

  private startMove(f: Fighter, m: CompiledMove, special: Fighter['special'], crouching = false): void {
    const air = f.state === 'jump';
    f.state = 'move';
    f.frame = 0;
    f.move = m;
    f.moveFrame = 0;
    f.moveFromAir = air;
    f.special = special;
    f.hitsDone = 0;
    f.walk = 0;
    if (air) {
      f.airActionUsed = true;
    } else {
      f.vx = 0;
      f.vy = 0;
      f.crouching = crouching;
    }
    f.lastMove = m;
    this.note(f, m.name.toUpperCase());
  }

  // ---------------------------------------------------------------- movement

  private advance(f: Fighter): void {
    f.frame++;
    const c = f.char;
    switch (f.state) {
      case 'ground':
        if (f.walk) this.moveX(f, f.facing * f.walk * (f.walk > 0 ? c.walkForward : c.walkBack));
        break;
      case 'jumpSquat':
        if (f.frame >= c.jump.squat) {
          f.state = 'jump';
          f.frame = 0;
          f.airActionUsed = false;
          f.vy = c.jump.up;
          f.vx = f.facing * (f.jumpDir > 0 ? c.jump.forward : f.jumpDir < 0 ? -c.jump.back : 0);
        }
        break;
      case 'jump':
        if (this.fall(f)) this.toGround(f);
        break;
      case 'move':
        this.advanceMove(f);
        break;
      case 'hitstun':
      case 'landing':
        f.stun--;
        break;
      case 'blockstun':
        f.stun--;
        if (f.airBlock && this.fall(f)) f.airBlock = false; // landed while blocking: keeps blocking on the ground
        break;
      case 'airReset':
        if (!f.landed && this.fall(f)) {
          f.landed = true;
          f.vx = 0;
        }
        break;
      case 'knockdown':
      case 'ko':
        if (f.down) {
          f.stun--;
        } else if (this.fall(f)) {
          // The wakeup count starts on the frame they touch the ground (that frame is the first one).
          f.down = true;
          f.vx = 0;
          f.stun = Math.round(RULES.knockdown.wakeup * f.wakeupMultiplier) - 1;
          this.events.push({ type: 'land', x: f.x, y: 0, fighter: f.index, strength: 'M', moveId: '' });
        }
        break;
    }
  }

  private advanceMove(f: Fighter): void {
    const m = f.move!;
    f.moveFrame++;
    for (const s of m.motion) {
      if (s.frame !== f.moveFrame) continue;
      if (s.forward !== undefined) f.vx = f.facing * s.forward;
      if (s.up !== undefined) f.vy = s.up;
    }
    if (f.y > 0 || f.vy > 0) {
      if (this.fall(f)) this.landMove(f);
    } else if (f.vx) {
      this.moveX(f, f.vx);
    }
  }

  /** A move in the air touched the ground: it ends, followed by its landing recovery. */
  private landMove(f: Fighter): void {
    const recovery = f.moveFromAir ? RULES.airAttackLanding : f.move!.landingRecovery;
    if (recovery <= 1) {
      this.toGround(f);
      return;
    }
    // Recovery R: the fighter touches the ground on frame L and can act again on frame L + R.
    this.toGround(f);
    f.state = 'landing';
    f.stun = recovery - 1;
  }

  /** Moves an airborne fighter one frame. Returns true when they touch the ground. */
  private fall(f: Fighter): boolean {
    if (f.vx) this.moveX(f, f.vx);
    f.y += f.vy;
    f.vy -= GRAVITY;
    if (f.y > 0) return false;
    f.y = 0;
    f.vy = 0;
    return true;
  }

  /** Moves a fighter sideways, stopping at the stage walls and at the maximum distance from the other fighter. */
  private moveX(f: Fighter, dx: number): number {
    const o = this.other(f);
    const lo = Math.max(WALL_LEFT, o.x - MAX_SEP);
    const hi = Math.min(WALL_RIGHT, o.x + MAX_SEP);
    const before = f.x;
    f.x = Math.min(hi, Math.max(lo, f.x + dx));
    return f.x - before;
  }

  /** Knockback: slides the fighter away; whatever a wall stops is pushed onto the attacker instead. */
  private slide(f: Fighter): void {
    const s = f.slide;
    if (!s) return;
    const step = Math.min(s.speed, s.left);
    s.left -= step;
    const stuck = step - Math.abs(this.moveX(f, s.dir * step));
    const attacker = this.other(f);
    if (stuck > 0 && s.from === attacker.index && attacker.y === 0 && attacker.state !== 'knockdown') {
      this.moveX(attacker, -s.dir * stuck);
    }
    if (s.left <= 0) f.slide = null;
  }

  /** Pushboxes: fighters can't stand inside each other. */
  private separate(): void {
    const [a, b] = this.fighters;
    const pa = this.pushbox(a);
    const pb = this.pushbox(b);
    if (!pa || !pb || !overlap(pa, pb)) return;
    const amount = Math.min(pa.r, pb.r) - Math.max(pa.l, pb.l);
    const aLeft = a.x !== b.x ? a.x < b.x : a.facing === 1;
    const left = aLeft ? a : b;
    const right = aLeft ? b : a;
    const movedLeft = this.shove(left, -Math.floor(amount / 2));
    const movedRight = this.shove(right, amount + movedLeft);
    const rest = amount + movedLeft - movedRight;
    if (rest > 0) this.shove(left, -rest);
  }

  private shove(f: Fighter, dx: number): number {
    const before = f.x;
    f.x = Math.min(WALL_RIGHT, Math.max(WALL_LEFT, f.x + dx));
    return f.x - before;
  }

  private face(f: Fighter): void {
    if (f.state !== 'ground') return;
    const o = this.other(f);
    if (o.x > f.x) f.facing = 1;
    else if (o.x < f.x) f.facing = -1;
  }

  private toGround(f: Fighter): void {
    f.state = 'ground';
    f.frame = 0;
    f.move = null;
    f.special = null;
    f.y = 0;
    f.vx = 0;
    f.vy = 0;
    f.walk = 0;
    f.stun = 0;
    f.airBlock = false;
    f.landed = false;
    f.down = false;
    f.airActionUsed = false;
    const input = f.input.get(0);
    f.crouching = !!input && input.y < 0;
  }

  private toJump(f: Fighter, airActionUsed: boolean): void {
    f.state = 'jump';
    f.frame = 0;
    f.move = null;
    f.special = null;
    f.airBlock = false;
    f.airActionUsed = airActionUsed;
  }

  // ---------------------------------------------------------------- hitting

  private findContact(att: Fighter): Contact | null {
    const m = att.move;
    if (att.state !== 'move' || !m) return null;
    const def = this.other(att);
    const hurt = this.hurtboxes(def).map((b) => place(def.x, def.y, def.facing, b));
    if (!hurt.length) return null;
    for (const phase of m.hitPhases) {
      if (att.moveFrame < phase.from || att.moveFrame > phase.to) continue;
      if (att.hitsDone & (1 << phase.hit)) continue;
      for (const box of phase.boxes) {
        const hb = place(att.x, att.y, att.facing, box);
        for (const h of hurt) {
          if (overlap(hb, h)) return { move: m, fromAir: att.moveFromAir, hit: phase.hit, where: intersection(hb, h) };
        }
      }
    }
    return null;
  }

  private applyContact(att: Fighter, c: Contact): void {
    const def = this.other(att);
    const m = c.move;
    att.hitsDone |= 1 << c.hit;
    const air = this.isAirborne(def);
    const blocked = this.blocks(def, att, m, c.fromAir, air);
    att.hitstop = Math.max(att.hitstop, m.hitstop);
    def.hitstop = Math.max(def.hitstop, m.hitstop);
    const away = def.x > att.x ? 1 : def.x < att.x ? -1 : att.facing;
    const knockback = { left: m.knockback.distance, speed: m.knockback.speed, dir: away, from: att.index };

    if (blocked) {
      def.state = 'blockstun';
      def.frame = 0;
      def.stun = m.blockstun;
      def.airBlock = air;
      def.move = null;
      def.special = null;
      def.walk = 0;
      if (air) def.vx = 0;
      def.slide = knockback;
      def.meter = Math.min(METER_MAX, def.meter + RULES.meter.onBlock);
      def.combo = { hits: 0, damage: 0 };
    } else {
      let damage = m.damage;
      const vulnerable = def.state === 'move' ? def.move!.vulnerable : null;
      if (vulnerable && def.moveFrame >= vulnerable.from && def.moveFrame <= vulnerable.to) {
        damage *= vulnerable.damageMultiplier;
      }
      damage = Math.round(damage);
      def.combo = def.state === 'hitstun'
        ? { hits: def.combo.hits + 1, damage: def.combo.damage + damage }
        : { hits: 1, damage };
      def.health = Math.max(this.koEnabled ? 0 : 1, def.health - damage);
      att.meter = Math.min(METER_MAX, att.meter + m.meterOnHit);
      def.move = null;
      def.special = null;
      def.slide = null;
      def.airBlock = false;
      def.walk = 0;
      if (def.health <= 0) {
        this.knockDown(def, away, 1, 'ko');
      } else if (air) {
        if (airHitResult(m, c.fromAir) === 'reset') this.airReset(def, away);
        else this.knockDown(def, away, m.knockdown?.wakeupMultiplier ?? 1, 'knockdown');
      } else if (m.knockdown) {
        this.knockDown(def, away, m.knockdown.wakeupMultiplier, 'knockdown');
      } else {
        def.state = 'hitstun';
        def.frame = 0;
        def.stun = m.hitstun;
        def.slide = knockback;
      }
    }

    this.events.push({
      type: blocked ? 'block' : 'hit',
      x: (c.where.l + c.where.r) / 2,
      y: (c.where.b + c.where.t) / 2,
      fighter: att.index,
      strength: m.strength,
      moveId: m.id,
    });
    this.measuring = { attacker: att.index, blocked, free: [null, null] };
  }

  /** Hold back to block. Crouch to block lows, stand to block overheads. In the air, see canAirBlock. */
  private blocks(def: Fighter, att: Fighter, m: CompiledMove, fromAir: boolean, air: boolean): boolean {
    if (def.state !== 'ground' && def.state !== 'blockstun' && def.state !== 'jump') return false;
    if (air && !canAirBlock(m, fromAir)) return false;
    if (def.autoBlock) {
      if (!air && m.guard !== 'mid') def.crouching = m.guard === 'low';
      return true;
    }
    const input = def.input.get(0)!;
    const away = att.x > def.x ? -1 : att.x < def.x ? 1 : -def.facing;
    if (input.x !== away) return false;
    if (air) return true;
    const crouch = input.y < 0;
    if ((m.guard === 'low' && !crouch) || (m.guard === 'overhead' && crouch)) return false;
    def.crouching = crouch;
    return true;
  }

  private airReset(f: Fighter, away: number): void {
    f.state = 'airReset';
    f.frame = 0;
    f.landed = false;
    f.crouching = false;
    f.vx = away * px(RULES.airReset.pushAway);
    f.vy = px(RULES.airReset.popUp);
  }

  private knockDown(f: Fighter, away: number, wakeupMultiplier: number, state: 'knockdown' | 'ko'): void {
    f.state = state;
    f.frame = 0;
    f.down = false;
    f.landed = false;
    f.crouching = false;
    f.wakeupMultiplier = wakeupMultiplier;
    f.vx = away * px(RULES.knockdown.pushAway);
    f.vy = px(RULES.knockdown.popUp);
  }

  private finishMeasure(): void {
    const m = this.measuring;
    if (!m) return;
    const att = m.free[m.attacker];
    const def = m.free[m.attacker === 0 ? 1 : 0];
    if (att === null || def === null) return;
    this.advantage = { attacker: m.attacker, blocked: m.blocked, value: def - att };
    this.measuring = null;
  }

  // ---------------------------------------------------------------- queries (also used for drawing)

  isAirborne(f: Fighter): boolean {
    if (f.y > 0 || f.state === 'jump') return true;
    if (f.state === 'blockstun') return f.airBlock;
    if (f.state === 'move') return f.move!.airborne.some(([a, b]) => f.moveFrame >= a && f.moveFrame <= b);
    return false;
  }

  isInvulnerable(f: Fighter): boolean {
    if (f.state === 'airReset' || f.state === 'knockdown' || f.state === 'ko') return true;
    return f.state === 'move' && f.move!.invincible.some(([a, b]) => f.moveFrame >= a && f.moveFrame <= b);
  }

  /** The boxes that can be hit right now (empty while invulnerable). */
  hurtboxes(f: Fighter): UBox[] {
    if (this.isInvulnerable(f)) return [];
    const h = f.char.hurt;
    if (f.state !== 'move') {
      if (f.state === 'jump' || (f.state === 'blockstun' && f.airBlock)) return h.air;
      return f.crouching ? h.crouch : h.stand;
    }
    const m = f.move!;
    let boxes = f.moveFromAir ? h.air : f.crouching ? h.crouch : h.stand;
    for (const p of m.hurtPhases) if (p.replace && f.moveFrame >= p.from && f.moveFrame <= p.to) boxes = p.boxes;
    for (const p of m.hurtPhases) if (!p.replace && f.moveFrame >= p.from && f.moveFrame <= p.to) boxes = boxes.concat(p.boxes);
    return boxes;
  }

  /** Hitbox phases that exist right now; `spent` = already connected. */
  hitboxes(f: Fighter): { boxes: UBox[]; spent: boolean }[] {
    const m = f.move;
    if (f.state !== 'move' || !m) return [];
    return m.hitPhases
      .filter((p) => f.moveFrame >= p.from && f.moveFrame <= p.to)
      .map((p) => ({ boxes: p.boxes, spent: (f.hitsDone & (1 << p.hit)) !== 0 }));
  }

  pushbox(f: Fighter): Rect | null {
    const p = f.char.push;
    if (f.state === 'airReset') return null;
    if (f.state === 'knockdown' || f.state === 'ko') return f.down ? place(f.x, f.y, f.facing, p.down) : null;
    const box = this.isAirborne(f) ? p.air : f.crouching ? p.crouch : p.stand;
    return place(f.x, f.y, f.facing, box);
  }
}
