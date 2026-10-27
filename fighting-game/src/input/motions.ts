import { numpad } from './buttons';
import type { InputHistory } from './history';

/**
 * True if the directions of a motion (numpad, relative to `facing`) appear in order in the history,
 * finishing on or before frame `age`, with the first one at most `window` frames before it.
 *
 * Other directions may come between the steps: a stick rolled from 1 to 6 passes through 2 and 3,
 * so 4-2-1-6 also matches 4,1,2,1,2,3,6.
 */
export function motionDone(
  history: InputHistory,
  steps: readonly number[],
  window: number,
  facing: number,
  age = 0,
): boolean {
  let step = steps.length - 1;
  for (let a = age; a < history.length && a - age <= window; a++) {
    const frame = history.get(a)!;
    if (numpad(frame.x, frame.y, facing) === steps[step]) {
      step--;
      if (step < 0) return true;
    }
  }
  return false;
}
