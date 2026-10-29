export const BUTTONS = ['LP', 'MP', 'HP', 'LK', 'MK', 'HK'] as const;
export type ButtonName = (typeof BUTTONS)[number];

/** One bit per button, so several buttons fit in one number. */
export const BTN: Record<ButtonName, number> = { LP: 1, MP: 2, HP: 4, LK: 8, MK: 16, HK: 32 };
export const PUNCHES = BTN.LP | BTN.MP | BTN.HP;
export const KICKS = BTN.LK | BTN.MK | BTN.HK;

export type Strength = 'L' | 'M' | 'H';
export const STRENGTH_OF: Record<ButtonName, Strength> = { LP: 'L', MP: 'M', HP: 'H', LK: 'L', MK: 'M', HK: 'H' };

/**
 * Lightest first: when several buttons are pressed on the same frame and no move uses that combination,
 * the lightest one comes out (a punch before a kick of the same strength).
 */
export const LIGHTEST_FIRST: readonly ButtonName[] = ['LP', 'LK', 'MP', 'MK', 'HP', 'HK'];

/**
 * One player's controller on one frame.
 * x: -1 left, 0, 1 right (screen directions). y: -1 down, 0, 1 up.
 * held: buttons down right now. pressed: buttons that went down since the previous frame.
 */
export interface RawInput {
  x: number;
  y: number;
  held: number;
  pressed: number;
}

export const NEUTRAL: RawInput = Object.freeze({ x: 0, y: 0, held: 0, pressed: 0 });

/** Numpad notation (1–9) as seen by a fighter facing right (1) or left (-1): 6 is forward, 4 is back, 2 is down. */
export function numpad(x: number, y: number, facing: number): number {
  return 5 + x * facing + 3 * y;
}

export function buttonsIn(mask: number): ButtonName[] {
  return BUTTONS.filter((b) => mask & BTN[b]);
}

export function countButtons(mask: number): number {
  let n = 0;
  for (let m = mask; m; m &= m - 1) n++;
  return n;
}
