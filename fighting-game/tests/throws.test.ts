import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '../src/characters';
import { RULES } from '../src/config';
import { hold, inp, inp2, newWorld, play, putInAir, until } from './helpers';

const shoto = CHARACTERS.shoto;
const shoulderThrow = shoto.throw!.move;

describe('throw', () => {
  it.each(['MP', 'HP'] as const)('close forward + %s throws: never airborne, slammed down behind the thrower', (button) => {
    const w = newWorld(40);
    const [p1, p2] = w.fighters;
    play(w, [inp(6, [button])]);
    expect(p1.move?.id).toBe('throw');
    expect(p2.state).toBe('thrown');
    let slammedOn = 0;
    for (let i = 0; i < 30; i++) {
      hold(w, 1);
      expect(p2.y).toBe(0); // never in the air
      if (!slammedOn && p2.state === 'knockdown') slammedOn = p1.moveFrame;
    }
    expect(slammedOn).toBe(shoulderThrow.throw!.slamFrame);
    expect(p2.down).toBe(true);
    expect(p2.health).toBe(1000 - shoulderThrow.damage);
    expect(p2.x).toBeLessThan(p1.x); // landed behind P1: the sides switched
  });

  it.each([0, 1] as const)('the wakeup count starts on the slam (player %i throws)', (thrower) => {
    const w = newWorld(40);
    const t = w.fighters[thrower];
    const o = w.fighters[1 - thrower];
    const press = thrower === 0 ? inp(6, ['HP']) : inp2(6, ['HP']);
    play(w, thrower === 0 ? [press] : [], thrower === 0 ? [] : [press]);
    expect(o.state).toBe('thrown');
    until(w, () => o.state === 'knockdown');
    expect(t.moveFrame).toBe(shoulderThrow.throw!.slamFrame);
    const slam = w.frame;
    until(w, () => o.state === 'ground');
    expect(w.frame - slam).toBe(RULES.knockdown.wakeup);
  });

  it('out of range, forward + MP does the Lunging Palm and forward + HP its normal (not made yet)', () => {
    const w = newWorld(70);
    play(w, [inp(6, ['MP'])]);
    expect(w.fighters[0].move?.id).toBe('6MP');
    const w2 = newWorld(70);
    play(w2, [inp(6, ['HP'])]);
    expect(w2.fighters[0].state).toBe('ground');
    expect(w2.fighters[0].lastCommand).toBe('5HP: EMPTY SLOT');
  });

  it('can not be blocked', () => {
    const w = newWorld(40);
    play(w, [inp(6, ['HP'])], [inp2(4)]);
    expect(w.fighters[1].state).toBe('thrown');
  });

  it('only works on a grounded opponent who is not in blockstun or hit stun', () => {
    const air = newWorld(40);
    putInAir(air.fighters[1], 20, 0);
    play(air, [inp(6, ['MP'])]);
    expect(air.fighters[0].move?.id).toBe('6MP');

    for (const state of ['blockstun', 'hitstun'] as const) {
      const w = newWorld(40);
      w.fighters[1].state = state;
      w.fighters[1].stun = 10;
      play(w, [inp(6, ['MP'])]);
      expect(w.fighters[0].move?.id, state).toBe('6MP');
    }
  });

  it('both fighters are invulnerable during the throw', () => {
    const w = newWorld(40);
    play(w, [inp(6, ['MP'])]);
    hold(w, 5);
    expect(w.hurtboxes(w.fighters[0])).toHaveLength(0);
    expect(w.hurtboxes(w.fighters[1])).toHaveLength(0);
  });
});
