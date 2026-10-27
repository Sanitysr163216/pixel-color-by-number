import { describe, expect, it } from 'vitest';
import { CHARACTERS } from '../src/characters';
import { STRENGTH_DEFAULTS } from '../src/config';
import { px } from '../src/core/units';
import { NEUTRAL } from '../src/input/buttons';
import { distance, hold, inp, inp2, inputsFor, newWorld, play } from './helpers';

const shoto = CHARACTERS.shoto;

describe('hitting and blocking', () => {
  it('standing LP hits a standing opponent: damage, hitstun, hitstop on both', () => {
    const w = newWorld(50);
    const [p1, p2] = w.fighters;
    play(w, [inp(5, ['LP'])]);
    hold(w, 3);
    expect(p2.health).toBe(1000);
    hold(w, 1); // frame 5: first active frame
    expect(p2.health).toBe(970);
    expect(p2.state).toBe('hitstun');
    expect(p1.hitstop).toBe(7);
    expect(p2.hitstop).toBe(7);
  });

  it('high moves whiff on crouching opponents, mid ones hit', () => {
    for (const [id, hits] of [['5LP', false], ['5HP', false], ['5MP', true]] as const) {
      const w = newWorld(50);
      const p2 = w.fighters[1];
      play(w, inputsFor(id), [inp2(2)]);
      hold(w, 25, NEUTRAL, inp2(2));
      expect(p2.health < 1000, id).toBe(hits);
    }
  });

  it('holding back blocks: no damage, blockstun, the attacker gets no meter and the blocker 2 per hit', () => {
    const w = newWorld(50);
    const [p1, p2] = w.fighters;
    play(w, [inp(5, ['LP'])], [inp2(4)]);
    hold(w, 4, NEUTRAL, inp2(4));
    expect(p2.health).toBe(1000);
    expect(p2.state).toBe('blockstun');
    expect(p1.meter).toBe(0);
    expect(p2.meter).toBe(2);
  });

  it('lows must be blocked crouching, overheads standing', () => {
    const cases = [
      ['2HK', 4, true], // standing block vs low: hit
      ['2HK', 1, false], // crouching block vs low: blocked
      ['6MK', 1, true], // crouching block vs overhead: hit
      ['6MK', 4, false], // standing block vs overhead: blocked
      ['5MP', 1, false], // mids: either
      ['5MP', 4, false],
    ] as const;
    for (const [id, block, hit] of cases) {
      const w = newWorld(40); // close enough to still reach a fighter who walks back while holding back
      const p2 = w.fighters[1];
      play(w, inputsFor(id), [inp2(block)]);
      hold(w, 30, NEUTRAL, inp2(block));
      expect(p2.health < 1000, `${id} vs block ${block}`).toBe(hit);
    }
  });

  it('the opponent slides `distance` px at `speed` px per frame after hitstop', () => {
    const w = newWorld(50);
    const p2 = w.fighters[1];
    play(w, [inp(5, ['LP'])]);
    hold(w, 4); // hit on this frame
    const before = p2.x;
    hold(w, 7); // hitstop: nobody moves
    expect(p2.x).toBe(before);
    const steps: number[] = [];
    for (let i = 0; i < 6; i++) {
      const x = p2.x;
      hold(w, 1);
      steps.push((p2.x - x) / px(1));
    }
    expect(steps).toEqual([3.5, 3.5, 3.5, 3.5, 0, 0]); // 14 px at 3.5 px per frame
  });

  it('heavier moves push further and faster by default', () => {
    const { L, M, H } = STRENGTH_DEFAULTS;
    expect(L.knockback.distance).toBeLessThan(M.knockback.distance);
    expect(M.knockback.distance).toBeLessThan(H.knockback.distance);
    expect(L.knockback.speed).toBeLessThan(M.knockback.speed);
    expect(M.knockback.speed).toBeLessThan(H.knockback.speed);
    for (const m of Object.values(shoto.normals)) if (m) expect(m.knockback.distance, m.id).toBeGreaterThan(0);
  });

  it('in the corner the attacker slides back instead', () => {
    const w = newWorld(50);
    const [p1, p2] = w.fighters;
    const wall = px(640 - 20);
    p2.x = wall;
    p1.x = wall - px(50);
    const start = p1.x;
    play(w, [inp(5, ['HP'])]);
    hold(w, 40);
    expect(p2.x).toBe(wall);
    expect((start - p1.x) / px(1)).toBe(32);
  });

  it('each move has its own hitstun: frame advantage = hitstun + 1 - active - recovery', () => {
    for (const id of ['5LP', '5MP', '5HP']) {
      const m = shoto.normals[id as '5LP']!;
      const w = newWorld(46);
      play(w, inputsFor(id));
      hold(w, 80);
      expect(w.advantage, id).toEqual({ attacker: 0, blocked: false, value: m.hitstun + 1 - m.active - m.recovery });
    }
  });

  it('two moves that connect on the same frame trade', () => {
    const w = newWorld(50);
    const [p1, p2] = w.fighters;
    play(w, [inp(5, ['LP'])], [inp2(5, ['LP'])]);
    hold(w, 4);
    expect(p1.health).toBe(970);
    expect(p2.health).toBe(970);
  });

  it('fighters can not walk through each other', () => {
    const w = newWorld(60);
    hold(w, 120, inp(6), inp2(6));
    expect(distance(w)).toBeGreaterThanOrEqual(32);
  });
});

describe('double spin sweep', () => {
  it('hits behind on its back phases', () => {
    const w = newWorld(60);
    const [p1, p2] = w.fighters;
    p2.x = p1.x - px(34); // opponent behind P1, who still faces right
    play(w, [inp(2, ['HK'])]);
    expect(p1.facing).toBe(1);
    hold(w, 30);
    expect(p2.health).toBe(1000 - shoto.normals['2HK']!.damage);
  });

  it('knocks down and only hits once', () => {
    const w = newWorld(50);
    const p2 = w.fighters[1];
    play(w, [inp(2, ['HK'])]);
    hold(w, 40);
    expect(p2.health).toBe(920);
    expect(p2.state).toBe('knockdown');
  });
});
