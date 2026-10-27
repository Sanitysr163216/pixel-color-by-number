import { px } from '../core/units';
import type { ButtonName } from '../input/buttons';
import { compileMove, ubox, type CompiledMove, type UBox } from '../moves/compile';
import { NORMAL_SLOTS, type CharacterData, type NormalSlot } from './types';

export interface CompiledSpecial {
  id: string;
  name: string;
  motion: number[];
  window: number;
  button: 'P' | 'K';
  L: CompiledMove | null;
  M: CompiledMove | null;
  H: CompiledMove | null;
  CE: CompiledMove | null;
}

export interface CompiledChakraSpecial {
  id: string;
  name: string;
  motion: number[];
  window: number;
  button: 'P' | 'K';
  move: CompiledMove;
}

export interface CompiledCharacter {
  name: string;
  health: number;
  walkForward: number;
  walkBack: number;
  jump: { squat: number; up: number; forward: number; back: number };
  hurt: { stand: UBox[]; crouch: UBox[]; air: UBox[] };
  push: { stand: UBox; crouch: UBox; air: UBox; down: UBox };
  normals: Record<NormalSlot, CompiledMove | null>;
  commandNormals: { direction: number; button: ButtonName; move: CompiledMove }[];
  specials: CompiledSpecial[];
  chakraSpecials: CompiledChakraSpecial[];
  data: CharacterData;
}

export function compileCharacter(c: CharacterData): CompiledCharacter {
  const normals = {} as Record<NormalSlot, CompiledMove | null>;
  for (const slot of NORMAL_SLOTS) {
    const m = c.normals[slot];
    normals[slot] = m ? compileMove(slot, m) : null;
  }
  const version = (id: string, m: Parameters<typeof compileMove>[1] | null) => (m ? compileMove(id, m) : null);
  return {
    name: c.name,
    health: c.health,
    walkForward: px(c.walkForward),
    walkBack: px(c.walkBack),
    jump: { squat: c.jump.squat, up: px(c.jump.up), forward: px(c.jump.forward), back: px(c.jump.back) },
    hurt: { stand: c.hurtboxes.stand.map(ubox), crouch: c.hurtboxes.crouch.map(ubox), air: c.hurtboxes.air.map(ubox) },
    push: {
      stand: ubox(c.pushboxes.stand),
      crouch: ubox(c.pushboxes.crouch),
      air: ubox(c.pushboxes.air),
      down: ubox(c.pushboxes.down),
    },
    normals,
    commandNormals: c.commandNormals.map((cn) => ({
      direction: cn.direction,
      button: cn.button,
      move: compileMove(`${cn.direction}${cn.button}`, cn.move),
    })),
    specials: c.specials.map((s) => ({
      id: s.id,
      name: s.name,
      motion: s.motion,
      window: s.window,
      button: s.button,
      L: version(`${s.id}.L`, s.L),
      M: version(`${s.id}.M`, s.M),
      H: version(`${s.id}.H`, s.H),
      CE: version(`${s.id}.CE`, s.CE),
    })),
    chakraSpecials: c.chakraSpecials.map((s) => ({
      id: s.id,
      name: s.name,
      motion: s.motion,
      window: s.window,
      button: s.button,
      move: compileMove(s.id, s.move),
    })),
    data: c,
  };
}
