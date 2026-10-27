/**
 * The simulation stores positions and speeds as whole numbers of 1/100 pixel, so the same inputs
 * always give exactly the same result (needed for tests, replays and, later, online play).
 */
export const SUB = 100;

/** Pixels → simulation units. */
export function px(pixels: number): number {
  return Math.round(pixels * SUB);
}
