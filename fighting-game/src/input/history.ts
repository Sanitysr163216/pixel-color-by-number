import type { RawInput } from './buttons';

export interface InputFrame extends RawInput {
  /** Buttons from `pressed` that already did something, so a buffered press can't trigger twice. */
  used: number;
}

/** The last few seconds of one player's input. get(0) is the newest frame, get(1) the one before, … */
export class InputHistory {
  private readonly frames: InputFrame[] = [];

  constructor(private readonly size = 90) {}

  push(input: RawInput): void {
    this.frames.unshift({ x: input.x, y: input.y, held: input.held, pressed: input.pressed, used: 0 });
    if (this.frames.length > this.size) this.frames.pop();
  }

  get(age: number): InputFrame | undefined {
    return this.frames[age];
  }

  get length(): number {
    return this.frames.length;
  }

  clear(): void {
    this.frames.length = 0;
  }
}
