import { describe, expect, it } from 'vitest';
import { NEUTRAL } from '../src/input/buttons';
import { METER_MAX } from '../src/sim/world';
import { hold, inp2, inputsFor, newWorld, play } from './helpers';

function meterAfter(id: string, gap: number, p2Block = false) {
  const w = newWorld(gap);
  play(w, inputsFor(id), p2Block ? [inp2(4)] : []);
  hold(w, 40, NEUTRAL, p2Block ? inp2(4) : NEUTRAL);
  return { attacker: w.fighters[0].meter, defender: w.fighters[1].meter, hit: w.fighters[1].health < 1000 };
}

describe('meter', () => {
  it('a hit gives the attacker 3 × 1 / 2 / 3 for light / medium / heavy', () => {
    expect(meterAfter('5LP', 50)).toEqual({ attacker: 3, defender: 0, hit: true });
    expect(meterAfter('5MP', 50)).toEqual({ attacker: 6, defender: 0, hit: true });
    expect(meterAfter('5HP', 50)).toEqual({ attacker: 9, defender: 0, hit: true });
    expect(meterAfter('leopard.L', 56)).toEqual({ attacker: 3, defender: 0, hit: true });
    expect(meterAfter('leopard.H', 56)).toEqual({ attacker: 9, defender: 0, hit: true });
  });

  it('a blocked hit gives the defender 2 and the attacker nothing', () => {
    // Closer than the hit tests: holding back walks backward until the attack arrives.
    expect(meterAfter('5HP', 40, true)).toEqual({ attacker: 0, defender: 2, hit: false });
    expect(meterAfter('leopard.M', 44, true)).toEqual({ attacker: 0, defender: 2, hit: false });
  });

  it('stops at 10 bars of 100 points', () => {
    expect(METER_MAX).toBe(1000);
    const w = newWorld(50);
    w.fighters[0].meter = 999;
    play(w, inputsFor('5HP'));
    hold(w, 20);
    expect(w.fighters[0].meter).toBe(1000);
  });
});
