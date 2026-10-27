import { describe, expect, it } from 'vitest';
import { compileMove } from '../src/moves/compile';
import type { MoveData } from '../src/moves/types';
import { BUTTONS, BTN, type RawInput } from '../src/input/buttons';
import { newWorld } from './helpers';

const base: MoveData = {
  name: 'Test',
  kind: 'normal',
  strength: 'L',
  startup: 3,
  active: 2,
  recovery: 5,
  damage: 10,
  hitstun: 10,
  blockstun: 5,
  hitboxes: [{ boxes: [{ x: 10, y: 50, w: 20, h: 10 }] }],
};

describe('move data checks', () => {
  it('fills in defaults by strength', () => {
    const m = compileMove('t', base);
    expect(m.total).toBe(10);
    expect(m.hitstop).toBeNull(); // comes from the character's hitstop table
    expect(m.meterOnHit).toBe(3);
    expect(m.hitPhases[0]).toMatchObject({ from: 4, to: 5 });
  });

  it('says clearly which move has a mistake', () => {
    expect(() => compileMove('5LP', { ...base, startup: -1 })).toThrow('Move 5LP (Test): startup must be a whole number');
    expect(() => compileMove('5LP', { ...base, hitboxes: [{ frames: [1, 3], boxes: base.hitboxes[0].boxes }] })).toThrow(
      'go past the 2 active frame(s)',
    );
    expect(() => compileMove('5LP', { ...base, active: 0 })).toThrow('active must be a whole number of at least 1');
  });
});

/** Small deterministic random numbers, so the test is the same every run. */
function random(seed: number) {
  return () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
}

function randomInputs(n: number, seed: number): RawInput[] {
  const r = random(seed);
  let held = 0;
  return Array.from({ length: n }, () => {
    const next = r() < 0.15 ? BTN[BUTTONS[Math.floor(r() * 6)]] : 0;
    const pressed = next & ~held;
    held = next;
    return { x: Math.floor(r() * 3) - 1, y: r() < 0.1 ? 1 : r() < 0.3 ? -1 : 0, held, pressed };
  });
}

function snapshot(w: ReturnType<typeof newWorld>) {
  return JSON.stringify(
    w.fighters.map((f) => [f.x, f.y, f.vx, f.vy, f.state, f.frame, f.health, f.meter, f.move?.id, f.moveFrame, f.stun, f.hitstop]),
  );
}

describe('determinism', () => {
  it('the same inputs give exactly the same fight', () => {
    const p1 = randomInputs(3000, 1);
    const p2 = randomInputs(3000, 2);
    const runs = [newWorld(80), newWorld(80)].map((w) => {
      w.koEnabled = false;
      const frames: string[] = [];
      for (let i = 0; i < p1.length; i++) {
        w.step([p1[i], p2[i]]);
        frames.push(snapshot(w));
      }
      return frames;
    });
    expect(runs[0]).toEqual(runs[1]);
    // The random fight should actually have contained some hits.
    expect(runs[0].at(-1)).not.toEqual(runs[0][0]);
  });
});
