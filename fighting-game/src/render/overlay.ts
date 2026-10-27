import { SCREEN_W } from '../config';
import { SUB } from '../core/units';
import type { Game } from '../game/game';
import type { UBox } from '../moves/compile';
import { movePhase, type Fighter } from '../sim/fighter';
import { place } from '../sim/boxes';
import { drawText, textWidth } from './font';
import { rgb, type Color, type Framebuffer } from './framebuffer';
import { UI } from './palette';
import { centred } from './hud';

const GREEN = rgb('#7cf07c');
const RED = rgb('#ff7a6a');

/** Hitboxes, hurtboxes and pushboxes on top of the fighters. */
export function drawBoxes(fb: Framebuffer, game: Game, cameraX: number, ground: number): void {
  const w = game.world;
  const toScreen = (f: Fighter, b: UBox) => {
    const r = place(f.x, f.y, f.facing, b);
    return { x: r.l / SUB - cameraX, y: ground - r.t / SUB, w: (r.r - r.l) / SUB, h: (r.t - r.b) / SUB };
  };
  for (const f of w.fighters) {
    const push = w.pushbox(f);
    if (push) fb.outline(push.l / SUB - cameraX, ground - push.t / SUB, (push.r - push.l) / SUB, (push.t - push.b) / SUB, UI.push);
    for (const b of w.hurtboxes(f)) {
      const s = toScreen(f, b);
      fb.rect(s.x, s.y, s.w, s.h, UI.hurt);
      fb.outline(s.x, s.y, s.w, s.h, UI.hurtLine);
    }
    for (const phase of w.hitboxes(f)) {
      for (const b of phase.boxes) {
        const s = toScreen(f, b);
        fb.rect(s.x, s.y, s.w, s.h, phase.spent ? UI.spent : UI.hit);
        fb.outline(s.x, s.y, s.w, s.h, phase.spent ? UI.spentLine : UI.hitLine);
      }
    }
    const ox = Math.round(f.x / SUB - cameraX);
    const oy = Math.round(ground - f.y / SUB);
    fb.rect(ox - 2, oy, 5, 1, UI.white);
    fb.rect(ox, oy - 2, 1, 5, UI.white);

    // State label above the head, but never up among the life bars and frame data.
    const tag = stateTag(game, f);
    const x = Math.min(SCREEN_W - 2 - textWidth(tag), Math.max(2, ox - textWidth(tag) / 2));
    if (tag) drawText(fb, tag, x, Math.max(64, oy - 112), UI.text, 1, UI.shadow);
  }
}

function stateTag(game: Game, f: Fighter): string {
  if (game.world.isInvulnerable(f) && f.state !== 'move') {
    return f.state === 'knockdown' && f.down ? `DOWN ${f.stun + 1}` : 'INVULNERABLE';
  }
  switch (f.state) {
    case 'move': {
      const m = f.move!;
      const phase = movePhase(f)!;
      if (phase === 'startup') return `STARTUP ${f.moveFrame}/${m.startup}`;
      if (phase === 'active') return `ACTIVE ${f.moveFrame - m.startup}/${m.active}`;
      const k = f.moveFrame - m.startup - m.active;
      return k > m.recovery ? 'FALLING' : `RECOVERY ${k}/${m.recovery}`;
    }
    case 'hitstun':
      return `HITSTUN ${f.stun}`;
    case 'blockstun':
      return `BLOCKSTUN ${f.stun}`;
    case 'landing':
      return `LANDING ${f.stun + 1}`;
    case 'jumpSquat':
      return 'PRE-JUMP';
    default:
      return '';
  }
}

/** Training mode text: frame data, frame advantage, recognised commands, dummy settings, input display. */
export function drawTrainingInfo(fb: Framebuffer, game: Game): void {
  const w = game.world;
  const [p1, p2] = w.fighters;
  const line = (text: string, y: number, color: Color = UI.text, right = false) =>
    drawText(fb, text, right ? SCREEN_W - 8 - textWidth(text) : 8, y, color, 1, UI.shadow);

  const m = p1.lastMove;
  if (m) {
    line(m.name.toUpperCase(), 26, UI.yellow);
    const landing = m.landingRecovery ? `+${m.landingRecovery}L` : '';
    line(`S${m.startup} A${m.active} R${m.recovery}${landing} DMG ${m.damage}`, 35);
  }
  const adv = w.advantage;
  if (adv) {
    const value = adv.attacker === 0 ? adv.value : -adv.value;
    const text = `${value >= 0 ? '+' : ''}${value} ON ${adv.blocked ? 'BLOCK' : 'HIT'}`;
    line(text, 44, value >= 0 ? GREEN : RED);
  }
  if (p1.lastCommand && w.frame - p1.lastCommandFrame < 120) line(`> ${p1.lastCommand}`, 53, UI.dim);

  line(`DUMMY ${game.dummyStance.toUpperCase()}`, 26, UI.text, true);
  line(game.dummyBlock ? 'BLOCK ALL' : 'NO BLOCK', 35, UI.text, true);
  if (game.fullMeter) line('FULL METER', 44, UI.meterLight, true);
  if (p2.combo.hits > 0) line(`${p2.combo.hits} HIT ${p2.combo.damage} DMG`, 53, UI.yellow, true);

  // Input display in numpad notation (6 = forward), newest at the top.
  const log = game.inputLog[0];
  for (let i = 0; i < log.length && i < 13; i++) {
    const e = log[i];
    const y = 66 + i * 9;
    drawText(fb, String(e.dir), 8, y, e.dir === 5 ? UI.dim : UI.text, 1, UI.shadow);
    if (e.buttons) drawText(fb, e.buttons, 18, y, UI.yellow, 1, UI.shadow);
    const frames = String(Math.min(e.frames, 99));
    drawText(fb, frames, 78 - textWidth(frames), y, UI.dim, 1, UI.shadow);
  }

  if (game.paused) centred(fb, 'PAUSED - 4: NEXT FRAME', 100, 1, UI.yellow);
}
