import type { CompiledCharacter } from '../characters/compile';
import { NORMAL_SLOTS } from '../characters/types';
import type { Game } from '../game/game';
import type { CompiledMove } from '../moves/compile';
import { SUB } from '../core/units';

/** What each training key does; the toolbar buttons do the same. */
export function runKey(game: Game, code: string): boolean {
  switch (code) {
    case 'Digit1':
      game.showBoxes = !game.showBoxes;
      return true;
    case 'Digit2':
      game.showInfo = !game.showInfo;
      return true;
    case 'Digit3':
      game.togglePause();
      return true;
    case 'Digit4':
      game.stepFrame();
      return true;
    case 'Digit5':
      game.cycleDummyStance();
      return true;
    case 'Digit6':
      game.dummyBlock = !game.dummyBlock;
      return true;
    case 'Digit7':
      game.setMode(game.mode === 'training' ? 'versus' : 'training');
      return true;
    case 'Digit8':
      game.fullMeter = !game.fullMeter;
      return true;
    case 'Digit0':
      game.reset();
      return true;
  }
  return false;
}

export const TRAINING_KEYS = ['Digit1', 'Digit2', 'Digit3', 'Digit4', 'Digit5', 'Digit6', 'Digit7', 'Digit8', 'Digit0'];

/** Keeps the toolbar buttons showing the current settings. */
export function syncToolbar(game: Game): void {
  const set = (id: string, pressed: boolean | null, label?: string) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (pressed !== null) el.setAttribute('aria-pressed', String(pressed));
    if (label !== undefined && el.firstChild && el.firstChild.textContent !== label) el.firstChild.textContent = label;
  };
  set('btn-mode', null, game.mode === 'training' ? 'Training ' : 'Versus ');
  set('btn-boxes', game.showBoxes);
  set('btn-info', game.showInfo);
  set('btn-pause', game.paused);
  set('btn-stance', null, `Dummy: ${game.dummyStance} `);
  set('btn-block', game.dummyBlock);
  set('btn-meter', game.fullMeter);
}

const PUNCH_OR_KICK = { P: 'P', K: 'K' } as const;

function notes(m: CompiledMove): string {
  const out: string[] = [];
  if (m.guard === 'low') out.push('Low');
  if (m.guard === 'overhead') out.push('Overhead');
  if (m.knockdown) out.push(m.knockdown.wakeupMultiplier > 1 ? `Knockdown, wakeup ×${m.knockdown.wakeupMultiplier}` : 'Knockdown');
  if (m.vulnerable) out.push(`Takes ×${m.vulnerable.damageMultiplier} damage if hit during startup`);
  if (m.landingRecovery) out.push(`Airborne; +${m.landingRecovery} frames after landing`);
  if (m.hitPhases.some((p) => p.boxes.some((b) => b.x + b.w / 2 < 0))) out.push('Hits behind too');
  out.push(`Knockback ${m.knockback.distance / SUB} px`);
  return out.join('. ');
}

/** Fills the move list table from the same data the game uses, so it is always up to date. */
export function renderMoveList(c: CompiledCharacter): void {
  const body = document.getElementById('move-list');
  if (!body) return;
  const rows: string[] = [];
  const group = (title: string) => rows.push(`<tr class="group"><td colspan="8">${title}</td></tr>`);
  const row = (input: string, m: CompiledMove) =>
    rows.push(
      `<tr><td class="input">${input}</td><td>${m.name}</td><td class="num">${m.startup}</td><td class="num">${m.active}</td>` +
        `<td class="num">${m.recovery}</td><td class="num">${m.damage}</td><td class="num">${m.knockdown ? '–' : m.hitstun}</td><td>${notes(m)}</td></tr>`,
    );

  group('Normals');
  for (const slot of NORMAL_SLOTS) {
    const m = c.normals[slot];
    if (m) row(slot, m);
  }
  group('Command normals');
  for (const cn of c.commandNormals) row(`${cn.direction} + ${cn.button}`, cn.move);
  group('Special moves');
  for (const sp of c.specials) {
    for (const v of ['L', 'M', 'H'] as const) {
      const m = sp[v];
      if (m) row(`${sp.motion.join(' ')} + ${v}${PUNCH_OR_KICK[sp.button]}`, m);
    }
  }
  body.innerHTML = rows.join('');

  const missing = [
    ...NORMAL_SLOTS.filter((s) => !c.normals[s]),
    ...c.specials.filter((s) => !s.CE).map((s) => `${s.name} CE (${s.motion.join(' ')} + two ${s.button === 'P' ? 'punches' : 'kicks'})`),
  ];
  const note = document.getElementById('not-made');
  if (note) {
    note.textContent =
      `Not made yet (the input is read, nothing happens): ${missing.join(', ')}` +
      (c.chakraSpecials.length ? '.' : ', Chakra specials.');
  }
}
