import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '../src/characters';
import type { CompiledMove } from '../src/moves/compile';
import { NEUTRAL } from '../src/input/buttons';
import { hold, inp, inputsFor, newWorld, play } from './helpers';

const shoto = CHARACTERS.shoto;
const moves: CompiledMove[] = [
  ...Object.values(shoto.normals).filter((m): m is CompiledMove => m !== null),
  ...shoto.commandNormals.map((c) => c.move),
  ...shoto.specials.flatMap((s) => [s.L, s.M, s.H].filter((m): m is CompiledMove => m !== null)),
];

describe('startup / active / recovery', () => {
  it.each(moves.map((m) => [m.id, m] as const))('%s: hitbox only on the active frames', (id, m) => {
    const w = newWorld(250); // too far apart to hit anything
    const p1 = w.fighters[0];
    play(w, inputsFor(id));
    expect(p1.state).toBe('move');
    expect(p1.move!.id).toBe(id);
    expect(p1.moveFrame).toBe(1); // the frame the button is pressed is frame 1

    const seen: boolean[] = [];
    for (let frame = 1; frame <= m.startup + m.active + 2 && p1.state === 'move'; frame++) {
      expect(p1.moveFrame).toBe(frame);
      seen.push(w.hitboxes(p1).length > 0);
      w.step([NEUTRAL, NEUTRAL]);
    }
    for (let frame = 1; frame <= seen.length; frame++) {
      const active = frame > m.startup && frame <= m.startup + m.active;
      expect(seen[frame - 1], `frame ${frame}`).toBe(active);
    }
  });

  it('light Rising Push: 1 frame of startup, hitbox from the second frame', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    play(w, inputsFor('rising.L'));
    expect(p1.moveFrame).toBe(1);
    expect(w.hitboxes(p1)).toHaveLength(0);
    w.step([NEUTRAL, NEUTRAL]);
    expect(p1.moveFrame).toBe(2);
    expect(w.hitboxes(p1).length).toBeGreaterThan(0);
  });

  it('a grounded move can be followed on frame total + 1 and not before', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    const lp = shoto.normals['5LP']!;
    play(w, [inp(5, ['LP'])]);
    // Mash LP every frame: the buffer must not let the second one start early.
    for (let frame = 2; frame <= lp.total; frame++) {
      play(w, [inp(5, ['LP'])]);
      expect(p1.moveFrame).toBe(frame);
    }
    play(w, [inp(5, ['LP'])]);
    expect(p1.state).toBe('move');
    expect(p1.moveFrame).toBe(1);
  });

  it('a press up to 3 frames before the fighter is free is buffered', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    const lp = shoto.normals['5LP']!;
    play(w, [inp(5, ['LP'])]);
    hold(w, lp.total - 4);
    play(w, [inp(5, ['MP'])]); // pressed 3 frames before the LP ends
    hold(w, 2);
    expect(p1.move!.id).toBe('5LP');
    hold(w, 1);
    expect(p1.move!.id).toBe('5MP');
    expect(p1.moveFrame).toBe(1);
  });

  it('heavy Leopard Strike recovers much slower than light and medium', () => {
    const [l, m, h] = [shoto.specials[0].L!, shoto.specials[0].M!, shoto.specials[0].H!];
    expect(h.recovery).toBeGreaterThan(2 * Math.max(l.recovery, m.recovery));
    expect([l.active, m.active, h.active]).toEqual([1, 1, 1]);
  });
});

describe('moves that move', () => {
  it('forward + MK moves forward and forward + MP lunges forward', () => {
    for (const id of ['6MK', '6MP']) {
      const w = newWorld(250);
      const start = w.fighters[0].x;
      play(w, inputsFor(id));
      hold(w, 40);
      expect(w.fighters[0].x, id).toBeGreaterThan(start);
    }
  });

  it('Rising Push leaves the ground; medium goes higher and further than light, heavy furthest', () => {
    const results = ['rising.L', 'rising.M', 'rising.H'].map((id) => {
      const w = newWorld(250);
      const p1 = w.fighters[0];
      const startX = p1.x;
      play(w, inputsFor(id));
      let top = 0;
      for (let i = 0; i < 80 && p1.state === 'move'; i++) {
        hold(w, 1);
        top = Math.max(top, p1.y);
      }
      expect(p1.state, id).toBe('landing');
      return { top, forward: p1.x - startX };
    });
    expect(results[1].top).toBeGreaterThan(results[0].top);
    expect(results[1].forward).toBeGreaterThan(results[0].forward);
    expect(results[2].forward).toBeGreaterThan(results[1].forward * 1.5);
  });

  it('Rising Push lands, then waits out its landing recovery', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    play(w, inputsFor('rising.L'));
    until(w, () => p1.state === 'landing');
    const landed = w.frame;
    until(w, () => p1.state === 'ground');
    // Landing recovery R: touches the ground on frame L, can act again on frame L + R.
    expect(w.frame - landed).toBe(shoto.specials[1].L!.landingRecovery);
  });
});

function until(w: ReturnType<typeof newWorld>, done: () => boolean): void {
  for (let i = 0; i < 300; i++) {
    w.step([NEUTRAL, NEUTRAL]);
    if (done()) return;
  }
  throw new Error('never happened');
}
