import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '../src/characters';
import { px } from '../src/core/units';
import { NEUTRAL } from '../src/input/buttons';
import { hold, inp, inp2, newWorld, play, putInAir, until } from './helpers';

const shoto = CHARACTERS.shoto;

describe('crouching normals', () => {
  it('crouching LP punches twice', () => {
    const w = newWorld(36);
    play(w, [inp(2, ['LP'])]);
    hold(w, 30, inp(2));
    expect(w.fighters[1].combo.hits).toBe(2);
    expect(w.fighters[1].health).toBe(1000 - 2 * shoto.normals['2LP']!.damage);
  });

  it('crouching LK and MK are lows: a standing block fails, a crouching block works', () => {
    for (const id of ['2LK', '2MK'] as const) {
      for (const [block, hit] of [[4, true], [1, false]] as const) {
        const w = newWorld(34);
        play(w, [inp(2, [id.slice(1) as 'LK' | 'MK'])], [inp2(block)]);
        hold(w, 25, inp(2), inp2(block));
        expect(w.fighters[1].health < 1000, `${id} vs ${block}`).toBe(hit);
      }
    }
  });

  it('crouching MP reaches further than crouching LP', () => {
    for (const [button, hits] of [['LP', false], ['MP', true]] as const) {
      const w = newWorld(70);
      play(w, [inp(2, [button])]);
      hold(w, 20, inp(2));
      expect(w.fighters[1].health < 1000, button).toBe(hits);
    }
  });

  it('crouching MK pushes the character forward during its recovery', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    const m = shoto.normals['2MK']!;
    play(w, [inp(2, ['MK'])]);
    hold(w, m.startup + m.active - 1, inp(2));
    const before = p1.x;
    hold(w, m.recovery, inp(2));
    expect(p1.x).toBeGreaterThan(before + px(10));
  });
});

describe('jumping MK', () => {
  it('crosses up: from just behind, it has to be blocked the other way', () => {
    // P1 came from the left and is now just past P2's centre. Holding right (back from where P1 started)
    // doesn't block; holding left (away from where P1 is now) does. P2 stands still until the kick arrives.
    for (const [x, blocked] of [[1, false], [-1, true]] as const) {
      const w = newWorld(60);
      const [p1, p2] = w.fighters;
      putInAir(p1, 76, 0);
      p1.x = p2.x + px(6);
      const block = { x, y: 0, held: 0, pressed: 0 };
      play(w, [inp(5, ['MK']), NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL], [NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, block]);
      expect(p1.move?.id).toBe('j.MK');
      expect(w.events.map((e) => e.type), x === 1 ? 'held right' : 'held left').toEqual([blocked ? 'block' : 'hit']);
    }
  });
});

describe('Spiritual Tunneling', () => {
  const hcfTwoPunches = [inp(4), inp(1), inp(2), inp(3), inp(6, ['LP', 'MP'])];

  it('half circle forward + two punches, 1 bar: dashes in and knocks down', () => {
    const w = newWorld(120);
    const [p1, p2] = w.fighters;
    p1.meter = 100;
    play(w, hcfTwoPunches);
    expect(p1.move?.id).toBe('tunneling');
    expect(p1.meter).toBe(0);
    until(w, () => p2.state === 'knockdown');
    expect(p2.health).toBe(1000 - shoto.chakraSpecials[0].move.damage);
  });

  it('is invincible until its first recovery frame', () => {
    const w = newWorld(60);
    const [p1, p2] = w.fighters;
    p1.meter = 100;
    play(w, hcfTwoPunches, [NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, inp2(5, ['LP'])]);
    hold(w, 10);
    expect(p1.health).toBe(1000);
    expect(p2.health).toBeLessThan(1000);
  });

  it('without a bar, the same input throws a Soul Flake (the lighter button)', () => {
    const w = newWorld(250);
    play(w, hcfTwoPunches);
    expect(w.fighters[0].move?.id).toBe('flake.L');
  });
});
