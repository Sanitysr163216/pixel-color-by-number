import { BTN, BUTTONS, type ButtonName, type RawInput } from '../input/buttons';

/** Keyboard layout per player, by physical key (KeyboardEvent.code), so it works on any keyboard language. */
export interface KeyMap {
  up: string;
  down: string;
  left: string;
  right: string;
  buttons: Record<ButtonName, string>;
}

export const KEYS: [KeyMap, KeyMap] = [
  {
    up: 'KeyW',
    down: 'KeyS',
    left: 'KeyA',
    right: 'KeyD',
    buttons: { LP: 'KeyU', MP: 'KeyI', HP: 'KeyO', LK: 'KeyJ', MK: 'KeyK', HK: 'KeyL' },
  },
  {
    up: 'ArrowUp',
    down: 'ArrowDown',
    left: 'ArrowLeft',
    right: 'ArrowRight',
    buttons: { LP: 'Numpad4', MP: 'Numpad5', HP: 'Numpad6', LK: 'Numpad1', MK: 'Numpad2', HK: 'Numpad3' },
  },
];

/**
 * Standard gamepad buttons for a 6-button layout (Xbox names):
 * X Y RB = LP MP HP, A B RT = LK MK HK. D-pad or left stick to move.
 */
const PAD_BUTTONS: Record<ButtonName, number> = { LP: 2, MP: 3, HP: 5, LK: 0, MK: 1, HK: 7 };

/** Remembers every key that went down between two game frames, so a quick tap is never lost. */
export class Keyboard {
  private readonly down = new Set<string>();
  private readonly tapped = new Set<string>();
  private readonly systemTaps = new Set<string>();

  constructor(private readonly gameKeys: Set<string>) {}

  attach(target: Window): void {
    target.addEventListener('keydown', (e) => {
      if (this.gameKeys.has(e.code) || e.code.startsWith('Digit') || e.code.startsWith('Numpad')) e.preventDefault();
      if (e.repeat) return;
      this.down.add(e.code);
      this.tapped.add(e.code);
      this.systemTaps.add(e.code);
    });
    target.addEventListener('keyup', (e) => this.down.delete(e.code));
    target.addEventListener('blur', () => this.down.clear());
  }

  read(map: KeyMap): RawInput {
    const on = (code: string) => this.down.has(code);
    // Left + right together = neutral, up + down together = neutral.
    const x = (on(map.right) ? 1 : 0) - (on(map.left) ? 1 : 0);
    const y = (on(map.up) ? 1 : 0) - (on(map.down) ? 1 : 0);
    let held = 0;
    let pressed = 0;
    for (const b of BUTTONS) {
      if (on(map.buttons[b])) held |= BTN[b];
      if (this.tapped.has(map.buttons[b])) pressed |= BTN[b];
    }
    return { x, y, held, pressed };
  }

  /** Call after a game frame has used the presses. */
  endFrame(): void {
    this.tapped.clear();
  }

  /** For menu keys: true once per press. */
  takeTap(code: string): boolean {
    return this.systemTaps.delete(code);
  }

  clearTaps(): void {
    this.systemTaps.clear();
  }
}

export class Gamepads {
  private readonly lastHeld = [0, 0];

  read(index: number): RawInput | null {
    const pad = navigator.getGamepads?.()[index];
    if (!pad) return null;
    const pressedButton = (i: number) => !!pad.buttons[i]?.pressed;
    let held = 0;
    for (const b of BUTTONS) if (pressedButton(PAD_BUTTONS[b])) held |= BTN[b];
    const ax = pad.axes[0] ?? 0;
    const ay = pad.axes[1] ?? 0;
    const x = (pressedButton(15) || ax > 0.5 ? 1 : 0) - (pressedButton(14) || ax < -0.5 ? 1 : 0);
    const y = (pressedButton(12) || ay < -0.5 ? 1 : 0) - (pressedButton(13) || ay > 0.5 ? 1 : 0);
    const pressed = held & ~this.lastHeld[index];
    this.lastHeld[index] = held;
    return { x, y, held, pressed };
  }
}

/** Keyboard and gamepad together: either one can move, buttons from both count. */
export function merge(a: RawInput, b: RawInput | null): RawInput {
  if (!b) return a;
  return { x: a.x || b.x, y: a.y || b.y, held: a.held | b.held, pressed: a.pressed | b.pressed };
}

export function allGameKeys(): Set<string> {
  const keys = new Set<string>();
  for (const map of KEYS) {
    keys.add(map.up).add(map.down).add(map.left).add(map.right);
    for (const b of BUTTONS) keys.add(map.buttons[b]);
  }
  return keys;
}
