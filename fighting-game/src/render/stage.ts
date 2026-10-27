import { SCREEN_H, SCREEN_W, STAGE_W } from '../config';
import { Framebuffer, rgb, type Color } from './framebuffer';

/** Top of the floor on screen; the fighters stand lower down, on FLOOR_Y. */
const FLOOR_TOP = 168;

/** Deterministic noise for the scenery, so it looks the same every time. */
function wave(x: number, seed: number): number {
  return Math.sin(x * 0.021 + seed) * 0.5 + Math.sin(x * 0.057 + seed * 2.3) * 0.3 + Math.sin(x * 0.13 + seed * 5.1) * 0.2;
}

function layer(factor: number): Framebuffer {
  return new Framebuffer(Math.ceil(SCREEN_W + (STAGE_W - SCREEN_W) * factor), FLOOR_TOP);
}

/** 4×4 ordered dithering threshold, for retro colour bands. */
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];

/**
 * A placeholder stage: a temple courtyard at dusk, with layers that scroll at different speeds.
 * Pre-drawn once; only the floor is redrawn every frame.
 */
export class Stage {
  private readonly sky = new Framebuffer(SCREEN_W, FLOOR_TOP);
  private readonly mountains = layer(0.15);
  private readonly temple = layer(0.45);
  private readonly crowd = layer(0.8);

  constructor() {
    this.drawSky();
    this.drawMountains();
    this.drawTemple();
    this.drawCrowd();
  }

  /** cameraY: how far the view has risen to follow a high jump (the scenery moves down by that much). */
  draw(fb: Framebuffer, cameraX: number, cameraY: number, clock: number): void {
    if (cameraY > 0) fb.rect(0, 0, SCREEN_W, cameraY, this.sky.data[0]);
    fb.blit(this.sky, 0, 0, SCREEN_W, FLOOR_TOP, 0, cameraY);
    fb.blit(this.mountains, cameraX * 0.15, 0, SCREEN_W, FLOOR_TOP, 0, cameraY);
    fb.blit(this.temple, cameraX * 0.45, 0, SCREEN_W, FLOOR_TOP, 0, cameraY);
    // The crowd bobs a little, like spectators cheering.
    const bob = Math.floor(clock / 16) % 2;
    fb.blit(this.crowd, cameraX * 0.8, 0, SCREEN_W, FLOOR_TOP, 0, cameraY + bob);
    this.drawFloor(fb, cameraX, cameraY);
  }

  private drawSky(): void {
    const bands = ['#1b0f33', '#2a1440', '#3e1a4a', '#5a2150', '#7a2c50', '#9c3a4c', '#bd5045', '#d8683c', '#ec8a3e', '#f6ad55'].map((c) =>
      rgb(c),
    );
    const fb = this.sky;
    for (let y = 0; y < FLOOR_TOP; y++) {
      const t = (y / (FLOOR_TOP - 20)) * (bands.length - 1);
      const i = Math.min(bands.length - 1, Math.floor(t));
      const frac = t - i;
      for (let x = 0; x < SCREEN_W; x++) {
        const next = frac * 16 > BAYER[(y % 4) * 4 + (x % 4)] ? Math.min(bands.length - 1, i + 1) : i;
        fb.data[y * SCREEN_W + x] = bands[next];
      }
    }
    // The sun, low over the hills, with horizontal gaps like old arcade skies.
    const sun = rgb('#ffd98a');
    const glow = rgb('#ffe9b0', 0.18);
    fb.disc(214, 118, 40, glow);
    for (let y = -26; y <= 26; y++) {
      if (y > 6 && y % 5 === 0) continue;
      const w = Math.round(Math.sqrt(26 * 26 - y * y));
      fb.rect(214 - w, 118 + y, 2 * w, 1, sun);
    }
  }

  private drawMountains(): void {
    const fb = this.mountains;
    const far = rgb('#4c2a5c');
    const near = rgb('#34203f');
    for (let x = 0; x < fb.width; x++) {
      const h1 = 112 + Math.round(wave(x, 1) * 18);
      fb.rect(x, h1, 1, FLOOR_TOP - h1, far);
      const h2 = 132 + Math.round(wave(x + 400, 4) * 12);
      fb.rect(x, h2, 1, FLOOR_TOP - h2, near);
    }
  }

  private drawTemple(): void {
    const fb = this.temple;
    const dark = rgb('#22132c');
    const roof = rgb('#2c1636');
    const lantern = rgb('#ff9a3a');
    const lanternLight = rgb('#ffd27a');
    const cx = Math.round(fb.width / 2);

    // Trees along the whole layer.
    for (let x = 6; x < fb.width; x += 38) {
      const h = 22 + Math.round((wave(x, 7) + 1) * 10);
      fb.rect(x + 7, FLOOR_TOP - 20, 3, 20, dark);
      for (let r = 0; r < 3; r++) fb.ellipse(x + 8, FLOOR_TOP - 20 - h + r * 8, 12 - r * 2, 7, dark);
    }

    // A pagoda on each side and a gate in the middle.
    for (const px of [cx - 150, cx + 150]) {
      fb.rect(px - 16, FLOOR_TOP - 60, 32, 60, dark);
      for (let level = 0; level < 3; level++) {
        const y = FLOOR_TOP - 62 - level * 22;
        const w = 30 - level * 6;
        for (let i = 0; i < 6; i++) fb.rect(px - w - i, y + i, 2 * (w + i), 1, roof);
        fb.rect(px - w + 6, y + 6, 2 * (w - 6), 16, dark);
      }
      fb.rect(px - 1, FLOOR_TOP - 140, 2, 14, dark);
    }
    const gateTop = FLOOR_TOP - 70;
    fb.rect(cx - 46, gateTop, 92, 5, dark);
    fb.rect(cx - 52, gateTop - 4, 104, 4, dark);
    fb.rect(cx - 38, gateTop + 12, 76, 3, dark);
    fb.rect(cx - 34, gateTop + 5, 6, 65, dark);
    fb.rect(cx + 28, gateTop + 5, 6, 65, dark);

    // Lanterns.
    for (let x = cx - 120; x <= cx + 120; x += 60) {
      fb.rect(x, FLOOR_TOP - 34, 1, 8, dark);
      fb.disc(x, FLOOR_TOP - 24, 3, lantern);
      fb.pixel(x, FLOOR_TOP - 25, lanternLight);
    }
  }

  private drawCrowd(): void {
    const fb = this.crowd;
    const shirts = ['#5a3a6a', '#3a4a7a', '#6a3a3a', '#3a5a4a', '#5a4a3a'].map((c) => rgb(c));
    const skin = rgb('#4a3038');
    const rail = rgb('#2a1a24');
    for (let x = 4; x < fb.width; x += 11) {
      const seed = Math.abs(Math.round(wave(x, 3) * 1000));
      if (seed % 5 === 0) continue;
      const h = 14 + (seed % 6);
      const shirt = shirts[seed % shirts.length];
      fb.rect(x - 4, FLOOR_TOP - h, 9, h, shirt);
      fb.disc(x, FLOOR_TOP - h - 4, 3.5, skin);
    }
    fb.rect(0, FLOOR_TOP - 8, fb.width, 3, rail);
    for (let x = 0; x < fb.width; x += 24) fb.rect(x, FLOOR_TOP - 8, 2, 8, rail);
  }

  /** Stone floor in perspective: tiles get wider towards the bottom of the screen. */
  private drawFloor(fb: Framebuffer, cameraX: number, cameraY: number): void {
    const near = [0x6e, 0x5c, 0x52];
    const far = [0x3c, 0x30, 0x34];
    const centre = cameraX + SCREEN_W / 2;
    const top = FLOOR_TOP + cameraY;
    const rows = [0, 4, 9, 16, 25, 37, 52].map((r) => top + r);
    for (let y = top; y < SCREEN_H; y++) {
      const t = (y - top) / (SCREEN_H - FLOOR_TOP);
      const c = near.map((n, i) => Math.round(far[i] + (n - far[i]) * t));
      const base: Color = ((255 << 24) | (c[2] << 16) | (c[1] << 8) | c[0]) >>> 0;
      const line: Color = ((255 << 24) | ((c[2] * 0.7) << 16) | ((c[1] * 0.7) << 8) | (c[0] * 0.7)) >>> 0;
      fb.rect(0, y, SCREEN_W, 1, rows.includes(y) ? line : base);
      // Tile joints: world x every 48 px, squeezed towards the horizon.
      const scale = 0.45 + 0.55 * t;
      const first = Math.floor((centre - SCREEN_W / scale) / 48) * 48;
      for (let wx = first; wx < centre + SCREEN_W / scale; wx += 48) {
        const sx = Math.round(SCREEN_W / 2 + (wx - centre) * scale);
        fb.pixel(sx, y, line);
      }
    }
  }
}
