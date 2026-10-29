import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '../src/characters';
import { standLP, standMP } from '../src/characters/shoto/moves';
import { px } from '../src/core/units';
import { Game } from '../src/game/game';
import { NEUTRAL } from '../src/input/buttons';
import type { MoveData } from '../src/moves/types';
import { isStunned } from '../src/sim/fighter';
import type { World } from '../src/sim/world';
import { hold, inp, inp2, inputsFor, jumpLP, newWorld, play, putInAir, testCharacter, until } from './helpers';

const shoto = CHARACTERS.shoto;
const jumper = testCharacter({ normals: { 'j.LP': jumpLP, 'j.HP': { ...jumpLP, name: 'Jumping HP', strength: 'H' } } });

describe('Character 1 after the answers', () => {
  it('the donkey kick is standing HK; standing HP has no move yet', () => {
    expect(shoto.normals['5HK']?.name).toBe('Donkey Kick');
    expect(shoto.normals['5HP']).toBeNull();
  });

  it('forward + MP hits far: it reaches where standing MP does not', () => {
    for (const [id, hits] of [['5MP', false], ['6MP', true]] as const) {
      const w = newWorld(84);
      play(w, inputsFor(id));
      hold(w, 20);
      expect(w.fighters[1].health < 1000, id).toBe(hits);
    }
  });
});

describe('hitstop', () => {
  it('moves done from the ground: 7 / 9 / 11 frames by strength', () => {
    for (const [id, stop] of [['5LP', 7], ['5MP', 9], ['5HK', 11]] as const) {
      const w = newWorld(46);
      play(w, inputsFor(id));
      until(w, () => w.fighters[1].health < 1000);
      expect(w.fighters[0].hitstop, id).toBe(stop);
      expect(w.fighters[1].hitstop, id).toBe(stop);
    }
  });

  it('air to ground: 7 frames for every move, even a heavy', () => {
    const w = newWorld(40, [jumper, jumper]);
    putInAir(w.fighters[0], 30, 0);
    play(w, [inp(5, ['HP'])]);
    until(w, () => w.fighters[1].health < 1000);
    expect(w.fighters[0].hitstop).toBe(7);
  });

  it('air to air: 3 frames on hit, 7 on block', () => {
    for (const [p2Input, stop] of [[NEUTRAL, 3], [inp2(4), 7]] as const) {
      const w = newWorld(40, [jumper, jumper]);
      putInAir(w.fighters[0], 40, 2);
      putInAir(w.fighters[1], 40, 2);
      play(w, [inp(5, ['HP'])], [p2Input]);
      until(w, () => w.fighters[0].hitstop > 0, NEUTRAL, p2Input);
      expect(w.fighters[0].hitstop).toBe(stop);
    }
  });

  it('is set per character', () => {
    const slow = testCharacter({ normals: { 'j.HP': jumpLP }, hitstop: { airToGround: 5 } });
    const w = newWorld(40, [slow, slow]);
    putInAir(w.fighters[0], 30, 0);
    play(w, [inp(5, ['HP'])]);
    until(w, () => w.fighters[1].health < 1000);
    expect(w.fighters[0].hitstop).toBe(5);
  });
});

describe('proximity guard', () => {
  it('holding back stops walking 2 frames before the attack is active, if it would reach', () => {
    const w = newWorld(46);
    const [p1, p2] = w.fighters;
    const hk = shoto.normals['5HK']!;
    w.step([inp(5, ['HK']), inp2(4)]);
    for (let frame = 2; frame <= hk.startup; frame++) {
      const before = p2.x;
      w.step([NEUTRAL, inp2(4)]);
      expect(p1.moveFrame).toBe(frame);
      const guarding = frame >= hk.startup - 1;
      expect(p2.guarding, `frame ${frame}`).toBe(guarding);
      expect(p2.x === before, `frame ${frame}`).toBe(guarding);
    }
    w.step([NEUTRAL, inp2(4)]);
    expect(p2.state).toBe('blockstun');
  });

  it('does nothing when the attack would not reach', () => {
    const w = newWorld(120);
    const p2 = w.fighters[1];
    play(w, [inp(5, ['HK'])], [inp2(4)]);
    for (let i = 0; i < 12; i++) {
      w.step([NEUTRAL, inp2(4)]);
      expect(p2.guarding).toBe(false);
    }
  });
});

describe('blockstrings', () => {
  // Two hits: a mid, then a low 6 frames later; no knockback so both reach.
  const twoHit: MoveData = {
    name: 'Two Hit',
    kind: 'normal',
    strength: 'L',
    startup: 3,
    active: 8,
    recovery: 10,
    damage: 20,
    hitstun: 14,
    blockstun: 14,
    knockback: { distance: 0, speed: 1 },
    hitboxes: [
      { frames: [1, 2], boxes: [{ x: 10, y: 40, w: 30, h: 20 }], hit: 0 },
      { frames: [7, 8], boxes: [{ x: 10, y: 0, w: 30, h: 14 }], hit: 1 },
    ],
  };
  const tester = testCharacter({ normals: { '5LK': twoHit } });

  it('once blocking, every hit of the string is blocked, even after letting go of back (and even a low)', () => {
    const w = newWorld(40, [tester, tester]);
    const p2 = w.fighters[1];
    play(w, [inp(5, ['LK']), NEUTRAL, NEUTRAL, NEUTRAL], [inp2(4), inp2(4), inp2(4), inp2(4)]);
    expect(p2.state).toBe('blockstun');
    hold(w, 25); // back released, standing
    expect(p2.health).toBe(1000);
    expect(p2.meter).toBe(2 * 2);
  });

  it('without blocking the first hit, both hit', () => {
    const w = newWorld(40, [tester, tester]);
    play(w, [inp(5, ['LK'])]);
    hold(w, 25);
    expect(w.fighters[1].health).toBe(960);
    expect(w.fighters[1].combo.hits).toBe(2);
  });
});

describe('dash and back hop', () => {
  it('double-tap forward dashes for as long as forward is held, and stops the moment it is let go', () => {
    const w = newWorld(200);
    const p1 = w.fighters[0];
    play(w, [inp(6), inp(5), inp(6)]);
    expect(p1.state).toBe('dash');
    const start = p1.x;
    hold(w, 10, inp(6));
    expect(p1.state).toBe('dash');
    expect((p1.x - start) / px(1)).toBe(10 * shoto.data.dash.speed);
    hold(w, 1);
    expect(p1.state).toBe('ground');
    const stopped = p1.x;
    hold(w, 5);
    expect(p1.x).toBe(stopped);
  });

  it('no moves mid-dash, and a press during the dash does not come out after it', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    play(w, [inp(6), inp(5), inp(6), inp(6, ['LP']), inp(6)]);
    expect(p1.state).toBe('dash');
    play(w, [NEUTRAL, NEUTRAL]);
    expect(p1.state).toBe('ground');
  });

  it('holding forward walks; tapping too slowly walks too', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    hold(w, 10, inp(6));
    expect(p1.state).toBe('ground');
    play(w, [inp(6), ...Array(13).fill(NEUTRAL), inp(6)]);
    expect(p1.state).toBe('ground');
    expect(p1.walk).toBe(1);
  });

  it('double-tap back hops backwards through the air', () => {
    const w = newWorld(120);
    const p1 = w.fighters[0];
    const start = p1.x;
    play(w, [inp(4), inp(5), inp(4)]);
    expect(p1.state).toBe('jump');
    expect(p1.hop).toBe(true);
    expect(p1.y).toBeGreaterThan(0);
    until(w, () => p1.state === 'ground');
    expect(start - p1.x).toBeGreaterThan(px(50));
  });

  it('air normals can be used during the back hop, until it lands', () => {
    const w = newWorld(120, [jumper, jumper]);
    const p1 = w.fighters[0];
    play(w, [inp(4), inp(5), inp(4)]);
    hold(w, 3);
    play(w, [inp(5, ['LP'])]);
    expect(p1.move?.id).toBe('j.LP');
  });
});

describe('chains', () => {
  /** Steps until P2 has taken `hits` hits in the combo, then presses `button` (during hitstop). */
  const pressAfterHit = (w: World, hits: number, dir: number, button: 'LP' | 'MP') => {
    until(w, () => w.fighters[1].combo.hits === hits);
    play(w, [inp(dir, [button])]);
  };

  it('a normal chains into a different normal pressed during hitstop', () => {
    const w = newWorld(40);
    const [p1, p2] = w.fighters;
    play(w, [inp(5, ['LP'])]);
    pressAfterHit(w, 1, 5, 'MP');
    until(w, () => p1.move?.id === '5MP');
    expect(p1.chained).toBe(true);
    until(w, () => p2.combo.hits === 2);
    expect(p2.health).toBe(1000 - 30 - 60);
  });

  it('chains into command normals too', () => {
    const w = newWorld(40);
    play(w, [inp(5, ['LP'])]);
    pressAfterHit(w, 1, 6, 'MP');
    until(w, () => w.fighters[0].move?.id === '6MP');
  });

  it('a normal can not chain into itself', () => {
    const w = newWorld(40);
    const p1 = w.fighters[0];
    play(w, [inp(5, ['LP'])]);
    pressAfterHit(w, 1, 5, 'LP');
    hold(w, 8);
    expect(p1.chained).toBe(false);
    expect(p1.lastCommand).toBe("5LP: CAN'T CHAIN INTO ITSELF");
  });

  it('chains work on block too', () => {
    const w = newWorld(40);
    const [p1, p2] = w.fighters;
    play(w, [inp(5, ['LP'])], [inp2(4)]);
    until(w, () => p2.state === 'blockstun', NEUTRAL, inp2(4));
    play(w, [inp(5, ['MP'])]);
    until(w, () => p1.move?.id === '5MP');
    expect(p1.chained).toBe(true);
  });

  it('the second normal must be pressed during the hitstop (or 1 frame before the hit, as a buffer)', () => {
    // 5LP connects on frame 5 and freezes both for 7 frames (6 to 12); the attacker moves again on frame 13.
    const cases: [string, number, boolean][] = [
      ['last frame of hitstop', 12, true],
      ['first frame after hitstop', 13, false],
      ['1 frame before the hit', 4, true],
      ['2 frames before the hit', 3, false],
    ];
    for (const [label, pressFrame, chains] of cases) {
      const w = newWorld(40);
      const p1 = w.fighters[0];
      const inputs = Array.from({ length: 16 }, (_, i) => (i === 0 ? inp(5, ['LP']) : i + 1 === pressFrame ? inp(5, ['MP']) : NEUTRAL));
      play(w, inputs);
      expect(w.fighters[1].combo.hits, label).toBeGreaterThan(0);
      expect(p1.move?.id === '5MP' && p1.chained, label).toBe(chains);
    }
  });

  it('a blockstring can not use the same chain twice either', () => {
    const still = { knockback: { distance: 0, speed: 1 } };
    const tester = testCharacter({ normals: { '5LP': { ...standLP, ...still }, '5MP': { ...standMP, ...still } } });
    const w = newWorld(40, [tester, tester]);
    const [p1, p2] = w.fighters;
    const pressAfterBlock = (blocks: number, button: 'LP' | 'MP') => {
      until(w, () => p2.meter === 2 * blocks, NEUTRAL, inp2(4));
      play(w, [inp(5, [button])], [inp2(4)]);
    };
    play(w, [inp(5, ['LP'])], [inp2(4)]);
    pressAfterBlock(1, 'MP');
    pressAfterBlock(2, 'LP');
    pressAfterBlock(3, 'MP');
    hold(w, 10, NEUTRAL, inp2(4));
    expect(p2.health).toBe(1000);
    expect(p1.lastCommand).toBe('5LP > 5MP: CHAIN ALREADY USED');
  });

  it('a combo can not use the same chain twice; the next combo can', () => {
    const still = { knockback: { distance: 0, speed: 1 } };
    const tester = testCharacter({ normals: { '5LP': { ...standLP, ...still }, '5MP': { ...standMP, ...still } } });
    const w = newWorld(40, [tester, tester]);
    const [p1, p2] = w.fighters;
    play(w, [inp(5, ['LP'])]);
    pressAfterHit(w, 1, 5, 'MP'); // 5LP > 5MP
    pressAfterHit(w, 2, 5, 'LP'); // 5MP > 5LP
    pressAfterHit(w, 3, 5, 'MP'); // 5LP > 5MP again: refused
    hold(w, 10);
    expect(p1.lastCommand).toBe('5LP > 5MP: CHAIN ALREADY USED');
    expect(p1.lastMove?.id).toBe('5LP');

    until(w, () => p2.state === 'ground' && p1.state === 'ground');
    play(w, [inp(5, ['LP'])]);
    pressAfterHit(w, 1, 5, 'MP');
    until(w, () => p1.move?.id === '5MP');
  });
});

describe('special cancels', () => {
  const leopard = (w: World, p2: ReturnType<typeof inp2>) =>
    play(w, [inp(4), inp(2), inp(1), inp(6, ['LP'])], [p2, p2, p2, p2]);

  it('only from the hit until the normal\'s active frames end', () => {
    // 5LP: hit on frame 5 (its first active frame), hitstop on frames 6–12, its last active frame is played
    // on frame 13, recovery starts on frame 14.
    for (const [pressFrame, cancels] of [[13, true], [14, false]] as const) {
      const w = newWorld(40);
      const p1 = w.fighters[0];
      const inputs = Array.from({ length: pressFrame }, () => NEUTRAL);
      inputs[0] = inp(5, ['LP']);
      inputs[pressFrame - 4] = inp(4);
      inputs[pressFrame - 3] = inp(2);
      inputs[pressFrame - 2] = inp(1);
      inputs[pressFrame - 1] = inp(6, ['LP']);
      play(w, inputs);
      expect(p1.move?.id === 'leopard.L', `pressed on frame ${pressFrame}`).toBe(cancels);
    }
  });

  it('a special pressed up to 3 frames before the normal connects still cancels it', () => {
    // 5HK connects on frame 10.
    for (const [pressFrame, cancels] of [[7, true], [6, false]] as const) {
      const w = newWorld(46);
      const p1 = w.fighters[0];
      const inputs = Array.from({ length: pressFrame }, () => NEUTRAL);
      inputs[0] = inp(5, ['HK']);
      inputs[pressFrame - 4] = inp(4);
      inputs[pressFrame - 3] = inp(2);
      inputs[pressFrame - 2] = inp(1);
      inputs[pressFrame - 1] = inp(6, ['LP']);
      play(w, inputs);
      let cancelled = false;
      for (let i = 0; i < 30; i++) {
        hold(w, 1);
        if (p1.move?.id === 'leopard.L') cancelled = true;
      }
      expect(w.fighters[1].health).toBeLessThan(1000);
      expect(cancelled, `pressed on frame ${pressFrame}`).toBe(cancels);
    }
  });

  it('a normal cancels into a special on hit and on block', () => {
    for (const block of [false, true]) {
      const w = newWorld(40);
      const [p1, p2] = w.fighters;
      const p2Input = block ? inp2(4) : NEUTRAL;
      play(w, [inp(5, ['LP'])], [p2Input]);
      until(w, () => p2.state === (block ? 'blockstun' : 'hitstun'), NEUTRAL, p2Input);
      leopard(w, p2Input);
      until(w, () => p1.move?.id === 'leopard.L', NEUTRAL, p2Input, 20);
      expect(p1.lastMove?.id, block ? 'block' : 'hit').toBe('leopard.L');
    }
  });

  /** Steps a while, failing if a special ever starts. (The punch may still chain into a normal.) */
  const noSpecial = (w: World) => {
    for (let i = 0; i < 20; i++) {
      hold(w, 1);
      expect(w.fighters[0].move?.kind ?? 'none').not.toBe('special');
    }
  };

  it('not from a normal that was reached by a chain', () => {
    const w = newWorld(40);
    play(w, [inp(5, ['LP'])]);
    until(w, () => w.fighters[1].combo.hits === 1);
    play(w, [inp(5, ['MP'])]);
    until(w, () => w.fighters[1].combo.hits === 2);
    leopard(w, NEUTRAL);
    noSpecial(w);
  });

  it('not from a command normal', () => {
    const w = newWorld(40);
    play(w, [inp(6, ['MP'])]);
    until(w, () => w.fighters[1].combo.hits === 1);
    leopard(w, NEUTRAL);
    noSpecial(w);
  });
});

describe('combo counter', () => {
  it('counts the hits, stays 2 seconds after the defender recovers, and a new combo replaces it', () => {
    const g = new Game();
    g.world.resetRound(40);
    const p2 = g.world.fighters[1];
    const tick = (input = NEUTRAL) => g.tick(input, NEUTRAL);
    // 5LP chained into 5MP, from the start positions (the counter itself is not reset).
    const chain = () => {
      g.world.resetRound(40);
      tick(inp(5, ['LP']));
      while (p2.state !== 'hitstun') tick();
      tick(inp(5, ['MP']));
      for (let i = 0; i < 40 && p2.combo.hits < 2; i++) tick();
    };

    tick(inp(5, ['LP']));
    for (let i = 0; i < 40; i++) tick();
    expect(p2.combo.hits).toBe(1);
    expect(g.comboShown[0]).toBeNull(); // one hit is not a combo

    chain();
    expect(g.comboShown[0]).toEqual({ hits: 2, endedAt: null });
    while (isStunned(p2)) tick();
    expect(g.comboShown[0]).toEqual({ hits: 2, endedAt: g.world.frame });
    for (let i = 0; i < 119; i++) tick();
    expect(g.comboShown[0]).not.toBeNull();
    tick();
    expect(g.comboShown[0]).toBeNull();

    chain();
    while (isStunned(p2)) tick();
    for (let i = 0; i < 30; i++) tick();
    chain();
    expect(g.comboShown[0]).toEqual({ hits: 2, endedAt: null });
  });
});
