import { RULES, SCREEN_W } from '../config';
import type { Game } from '../game/game';
import type { Fighter } from '../sim/fighter';
import { drawText, textWidth } from './font';
import type { Color, Framebuffer } from './framebuffer';
import { UI } from './palette';

const BAR_W = 132;
const BAR_Y = 13;

/** Life bars, names, the meter gauges and big banners, laid out like a Neo Geo fighting game. */
export class Hud {
  /** The red part of the life bar that drains a moment after a hit. */
  private readonly trail = [0, 0];
  private readonly lastHealth = [0, 0];
  private readonly calm = [0, 0];

  draw(fb: Framebuffer, game: Game): void {
    const w = game.world;
    for (const f of w.fighters) {
      this.lifeBar(fb, f);
      this.meter(fb, f, w.frame);
    }
    // Centre emblem between the bars.
    fb.rect(SCREEN_W / 2 - 11, BAR_Y - 3, 22, 15, UI.barFrame);
    fb.outline(SCREEN_W / 2 - 11, BAR_Y - 3, 22, 15, UI.barEdge);
    const label = game.mode === 'training' ? 'TR' : 'VS';
    drawText(fb, label, SCREEN_W / 2 - textWidth(label) / 2, BAR_Y + 1, UI.yellow);

    this.combo(fb, game);
    const b = game.banner;
    if (b && w.frame < b.until) centred(fb, b.text, 80, 2, UI.yellow);
  }

  private lifeBar(fb: Framebuffer, f: Fighter): void {
    const i = f.index;
    const max = f.char.health;
    if (f.health !== this.lastHealth[i]) {
      if (f.health > this.lastHealth[i]) this.trail[i] = f.health;
      this.lastHealth[i] = f.health;
      this.calm[i] = 0;
    }
    this.calm[i]++;
    if (this.trail[i] < f.health) this.trail[i] = f.health;
    if (this.calm[i] > 30 && this.trail[i] > f.health) this.trail[i] = Math.max(f.health, this.trail[i] - 8);

    const x = i === 0 ? 8 : SCREEN_W - 8 - BAR_W;
    fb.rect(x - 1, BAR_Y - 1, BAR_W + 2, 10, UI.barFrame);
    fb.rect(x, BAR_Y, BAR_W, 8, UI.barBack);
    // Health is anchored at the outer end, so damage eats in from the middle of the screen.
    const fill = (value: number, color: Color, light: Color, dark: Color) => {
      const len = Math.round((BAR_W * Math.max(0, value)) / max);
      const bx = i === 0 ? x : x + BAR_W - len;
      fb.rect(bx, BAR_Y, len, 8, color);
      fb.rect(bx, BAR_Y, len, 1, light);
      fb.rect(bx, BAR_Y + 7, len, 1, dark);
    };
    fill(this.trail[i], UI.red, UI.red, UI.red);
    fill(f.health, UI.yellow, UI.yellowLight, UI.yellowDark);
    fb.outline(x - 1, BAR_Y - 1, BAR_W + 2, 10, UI.barEdge);

    const name = f.char.name.toUpperCase();
    drawText(fb, name, i === 0 ? x : x + BAR_W - textWidth(name), 3, UI.text, 1, UI.shadow);
  }

  private meter(fb: Framebuffer, f: Fighter, clock: number): void {
    const per = RULES.meter.perBar;
    const max = per * RULES.meter.bars;
    const bars = Math.floor(f.meter / per);
    const part = f.meter >= max ? per : f.meter % per;
    const left = f.index === 0;
    const w = 92;
    const x = left ? 8 : SCREEN_W - 8 - w;
    const y = 213;
    fb.rect(x - 1, y - 1, w + 2, 7, UI.barFrame);
    fb.rect(x, y, w, 5, UI.meterBack);
    const len = Math.round((w * part) / per);
    const full = f.meter >= max && Math.floor(clock / 4) % 2 === 0;
    const color = full ? UI.white : UI.meter;
    fb.rect(left ? x : x + w - len, y, len, 5, color);
    fb.rect(left ? x : x + w - len, y, len, 1, UI.meterLight);
    fb.rect(left ? x : x + w - len, y + 4, len, 1, UI.meterDark);
    fb.outline(x - 1, y - 1, w + 2, 7, UI.barEdge);

    drawText(fb, 'CHAKRA', left ? x : x + w - textWidth('CHAKRA'), 204, UI.meterLight, 1, UI.shadow);
    const count = String(bars);
    const cx = left ? x + w + 5 : x - 5 - textWidth(count, 2);
    drawText(fb, count, cx, 205, bars > 0 ? UI.yellow : UI.dim, 2, UI.shadow);
  }

  /** "N HITS" on the attacker's side of the screen; stays 2 seconds after the combo ends. */
  private combo(fb: Framebuffer, game: Game): void {
    game.comboShown.forEach((shown, attacker) => {
      if (!shown) return;
      const text = `${shown.hits} HITS`;
      const x = attacker === 0 ? 8 : SCREEN_W - 8 - textWidth(text, 2);
      drawText(fb, text, x, 66, shown.endedAt === null ? UI.yellow : UI.yellowDark, 2, UI.shadow);
    });
  }
}

export function centred(fb: Framebuffer, text: string, y: number, scale: number, color: Color): void {
  drawText(fb, text, Math.round((SCREEN_W - textWidth(text, scale)) / 2), y, color, scale, UI.shadow);
}
