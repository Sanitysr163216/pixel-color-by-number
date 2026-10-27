import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '../src/characters';
import { NEUTRAL } from '../src/input/buttons';
import { hold, inp, inp2, inputsFor, jumpHP, jumpLP, newWorld, play, putInAir, testCharacter } from './helpers';

const shoto = CHARACTERS.shoto;
const jumper = testCharacter({ normals: { 'j.LP': jumpLP, 'j.HP': jumpHP } });

describe('hitting an airborne opponent', () => {
  it('a light or medium normal flips them back; invulnerable and unable to act until they land', () => {
    for (const button of ['LP', 'MP'] as const) {
      const w = newWorld(50);
      const [p1, p2] = w.fighters;
      // P2 jumps on the same frame P1 presses: the hit lands while P2 is rising.
      play(w, [inp(5, [button])], [inp2(8)]);
      for (let i = 0; i < 12 && p2.state !== 'airReset'; i++) hold(w, 1);
      expect(p2.state, button).toBe('airReset');
      expect(w.hurtboxes(p2)).toHaveLength(0);

      // P2 mashes LP all the way down: nothing comes out until the frame after touching the ground.
      let landedAt = 0;
      for (let i = 0; i < 120 && p2.state === 'airReset'; i++) {
        if (p2.landed && !landedAt) landedAt = w.frame;
        expect(w.hurtboxes(p2)).toHaveLength(0);
        w.step([NEUTRAL, inp2(5, ['LP'])]);
      }
      expect(p2.state).toBe('move');
      expect(p2.moveFrame).toBe(1);
      expect(w.hurtboxes(p2).length).toBeGreaterThan(0);
      expect(w.frame).toBe(landedAt + 1);
      expect(p1.health).toBe(1000);
    }
  });

  it('a grounded heavy normal knocks them down; wakeup starts counting when they hit the ground', () => {
    const w = newWorld(50);
    const p2 = w.fighters[1];
    play(w, [inp(5, ['HP'])], [inp2(8)]);
    for (let i = 0; i < 14 && p2.state !== 'knockdown'; i++) hold(w, 1);
    expect(p2.state).toBe('knockdown');
    expect(p2.y).toBeGreaterThan(0);
    for (let i = 0; i < 100 && !p2.down; i++) hold(w, 1);
    const touched = w.frame;
    for (let i = 0; i < 100 && p2.state === 'knockdown'; i++) {
      expect(w.hurtboxes(p2)).toHaveLength(0);
      w.step([NEUTRAL, inp2(5, ['LP'])]);
    }
    // 40 frames on the ground (the frame they touch it is the first), then back up:
    // the hurtbox and the buttons return on the same frame.
    expect(w.frame - touched).toBe(40);
    expect(p2.state).toBe('move');
    expect(p2.moveFrame).toBe(1);
    expect(w.hurtboxes(p2).length).toBeGreaterThan(0);
  });

  it('a grounded special knocks them down', () => {
    const w = newWorld(30);
    const p2 = w.fighters[1];
    putInAir(p2, 30, 0);
    play(w, inputsFor('rising.L'));
    for (let i = 0; i < 10 && p2.state === 'jump'; i++) hold(w, 1);
    expect(p2.state).toBe('knockdown');
  });

  it('an air heavy against an airborne opponent flips them back (default)', () => {
    const w = newWorld(40, [jumper, jumper]);
    const [p1, p2] = w.fighters;
    putInAir(p1, 40, 2);
    putInAir(p2, 40, 2);
    play(w, [inp(5, ['HP'])]);
    for (let i = 0; i < 10 && p2.state === 'jump'; i++) hold(w, 1);
    expect(p2.state).toBe('airReset');
  });
});

describe('blocking in the air', () => {
  const setUp = (gap: number, p1Air: boolean) => {
    const w = newWorld(gap, [jumper, jumper]);
    const [p1, p2] = w.fighters;
    if (p1Air) putInAir(p1, 30, 3);
    putInAir(p2, 30, 3);
    return { w, p1, p2 };
  };

  it('grounded lights and mediums can be blocked in the air', () => {
    for (const button of ['LP', 'MP'] as const) {
      const { w, p2 } = setUp(46, false);
      play(w, [inp(5, [button])], [inp2(4)]);
      for (let i = 0; i < 10 && p2.state === 'jump'; i++) hold(w, 1, NEUTRAL, inp2(4));
      expect(p2.state, button).toBe('blockstun');
      expect(p2.airBlock).toBe(true);
    }
  });

  it('grounded heavies and specials can not be blocked in the air', () => {
    for (const id of ['5HP', 'rising.L']) {
      const { w, p2 } = setUp(id === '5HP' ? 46 : 30, false);
      play(w, inputsFor(id), [inp2(4)]);
      for (let i = 0; i < 14 && p2.state === 'jump'; i++) hold(w, 1, NEUTRAL, inp2(4));
      expect(p2.state, id).toBe('knockdown');
    }
  });

  it('air lights, mediums and heavies can all be blocked by an airborne opponent', () => {
    for (const button of ['LP', 'HP'] as const) {
      const { w, p2 } = setUp(40, true);
      play(w, [inp(5, [button])], [inp2(4)]);
      for (let i = 0; i < 10 && p2.state === 'jump'; i++) hold(w, 1, NEUTRAL, inp2(4));
      expect(p2.state, button).toBe('blockstun');
    }
  });
});

describe('blocking jumping attacks on the ground', () => {
  it('jumping attacks must be blocked standing (default)', () => {
    for (const [block, hit] of [[1, true], [4, false]] as const) {
      const w = newWorld(40, [jumper, jumper]);
      const [p1, p2] = w.fighters;
      putInAir(p1, 30, 0);
      play(w, [inp(5, ['LP'])], [inp2(block)]);
      hold(w, 6, NEUTRAL, inp2(block));
      expect(p2.health < 1000, `block ${block}`).toBe(hit);
    }
  });
});

describe('acting in the air', () => {
  it('after an air attack, no more attacks until landing', () => {
    const w = newWorld(250, [jumper, jumper]);
    const p1 = w.fighters[0];
    play(w, [inp(8)]);
    hold(w, 6);
    play(w, [inp(5, ['LP'])]);
    expect(p1.move!.id).toBe('j.LP');
    hold(w, jumpLP.startup + jumpLP.active + jumpLP.recovery);
    expect(p1.state).toBe('jump');
    expect(p1.airActionUsed).toBe(true);
    play(w, [inp(5, ['LP'])]);
    expect(p1.state).toBe('jump');
  });

  it('blocking in the air gives the air attack back', () => {
    const w = newWorld(46, [jumper, jumper]);
    const [p1, p2] = w.fighters;
    putInAir(p2, 30, 3, true); // P2 already used its air attack
    play(w, [inp(5, ['LP'])], [inp2(4)]);
    for (let i = 0; i < 10 && p2.state === 'jump'; i++) hold(w, 1, NEUTRAL, inp2(4));
    expect(p2.state).toBe('blockstun');
    for (let i = 0; i < 40 && p2.state === 'blockstun'; i++) hold(w, 1);
    expect(p2.state).toBe('jump');
    expect(p2.airActionUsed).toBe(false);
    play(w, [], [inp2(5, ['LP'])]);
    expect(p2.move!.id).toBe('j.LP');
    expect(p1.health).toBe(1000);
  });

  it('the real Shoto has no jumping attacks yet: the buttons do nothing in the air', () => {
    const w = newWorld(250, [shoto, shoto]);
    const p1 = w.fighters[0];
    play(w, [inp(8)]);
    hold(w, 8);
    play(w, [inp(5, ['HK'])]);
    expect(p1.state).toBe('jump');
    expect(p1.lastCommand).toBe('j.HK: EMPTY SLOT');
  });
});
