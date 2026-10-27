/**
 * A software pixel buffer. Everything is drawn into it at 304×224 and then scaled up with hard pixel
 * edges, so the picture looks like an arcade screen rather than smoothed vector art.
 *
 * Colours are 32-bit ABGR numbers (the byte order of ImageData on little-endian machines).
 */
export type Color = number;

export function rgb(hex: string, alpha = 1): Color {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return ((Math.round(alpha * 255) << 24) | (b << 16) | (g << 8) | r) >>> 0;
}

export class Framebuffer {
  readonly data: Uint32Array;

  constructor(
    readonly width: number,
    readonly height: number,
    pixels?: Uint8ClampedArray,
  ) {
    this.data = pixels ? new Uint32Array(pixels.buffer, pixels.byteOffset, width * height) : new Uint32Array(width * height);
  }

  clear(color: Color): void {
    this.data.fill(color);
  }

  pixel(x: number, y: number, color: Color): void {
    x |= 0;
    y |= 0;
    if (x < 0 || y < 0 || x >= this.width || y >= this.height) return;
    const i = y * this.width + x;
    const a = color >>> 24;
    if (a === 255) {
      this.data[i] = color;
    } else if (a > 0) {
      this.data[i] = blend(this.data[i], color, a);
    }
  }

  rect(x: number, y: number, w: number, h: number, color: Color): void {
    const x0 = Math.max(0, Math.round(x));
    const y0 = Math.max(0, Math.round(y));
    const x1 = Math.min(this.width, Math.round(x + w));
    const y1 = Math.min(this.height, Math.round(y + h));
    const a = color >>> 24;
    for (let yy = y0; yy < y1; yy++) {
      const row = yy * this.width;
      if (a === 255) this.data.fill(color, row + x0, row + x1);
      else for (let xx = x0; xx < x1; xx++) this.data[row + xx] = blend(this.data[row + xx], color, a);
    }
  }

  outline(x: number, y: number, w: number, h: number, color: Color): void {
    x = Math.round(x);
    y = Math.round(y);
    w = Math.round(w);
    h = Math.round(h);
    if (w <= 0 || h <= 0) return;
    this.rect(x, y, w, 1, color);
    if (h > 1) this.rect(x, y + h - 1, w, 1, color);
    if (h > 2) {
      this.rect(x, y + 1, 1, h - 2, color);
      if (w > 1) this.rect(x + w - 1, y + 1, 1, h - 2, color);
    }
  }

  /** A thick line with round ends: every pixel within `r` of the segment. */
  capsule(x1: number, y1: number, x2: number, y2: number, r: number, color: Color): void {
    const minX = Math.floor(Math.min(x1, x2) - r);
    const maxX = Math.ceil(Math.max(x1, x2) + r);
    const minY = Math.floor(Math.min(y1, y2) - r);
    const maxY = Math.ceil(Math.max(y1, y2) + r);
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len2 = dx * dx + dy * dy;
    const r2 = (r + 0.3) * (r + 0.3);
    for (let y = minY; y <= maxY; y++) {
      for (let x = minX; x <= maxX; x++) {
        let t = len2 ? ((x - x1) * dx + (y - y1) * dy) / len2 : 0;
        t = t < 0 ? 0 : t > 1 ? 1 : t;
        const ex = x1 + t * dx - x;
        const ey = y1 + t * dy - y;
        if (ex * ex + ey * ey <= r2) this.pixel(x, y, color);
      }
    }
  }

  disc(x: number, y: number, r: number, color: Color): void {
    this.capsule(x, y, x, y, r, color);
  }

  /** A 1-pixel line. */
  line(x1: number, y1: number, x2: number, y2: number, color: Color): void {
    const steps = Math.max(Math.abs(x2 - x1), Math.abs(y2 - y1), 1);
    for (let i = 0; i <= steps; i++) {
      this.pixel(Math.round(x1 + ((x2 - x1) * i) / steps), Math.round(y1 + ((y2 - y1) * i) / steps), color);
    }
  }

  ellipse(cx: number, cy: number, rx: number, ry: number, color: Color): void {
    for (let y = -Math.ceil(ry); y <= Math.ceil(ry); y++) {
      const w = Math.round(rx * Math.sqrt(Math.max(0, 1 - (y * y) / (ry * ry))));
      if (w > 0) this.rect(cx - w, cy + y, 2 * w, 1, color);
    }
  }

  /** Copies another buffer onto this one, skipping fully transparent pixels. */
  blit(src: Framebuffer, sx: number, sy: number, w: number, h: number, dx: number, dy: number): void {
    sx = Math.round(sx);
    sy = Math.round(sy);
    dx = Math.round(dx);
    dy = Math.round(dy);
    for (let y = 0; y < h; y++) {
      const ty = dy + y;
      const fy = sy + y;
      if (ty < 0 || ty >= this.height || fy < 0 || fy >= src.height) continue;
      for (let x = 0; x < w; x++) {
        const tx = dx + x;
        const fx = sx + x;
        if (tx < 0 || tx >= this.width || fx < 0 || fx >= src.width) continue;
        const c = src.data[fy * src.width + fx];
        const a = c >>> 24;
        if (a === 255) this.data[ty * this.width + tx] = c;
        else if (a > 0) this.data[ty * this.width + tx] = blend(this.data[ty * this.width + tx], c, a);
      }
    }
  }
}

function blend(dst: number, src: number, a: number): number {
  const ia = 255 - a;
  const r = ((src & 255) * a + (dst & 255) * ia) / 255;
  const g = (((src >> 8) & 255) * a + ((dst >> 8) & 255) * ia) / 255;
  const b = (((src >> 16) & 255) * a + ((dst >> 16) & 255) * ia) / 255;
  return ((255 << 24) | (b << 16) | (g << 8) | r) >>> 0;
}
