import { CHARACTERS } from './characters';
import { FPS, SCREEN_H, SCREEN_W } from './config';
import { Gamepads, KEYS, Keyboard, allGameKeys, merge } from './game/devices';
import { Game } from './game/game';
import { Framebuffer } from './render/framebuffer';
import { Renderer } from './render/renderer';
import { TRAINING_KEYS, renderMoveList, runKey, syncToolbar } from './ui/page';

const canvas = document.getElementById('screen') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const image = ctx.createImageData(SCREEN_W, SCREEN_H);
const fb = new Framebuffer(SCREEN_W, SCREEN_H, image.data);
const game = new Game();
const renderer = new Renderer();
const keyboard = new Keyboard(allGameKeys());
const pads = new Gamepads();
keyboard.attach(window);
renderMoveList(CHARACTERS.shoto);
// For automated browser checks: lets a script pause the game and step exact frames.
(window as unknown as { fightingGame: Game }).fightingGame = game;

// The hint covers the screen until the page has keyboard focus.
const hint = document.getElementById('hint') as HTMLButtonElement | null;
const start = () => {
  if (hint) hint.hidden = true;
  canvas.focus();
};
hint?.addEventListener('click', start);
window.addEventListener('keydown', () => hint && (hint.hidden = true), { once: true });

document.getElementById('toolbar')?.addEventListener('click', (e) => {
  const button = (e.target as HTMLElement).closest('button');
  if (button?.dataset.key) runKey(game, button.dataset.key);
  canvas.focus();
});

/** Largest whole-number scale that fits, so every game pixel is the same size. */
function fit(): void {
  const bezel = canvas.parentElement!;
  const room = bezel.parentElement!.clientWidth - 26;
  const scale = Math.floor(Math.min(room / SCREEN_W, (window.innerHeight - 150) / SCREEN_H));
  canvas.style.width = scale >= 1 ? `${SCREEN_W * Math.min(scale, 4)}px` : '100%';
}
fit();
window.addEventListener('resize', fit);

const TICK = 1000 / FPS;
let last = performance.now();
let behind = 0;

function frame(now: number): void {
  let dt = now - last;
  last = now;
  // A refresh that took (almost exactly) a whole number of game frames counts as exactly that,
  // so a 60 Hz screen shows every game frame once instead of occasionally skipping or repeating one.
  for (let k = 1; k <= 4; k++) {
    if (Math.abs(dt - k * TICK) < 1) {
      dt = k * TICK;
      break;
    }
  }
  behind = Math.min(behind + dt, 6 * TICK);

  for (const code of TRAINING_KEYS) if (keyboard.takeTap(code)) runKey(game, code);
  keyboard.clearTaps();

  while (behind >= TICK) {
    behind -= TICK;
    const p1 = merge(keyboard.read(KEYS[0]), pads.read(0));
    const p2 = merge(keyboard.read(KEYS[1]), pads.read(1));
    if (game.tick(p1, p2)) keyboard.endFrame();
  }

  renderer.draw(fb, game);
  ctx.putImageData(image, 0, 0);
  syncToolbar(game);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
