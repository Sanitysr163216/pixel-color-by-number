import { FLOOR_Y, SCREEN_W, STAGE_W } from '../config';
import { SUB } from '../core/units';
import { shotoPose } from '../characters/shoto/poses';
import type { Game } from '../game/game';
import { movePhase, type Fighter } from '../sim/fighter';
import { place } from '../sim/boxes';
import { drawFigure, type ScreenPoints } from './figure';
import { rgb, type Framebuffer } from './framebuffer';
import { Hud, centred } from './hud';
import { drawBoxes, drawTrainingInfo } from './overlay';
import { FIGHTER_PALETTES, UI } from './palette';
import { Stage } from './stage';

const SHADOW = rgb('#000000', 0.35);
const SPARK = rgb('#fff6c0');
const SPARK_EDGE = rgb('#ffb02a');
const GUARD = rgb('#9ae6ff');
const DUST = rgb('#c8b8a8', 0.6);
const GLOW = rgb('#ffe27a', 0.35);
const GLOW_CORE = rgb('#fff8d0', 0.8);
const CLAW = rgb('#fff2b0');

/** Draws one picture of the game: stage, fighters, effects, HUD and the training overlays. */
export class Renderer {
  private readonly stage = new Stage();
  private readonly hud = new Hud();

  draw(fb: Framebuffer, game: Game): void {
    const w = game.world;
    const [a, b] = w.fighters;
    const mid = (a.x + b.x) / 2 / SUB;
    const cameraX = Math.round(Math.min(STAGE_W - SCREEN_W, Math.max(0, mid - SCREEN_W / 2)));
    // The view rises a little with high jumps, so nobody disappears behind the life bars.
    const highest = Math.max(a.y, b.y) / SUB;
    const cameraY = Math.round(Math.min(30, Math.max(0, (highest - 48) * 0.5)));
    const ground = FLOOR_Y + cameraY;

    this.stage.draw(fb, cameraX, cameraY, w.frame);
    for (const f of w.fighters) {
      const x = f.x / SUB - cameraX;
      const lift = f.y / SUB;
      const size = Math.max(8, 18 - lift / 8);
      fb.ellipse(Math.round(x), ground + 1, size, 3, SHADOW);
    }
    // The fighter who is attacking is drawn in front.
    const order = b.state === 'move' && a.state !== 'move' ? [a, b] : [b, a];
    for (const f of order) this.fighter(fb, game, f, cameraX, ground);
    this.effects(fb, game, cameraX, ground);

    if (game.showBoxes) drawBoxes(fb, game, cameraX, ground);
    this.hud.draw(fb, game);
    if (game.mode === 'training' && game.showInfo) drawTrainingInfo(fb, game);
    else if (game.paused) centred(fb, 'PAUSED - 4: NEXT FRAME', 100, 1, UI.yellow);
  }

  private fighter(fb: Framebuffer, game: Game, f: Fighter, cameraX: number, ground: number): void {
    const w = game.world;
    const { pose, rotate, pivot } = shotoPose(f, w.frame);
    const shaking = f.hitstop > 0 && f.state !== 'move' && f.state !== 'ground';
    const x = f.x / SUB - cameraX + (shaking ? (w.frame % 2 ? 1 : -1) : 0);
    const y = ground - f.y / SUB;
    const points = drawFigure(fb, pose, { x, y, facing: f.facing, palette: FIGHTER_PALETTES[f.index], rotate, pivot });
    this.moveEffects(fb, game, f, points, cameraX, ground);
  }

  /** Move-specific flourishes: the Leopard Strike charge and claws, the palm's air wave. */
  private moveEffects(fb: Framebuffer, game: Game, f: Fighter, points: ScreenPoints, cameraX: number, ground: number): void {
    const m = f.move;
    if (f.state !== 'move' || !m) return;
    const phase = movePhase(f);
    const clock = game.world.frame;
    if (m.id.startsWith('leopard')) {
      if (phase === 'startup') {
        // The charge grows over the startup.
        const [hx, hy] = points.fh;
        const charge = f.moveFrame / Math.max(1, m.startup);
        fb.disc(hx, hy, 5 + charge * 6 + (clock % 2), GLOW);
        fb.disc(hx, hy, 3 + charge * 2, GLOW_CORE);
        for (let i = 0; i < 6; i++) {
          const angle = clock * 0.5 + (i * Math.PI) / 3;
          const r = 13 - charge * 5;
          fb.disc(hx + Math.cos(angle) * r, hy + Math.sin(angle) * r, 1, SPARK);
        }
      }
      const sinceActive = f.moveFrame - m.startup;
      if (sinceActive >= 1 && sinceActive <= m.active + 4) {
        const box = place(f.x, f.y, f.facing, m.hitPhases[0].boxes[0]);
        const l = box.l / SUB - cameraX;
        const r = box.r / SUB - cameraX;
        const top = ground - box.t / SUB;
        const bottom = ground - box.b / SUB;
        for (let i = 0; i < 3; i++) {
          const dy = (i - 1) * 5;
          fb.line(l + 4, top + dy, r, bottom + dy, CLAW);
        }
      }
    }
    if (m.id === '6MP' && phase === 'active') {
      const box = place(f.x, f.y, f.facing, m.hitPhases[0].boxes[0]);
      const cx = ((box.l + box.r) / 2) / SUB - cameraX;
      const cy = ground - (box.b + box.t) / 2 / SUB;
      for (let i = -5; i <= 5; i++) fb.pixel(cx + f.facing * (3 - Math.abs(i) / 2), cy + i, UI.white);
    }
  }

  private effects(fb: Framebuffer, game: Game, cameraX: number, ground: number): void {
    const now = game.world.frame;
    for (const { event, start } of game.effects) {
      const age = now - start;
      const x = event.x / SUB - cameraX;
      const y = ground - event.y / SUB;
      if (event.type === 'hit' && age < 12) {
        const size = event.strength === 'H' ? 1.6 : event.strength === 'M' ? 1.3 : 1;
        const len = (4 + age * 1.6) * size;
        for (let i = 0; i < 8; i++) {
          const angle = (i * Math.PI) / 4 + 0.3;
          const r0 = len * 0.4;
          fb.line(x + Math.cos(angle) * r0, y + Math.sin(angle) * r0, x + Math.cos(angle) * len, y + Math.sin(angle) * len, i % 2 ? SPARK_EDGE : SPARK);
        }
        if (age < 4) fb.disc(x, y, (5 - age) * size, SPARK);
      } else if (event.type === 'block' && age < 10) {
        const r = 3 + age * 1.2;
        for (let i = 0; i < 16; i++) {
          const angle = (i * Math.PI) / 8;
          fb.pixel(x + Math.cos(angle) * r, y + Math.sin(angle) * r, GUARD);
        }
        if (age < 3) fb.disc(x, y, 3, UI.white);
      } else if (event.type === 'land' && age < 18) {
        for (const side of [-1, 1]) fb.disc(x + side * (10 + age * 1.5), ground - 2 - age / 4, Math.max(1, 5 - age / 4), DUST);
      }
    }
  }
}
