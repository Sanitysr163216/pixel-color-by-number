import { CHARACTERS } from '../characters';
import { NEUTRAL, buttonsIn, numpad, type RawInput } from '../input/buttons';
import { METER_MAX, World, type WorldEvent } from '../sim/world';

export type Mode = 'training' | 'versus';
export type DummyStance = 'stand' | 'crouch' | 'jump';

/** One line of the input display: a direction (numpad), buttons pressed with it, and how long it was held. */
export interface InputLogEntry {
  dir: number;
  buttons: string;
  frames: number;
}

export interface Effect {
  event: WorldEvent;
  start: number;
}

/**
 * Everything around the fight itself: training mode (dummy, health refill, pause and frame step),
 * versus mode (KO and next round), the input display and hit sparks.
 */
export class Game {
  readonly world = new World([CHARACTERS.shoto, CHARACTERS.shoto]);
  mode: Mode = 'training';
  paused = false;
  showBoxes = true;
  showInfo = true;
  dummyStance: DummyStance = 'stand';
  dummyBlock = false;
  fullMeter = false;
  readonly inputLog: [InputLogEntry[], InputLogEntry[]] = [[], []];
  readonly effects: Effect[] = [];
  banner: { text: string; until: number } | null = null;
  private stepOnce = false;
  private koAt = 0;
  private readonly calmFor = [0, 0];

  constructor() {
    this.setMode('training');
  }

  setMode(mode: Mode): void {
    this.mode = mode;
    this.world.koEnabled = mode === 'versus';
    this.reset();
    this.banner = { text: mode === 'versus' ? 'FIGHT!' : 'TRAINING', until: this.world.frame + 60 };
  }

  reset(): void {
    this.world.resetRound();
    this.effects.length = 0;
    this.koAt = 0;
  }

  togglePause(): void {
    this.paused = !this.paused;
  }

  /** While paused: advance exactly one frame on the next tick. */
  stepFrame(): void {
    if (this.paused) this.stepOnce = true;
  }

  cycleDummyStance(): void {
    const order: DummyStance[] = ['stand', 'crouch', 'jump'];
    this.dummyStance = order[(order.indexOf(this.dummyStance) + 1) % order.length];
  }

  /** Advances the game by one frame unless paused. Returns false if nothing happened. */
  tick(p1: RawInput, p2: RawInput): boolean {
    if (this.paused && !this.stepOnce) return false;
    this.stepOnce = false;
    const w = this.world;
    const training = this.mode === 'training';
    const p2Input = training ? this.dummyInput() : p2;
    w.fighters[1].autoBlock = training && this.dummyBlock;
    w.step([p1, p2Input]);

    this.logInput(0, p1);
    this.logInput(1, p2Input);
    for (const event of w.events) this.effects.push({ event, start: w.frame });
    while (this.effects.length && w.frame - this.effects[0].start > 40) this.effects.shift();

    if (training) this.trainingUpkeep();
    else this.versusUpkeep();
    return true;
  }

  private dummyInput(): RawInput {
    if (this.dummyStance === 'crouch') return { ...NEUTRAL, y: -1 };
    if (this.dummyStance === 'jump') return { ...NEUTRAL, y: 1 };
    return NEUTRAL;
  }

  /** Training: health comes back once a fighter has been left alone for a moment. */
  private trainingUpkeep(): void {
    for (const f of this.world.fighters) {
      const calm = f.state === 'ground' || f.state === 'jump';
      this.calmFor[f.index] = calm ? this.calmFor[f.index] + 1 : 0;
      if (this.calmFor[f.index] > 50) f.health = f.char.health;
      if (this.fullMeter) f.meter = METER_MAX;
    }
  }

  private versusUpkeep(): void {
    const w = this.world;
    if (!w.fighters.some((f) => f.state === 'ko')) return;
    if (!this.koAt) {
      this.koAt = w.frame;
      this.banner = { text: 'K.O.', until: w.frame + 150 };
    } else if (w.frame - this.koAt > 180) {
      this.reset();
      this.banner = { text: 'FIGHT!', until: w.frame + 60 };
    }
  }

  private logInput(i: 0 | 1, input: RawInput): void {
    const dir = numpad(input.x, input.y, this.world.fighters[i].facing);
    const buttons = buttonsIn(input.pressed).join('+');
    const log = this.inputLog[i];
    const last = log[0];
    if (last && last.dir === dir && !buttons) {
      last.frames++;
      return;
    }
    log.unshift({ dir, buttons, frames: 1 });
    if (log.length > 14) log.pop();
  }
}
