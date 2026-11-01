import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '../src/characters';
import { px } from '../src/core/units';
import { NEUTRAL } from '../src/input/buttons';
import { hold, inp, inp2, inputsFor, newWorld, play, putInAir, until } from './helpers';

const shoto = CHARACTERS.shoto;
const flake = shoto.specials.find((s) => s.id === 'flake')!;
const flakeL = flake.L!;
const flakeCE = flake.CE!;

describe('chip damage', () => {
  it('a blocked special does 10 per hit; a blocked normal does nothing', () => {
    for (const [id, gap, chip] of [['leopard.M', 44, 10], ['5HK', 40, 0]] as const) {
      const w = newWorld(gap);
      const inputs = inputsFor(id);
      play(w, inputs, inputs.map(() => inp2(4)));
      hold(w, 40, NEUTRAL, inp2(4));
      expect(w.fighters[1].health, id).toBe(1000 - chip);
    }
  });

  it('Soul Flake can be blocked in the air, for double chip', () => {
    const w = newWorld(120);
    const [p1, p2] = w.fighters;
    putInAir(p2, 30, 0);
    const p = w.spawnProjectile(p1, flakeL);
    p.x = p2.x - px(30);
    p.y = p2.y + px(40);
    until(w, () => p2.state === 'blockstun', NEUTRAL, inp2(4));
    expect(p2.airBlock).toBe(true);
    expect(p2.health).toBe(1000 - 20);
  });
});

describe('blocking covers one side', () => {
  /** P2 between a Soul Flake coming from the left and P1 (on the right) punching. */
  const sandwich = (flakeFrame: number) => {
    const w = newWorld(60);
    const [p1, p2] = w.fighters;
    p2.x = px(300);
    p1.x = px(340);
    p1.facing = -1;
    p2.facing = 1;
    const p = w.spawnProjectile(p1, flakeL);
    p.vx = flakeL.projectile!.speed; // flying right, into P2's back
    p.facing = 1;
    p.y = px(58);
    // Its front edge (9 px ahead of its centre) reaches P2's body (14 px behind P2's centre) on `flakeFrame`,
    // at 3 px per frame, as long as P2 stands still.
    p.x = p2.x - px(14) - px(9) - px(3) * flakeFrame + px(1);
    return { w, p1, p2 };
  };

  it('a hit from each side on the same frame: only one can be blocked', () => {
    const { w, p2 } = sandwich(5);
    // P1's standing LP is active on frame 5, the same frame the flake arrives. P2 holds left (away from P1)
    // on that frame; standing still before it.
    play(w, [inp(5, ['LP'], -1), NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL], [NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, inp(4, [], 1)]);
    expect(w.events.map((e) => e.type).sort()).toEqual(['block', 'hit']);
    expect(p2.health).toBe(1000 - flakeL.damage); // punch blocked, flake hit
  });

  it('while blocking one side, a hit from the other side is not blocked automatically', () => {
    const { w, p2 } = sandwich(2);
    // P2 holds right to block the flake from the left, then lets go; P1's punch comes from the right.
    play(w, [inp(5, ['LP'], -1), NEUTRAL], [NEUTRAL, inp(6, [], 1)]);
    expect(p2.state).toBe('blockstun');
    hold(w, 10);
    expect(p2.health).toBe(1000 - 10 - 30); // chip from the flake, then the punch
  });
});

describe('Soul Flake', () => {
  it('flies at 3, 3.75 and 5.25 px per frame (light, medium +25%, heavy +75%); the CE at half the light speed', () => {
    for (const [v, speed] of [['L', 3], ['M', 3.75], ['H', 5.25], ['CE', 1.5]] as const) {
      const w = newWorld(250);
      const p = w.spawnProjectile(w.fighters[0], flake[v]!);
      const x = p.x;
      hold(w, 4);
      expect((p.x - x) / px(1), v).toBe(4 * speed);
    }
  });

  it('recovery: 43 frames for light, +1 for medium, +2 for heavy', () => {
    expect([flake.L!.recovery, flake.M!.recovery, flake.H!.recovery]).toEqual([43, 44, 45]);
    expect(flake.L!.startup).toBe(12);
    expect(flake.L!.damage).toBe(flake.M!.damage);
    expect(flake.L!.damage).toBe(flake.H!.damage);
  });

  it('disappears off the screen', () => {
    const w = newWorld(150);
    const p = w.spawnProjectile(w.fighters[0], flakeL);
    p.vx = -p.vx; // away from the opponent
    hold(w, 150);
    expect(w.projectiles).toHaveLength(0);
  });

  it('two Soul Flakes cancel out; the CE beats a normal one and keeps going', () => {
    for (const [mine, left] of [[flakeL, 0], [flakeCE, 1]] as const) {
      const w = newWorld(200);
      const [p1, p2] = w.fighters;
      const a = w.spawnProjectile(p1, mine);
      const b = w.spawnProjectile(p2, flakeL);
      a.x = b.x - px(60);
      hold(w, 20);
      expect(w.projectiles.length, mine.id).toBe(left);
      if (left) expect(w.projectiles[0].hitsLeft).toBe(mine.projectile!.hits - 1);
    }
  });

  it('QCF + punch throws it; with two punches and a bar, the CE', () => {
    const w = newWorld(250);
    const p1 = w.fighters[0];
    play(w, inputsFor('flake.M'));
    expect(p1.move?.id).toBe('flake.M');
    const w2 = newWorld(250);
    w2.fighters[0].meter = 100;
    play(w2, [inp(2), inp(3), inp(6, ['LP', 'MP'])]);
    expect(w2.fighters[0].move?.id).toBe('flake.CE');
    expect(w2.fighters[0].meter).toBe(0);
  });
});

describe('Soul Flake CE', () => {
  it('hits 5 times for 2.5 times the damage of a normal Soul Flake', () => {
    const w = newWorld(100);
    const [p1, p2] = w.fighters;
    p1.meter = 100;
    play(w, [inp(2), inp(3), inp(6, ['LP', 'MP'])]);
    hold(w, 150);
    expect(p2.combo.hits).toBe(5);
    expect(1000 - p2.health).toBe(2.5 * flakeL.damage);
  });

  it('can not be jumped over', () => {
    const w = newWorld(120);
    const [p1, p2] = w.fighters;
    putInAir(p2, 100, 0); // the top of a jump
    const p = w.spawnProjectile(p1, flakeCE);
    p.x = p2.x - px(40);
    hold(w, 3);
    expect(p2.health).toBeLessThan(1000);
  });

  it('blocking it crouching locks the stance: an overhead gets through', () => {
    const lockTest = (move: typeof flakeCE) => {
      const w = newWorld(50);
      const [p1, p2] = w.fighters;
      w.spawnProjectile(p1, move);
      play(w, [inputsFor('6MK')[0]], [inp2(1)]); // P1 starts the overhead axe kick; P2 crouch-blocks the orb
      expect(p2.state).toBe('blockstun');
      hold(w, 30, NEUTRAL, inp2(4)); // P2 tries to stand up
      return { p2, hitByAxeKick: p2.health <= 1000 - shoto.commandNormals[1].move.damage };
    };
    const locked = lockTest(flakeCE);
    expect(locked.hitByAxeKick).toBe(true);
    // A normal Soul Flake doesn't lock: the blockstring blocks the overhead too.
    expect(lockTest(flakeL).hitByAxeKick).toBe(false);
  });

  it('the thrower counts as airborne during its startup', () => {
    const w = newWorld(46);
    const p1 = w.fighters[0];
    p1.meter = 100;
    play(w, [inp(2), inp(3), inp(6, ['LP', 'MP'])], [NEUTRAL, NEUTRAL, inp2(5, ['LP'])]);
    until(w, () => p1.state !== 'move');
    expect(p1.state).toBe('airReset'); // a light normal flips an airborne fighter
  });
});
