import { describe, expect, it } from 'vitest';
import { InputHistory } from '../src/input/history';
import { motionDone } from '../src/input/motions';
import { NEUTRAL } from '../src/input/buttons';
import { hold, inp, inp2, inputsFor, leopardCE, newWorld, play, testCharacter } from './helpers';


function history(dirs: number[]): InputHistory {
  const h = new InputHistory();
  for (const d of dirs) h.push(inp(d));
  return h;
}

describe('motion inputs', () => {
  it('finds 4-2-1-6, also when the stick rolls through other directions', () => {
    expect(motionDone(history([4, 2, 1, 6]), [4, 2, 1, 6], 20, 1)).toBe(true);
    expect(motionDone(history([4, 1, 2, 1, 2, 3, 6]), [4, 2, 1, 6], 20, 1)).toBe(true);
    expect(motionDone(history([4, 5, 2, 1, 5, 6]), [4, 2, 1, 6], 20, 1)).toBe(true);
  });

  it('does not take a half circle forward or a dragon punch for 4-2-1-6', () => {
    expect(motionDone(history([4, 1, 2, 3, 6]), [4, 2, 1, 6], 20, 1)).toBe(false);
    expect(motionDone(history([6, 2, 3]), [4, 2, 1, 6], 20, 1)).toBe(false);
  });

  it('finds 6-2-3, including 6-3-2-3', () => {
    expect(motionDone(history([6, 2, 3]), [6, 2, 3], 15, 1)).toBe(true);
    expect(motionDone(history([6, 3, 2, 3]), [6, 2, 3], 15, 1)).toBe(true);
    expect(motionDone(history([2, 3]), [6, 2, 3], 15, 1)).toBe(false);
  });

  it('the motion has to fit in its window', () => {
    const slow = [4, ...Array(20).fill(5), 2, 1, 6];
    expect(motionDone(history(slow), [4, 2, 1, 6], 20, 1)).toBe(false);
  });

  it('is read relative to the way the fighter faces', () => {
    const h = new InputHistory();
    for (const d of [4, 2, 1, 6]) h.push(inp(d, [], -1));
    expect(motionDone(h, [4, 2, 1, 6], 20, -1)).toBe(true);
    expect(motionDone(h, [4, 2, 1, 6], 20, 1)).toBe(false);
  });
});

describe('special moves in the game', () => {
  it.each([
    ['leopard.L', 'LP'],
    ['leopard.M', 'MP'],
    ['leopard.H', 'HP'],
    ['rising.L', 'LK'],
    ['rising.M', 'MK'],
    ['rising.H', 'HK'],
  ])('%s comes out', (id) => {
    const w = newWorld(250);
    play(w, inputsFor(id));
    expect(w.fighters[0].move?.id).toBe(id);
  });

  it('works for P2, facing left', () => {
    const w = newWorld(250);
    play(w, [], inputsFor('leopard.M', -1));
    expect(w.fighters[1].move?.id).toBe('leopard.M');
  });

  it('a special beats the command normal that ends its motion (…6 + MP)', () => {
    const w = newWorld(250);
    play(w, inputsFor('leopard.M'));
    expect(w.fighters[0].move?.id).toBe('leopard.M');
    const w2 = newWorld(250);
    play(w2, [inp(6, ['MP'])]);
    expect(w2.fighters[0].move?.id).toBe('6MP');
  });

  it('getting hit during Leopard Strike startup does double damage', () => {
    const w = newWorld(50);
    const [p1, p2] = w.fighters;
    play(w, [inp(4), inp(2), inp(1)]);
    play(w, [inp(6, ['LP'])], [inp2(5, ['LP'])]); // P1's Leopard (7 startup) vs P2's LP (4 startup)
    hold(w, 4);
    expect(p1.health).toBe(1000 - 2 * 30);
    expect(p2.health).toBe(1000);
  });

  it('heavy Leopard Strike knocks down and the opponent stays down twice as long', () => {
    const w = newWorld(56);
    const p2 = w.fighters[1];
    play(w, inputsFor('leopard.H'));
    for (let i = 0; i < 20 && p2.state !== 'knockdown'; i++) hold(w, 1);
    expect(p2.state).toBe('knockdown');
    expect(p2.health).toBe(860);
    for (let i = 0; i < 100 && !p2.down; i++) hold(w, 1);
    const touched = w.frame;
    for (let i = 0; i < 200 && p2.state === 'knockdown'; i++) hold(w, 1);
    expect(w.frame - touched).toBe(80);
  });

  it('light and medium Leopard Strike do not knock down', () => {
    for (const id of ['leopard.L', 'leopard.M']) {
      const w = newWorld(56);
      const p2 = w.fighters[1];
      play(w, inputsFor(id));
      hold(w, 12);
      expect(p2.state, id).toBe('hitstun');
    }
  });
});

describe('empty moves and Chakra Enhance', () => {
  it('buttons with no move do nothing, and the fighter keeps walking or crouching', () => {
    for (const [dir, button, slot] of [[5, 'LK', '5LK'], [6, 'HP', '5HP'], [2, 'LP', '2LP'], [3, 'MK', '2MK']] as const) {
      const w = newWorld(250);
      const p1 = w.fighters[0];
      play(w, [inp(dir, [button])]);
      expect(p1.state, slot).toBe('ground');
      expect(p1.lastCommand).toBe(`${slot}: EMPTY SLOT`);
      expect(p1.crouching).toBe(dir <= 3);
    }
  });

  it('while the CE move is not made, two punches do the normal special (heaviest button) and spend nothing', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    p1.meter = 500;
    play(w, [inp(4), inp(2), inp(1), inp(6, ['LP', 'MP'])]);
    expect(p1.move?.id).toBe('leopard.M');
    expect(p1.meter).toBe(500);
    expect(p1.lastCommand).toBe('LEOPARD STRIKE M (CE NOT MADE YET)');
  });

  it('with a CE move: two punches start it and spend one bar', () => {
    const withCE = testCharacter({ leopardCE });
    const w = newWorld(250, [withCE, withCE]);
    const p1 = w.fighters[0];
    p1.meter = 250;
    play(w, [inp(4), inp(2), inp(1), inp(6, ['LP', 'HP'])]);
    expect(p1.move?.id).toBe('leopard.CE');
    expect(p1.meter).toBe(150);
  });

  it('with a CE move: the two punches must be pressed on exactly the same frame', () => {
    const withCE = testCharacter({ leopardCE });
    const w = newWorld(250, [withCE, withCE]);
    const p1 = w.fighters[0];
    p1.meter = 100;
    play(w, [inp(4), inp(2), inp(1), inp(6, ['LP'])]);
    expect(p1.move?.id).toBe('leopard.L');
    play(w, [inp(6, ['MP'])]); // one frame late
    expect(p1.move?.id).toBe('leopard.L');
    expect(p1.meter).toBe(100);
  });

  it('with a CE move but less than a bar: the normal version of the heaviest button', () => {
    const withCE = testCharacter({ leopardCE });
    const w = newWorld(250, [withCE, withCE]);
    const p1 = w.fighters[0];
    p1.meter = 99;
    play(w, [inp(4), inp(2), inp(1), inp(6, ['LP', 'MP'])]);
    expect(p1.move?.id).toBe('leopard.M');
    expect(p1.meter).toBe(99);
  });

  it('two buttons too far apart are not a CE', () => {
    const withCE = testCharacter({ leopardCE });
    const w = newWorld(250, [withCE, withCE]);
    const p1 = w.fighters[0];
    p1.meter = 100;
    play(w, [inp(4), inp(2), inp(1), inp(6, ['LP']), NEUTRAL, inp(6, ['MP'])]);
    expect(p1.move?.id).toBe('leopard.L');
    expect(p1.meter).toBe(100);
  });
});
